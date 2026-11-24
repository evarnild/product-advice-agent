// Shared harness for the kit tests that fetch and push: a throwaway bare
// `origin` and clones of it in the OS temp dir, never the real repository and
// never a network remote. Not a test file (no `.test.`), so `node --test`
// does not run it.
//
// The environment follows scripts/update-branch.test.mjs: no inherited GIT_*
// variable, an empty global config, no system config, and no credential
// prompt, so the machine's git setup (credential helper, url rewrites, hooks
// path) cannot reach a sandbox.
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';

export function makeSandbox(prefix = 'sdlc-sandbox-') {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  const emptyConfig = join(dir, 'empty.gitconfig');
  writeFileSync(emptyConfig, '');
  const env = {
    ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^GIT_/i.test(k))),
    GIT_AUTHOR_NAME: 't',
    GIT_AUTHOR_EMAIL: 't@example.com',
    GIT_COMMITTER_NAME: 't',
    GIT_COMMITTER_EMAIL: 't@example.com',
    GIT_CONFIG_GLOBAL: emptyConfig,
    GIT_CONFIG_NOSYSTEM: '1',
    GIT_TERMINAL_PROMPT: '0',
    GCM_INTERACTIVE: 'never',
  };
  const git = (cwd, ...args) => execFileSync('git', args, { cwd, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  const write = (cwd, path, text) => {
    mkdirSync(dirname(join(cwd, path)), { recursive: true });
    writeFileSync(join(cwd, path), text);
  };
  const commitFile = (cwd, path, text, message = `add ${path}`) => {
    write(cwd, path, text);
    git(cwd, 'add', path);
    git(cwd, 'commit', '-q', '-m', message);
  };
  /** A new bare origin with `main` seeded by one commit (files: { path: text }). */
  const makeOrigin = (files = { 'OVERVIEW.md': 'seed\n' }) => {
    const origin = join(dir, 'origin.git');
    git(dir, 'init', '-q', '--bare', '-b', 'main', origin);
    const seed = join(dir, 'seed');
    mkdirSync(seed);
    git(seed, 'init', '-q', '-b', 'main');
    git(seed, 'config', 'core.autocrlf', 'false');
    git(seed, 'remote', 'add', 'origin', origin);
    for (const [p, t] of Object.entries(files)) write(seed, p, t);
    git(seed, 'add', '.');
    git(seed, 'commit', '-q', '-m', 'seed');
    git(seed, 'push', '-q', 'origin', 'main');
    return origin;
  };
  /** A clone of `origin` in <sandbox>/<name>. */
  const clone = (origin, name) => {
    const path = join(dir, name);
    git(dir, 'clone', '-q', origin, path);
    git(path, 'config', 'core.autocrlf', 'false');
    return path;
  };
  /** A parentless commit holding `files` ({ path: text }), made with plumbing in `cwd`; returns its hash. */
  const orphanCommit = (cwd, files, message = 'orphan') => {
    const index = join(dir, `index-${Math.random().toString(36).slice(2)}`);
    const e = { ...env, GIT_INDEX_FILE: index };
    const run = (...args) => execFileSync('git', args, { cwd, env: e, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
    for (const [p, t] of Object.entries(files)) {
      const blob = execFileSync('git', ['hash-object', '-w', '--stdin'], { cwd, env, input: t, encoding: 'utf8' }).trim();
      run('update-index', '--add', '--cacheinfo', `100644,${blob},${p}`);
    }
    const tree = run('write-tree');
    rmSync(index, { force: true });
    return git(cwd, 'commit-tree', tree, '-m', message);
  };
  const meta = (id, slug, status = 'draft') => `id: ${id}\nslug: ${slug}\ntype: fix\nstatus: ${status}\ntitle: Title ${id}\n`;
  const cleanup = () => rmSync(dir, { recursive: true, force: true, maxRetries: 5 });
  return { dir, env, git, write, commitFile, makeOrigin, clone, orphanCommit, meta, cleanup };
}
