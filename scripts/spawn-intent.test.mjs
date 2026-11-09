// End-to-end tests for `npm run spawn` and the session-event hook, against a
// throwaway git repository in the OS temp dir — never this repository. These
// cover the code that moves files and decides whether a worktree may be
// deleted, so they run the real scripts rather than their pure helpers.
import { execFileSync, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, unlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const SPAWN = join(here, 'spawn-intent.mjs');
const EVENT = join(here, 'session-event.mjs');

// Drop every inherited GIT_* variable: run from a git hook or `rebase -x`,
// GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE would point the sandbox's git
// commands at the real repository.
const GIT_ENV = {
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^GIT_/i.test(k))),
  GIT_AUTHOR_NAME: 't',
  GIT_AUTHOR_EMAIL: 't@example.com',
  GIT_COMMITTER_NAME: 't',
  GIT_COMMITTER_EMAIL: 't@example.com',
};

let sandbox;
let repo;
const wt = (name) => join(sandbox, 'product-advice-agent-wt', name);

const git = (cwd, ...args) => execFileSync('git', args, { cwd, env: GIT_ENV, encoding: 'utf8' }).trim();
const run = (script, args, opts = {}) =>
  spawnSync(process.execPath, [script, ...args], { cwd: repo, env: GIT_ENV, encoding: 'utf8', ...opts });
const logOf = (root) => {
  const file = join(root, '.git', 'product-advice-agent-sessions.jsonl');
  return existsSync(file) ? readFileSync(file, 'utf8') : '';
};
/** Writes an intent folder (metadata + intent.md) under `root`. */
const writeIntent = (root, id, slug, body = `# §${id}\n`) => {
  const dir = join(root, 'intents', `${id}-${slug}`);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'metadata.yml'), `id: ${id}\nslug: ${slug}\ntype: fix\nstatus: draft\n`);
  writeFileSync(join(dir, 'intent.md'), body);
  return dir;
};

beforeAll(() => {
  sandbox = mkdtempSync(join(tmpdir(), 'sdlc-spawn-'));
  repo = join(sandbox, 'repo');
  mkdirSync(repo);
  git(repo, 'init', '-q', '-b', 'main');
  // Byte-exact checkouts whatever the machine's global core.autocrlf says.
  git(repo, 'config', 'core.autocrlf', 'false');
  // A base with no .gitignore line for the brief, like an old --base ref.
  writeFileSync(join(repo, 'README.md'), 'probe\n');
  git(repo, 'add', '.');
  git(repo, 'commit', '-q', '-m', 'init');
  // Intents drafted in the main checkout but never committed.
  writeIntent(repo, 98, 'probe-thing', '# §98 probe\n');
  writeIntent(repo, 97, 'neighbour');
});

afterAll(() => {
  // Remove every linked worktree the tests left, then the whole sandbox.
  try {
    const paths = git(repo, 'worktree', 'list', '--porcelain')
      .split(/\r?\n/)
      .filter((l) => l.startsWith('worktree '))
      .map((l) => l.slice('worktree '.length))
      .slice(1);
    for (const p of paths) git(repo, 'worktree', 'remove', '--force', p);
  } catch {
    // the sandbox goes anyway
  }
  rmSync(sandbox, { recursive: true, force: true });
});

describe('npm run spawn', { timeout: 60_000 }, () => {
  it('moves an uncommitted intent into a new worktree, briefs it, and keeps the brief out of git', () => {
    const r = run(SPAWN, ['98', '--no-install']);
    expect(r.status, r.stderr).toBe(0);
    const w = wt('98-probe-thing');
    expect(git(w, 'rev-parse', '--abbrev-ref', 'HEAD')).toBe('fix/98-probe-thing');
    expect(readFileSync(join(w, 'intents', '98-probe-thing', 'intent.md'), 'utf8')).toBe('# §98 probe\n');
    expect(existsSync(join(repo, 'intents', '98-probe-thing'))).toBe(false);
    expect(readFileSync(join(w, 'CLAUDE.local.md'), 'utf8')).toContain('You are the session for §98');
    expect(git(w, 'status', '--porcelain')).not.toContain('CLAUDE.local.md');
    expect(logOf(repo)).toMatch(/"event":"spawned".*"detail":"port 5298"/);
  });

  it('lists the brief in info/exclude only once however many worktrees are spawned', () => {
    expect(run(SPAWN, ['97', '--no-install']).status).toBe(0);
    const exclude = readFileSync(join(repo, '.git', 'info', 'exclude'), 'utf8');
    expect(exclude.match(/^CLAUDE\.local\.md$/gm)).toHaveLength(1);
  });

  it('refuses to spawn over an existing worktree with the right message', () => {
    const r = run(SPAWN, ['98', '--no-install']);
    expect(r.status).toBe(1);
    expect(r.stderr).toMatch(/already has a worktree/);
    expect(r.stderr).not.toMatch(/Draft it/);
  });

  it('refuses to remove an unmerged worktree', () => {
    const w = wt('98-probe-thing');
    git(w, 'add', 'intents');
    git(w, 'commit', '-q', '-m', '§98 intent');
    const r = run(SPAWN, ['98', '--remove']);
    expect(r.status).toBe(1);
    expect(r.stderr).toMatch(/not merged into main/);
    expect(existsSync(w)).toBe(true);
  });

  it('refuses to remove a worktree holding a link (a shared dependency folder), and leaves the link target alone', () => {
    const target = join(sandbox, 'shared-deps');
    mkdirSync(target);
    writeFileSync(join(target, 'sentinel'), 'keep me');
    const nm = join(wt('98-probe-thing'), 'deps');
    symlinkSync(target, nm, process.platform === 'win32' ? 'junction' : 'dir');
    try {
      const r = run(SPAWN, ['98', '--remove', '--unmerged']);
      expect(r.status).toBe(1);
      expect(r.stderr).toMatch(/is a link/);
      expect(existsSync(wt('98-probe-thing'))).toBe(true);
    } finally {
      unlinkSync(nm);
    }
    expect(readFileSync(join(target, 'sentinel'), 'utf8')).toBe('keep me');
  });

  it('refuses to remove a worktree with uncommitted files', () => {
    const scratch = join(wt('98-probe-thing'), 'scratch.txt');
    writeFileSync(scratch, 'wip');
    try {
      const r = run(SPAWN, ['98', '--remove', '--unmerged']);
      expect(r.status).toBe(1);
      expect(existsSync(scratch)).toBe(true);
    } finally {
      rmSync(scratch);
    }
  });

  it("removes only the named intent's worktree, then re-spawns it from its branch", () => {
    expect(run(SPAWN, ['98', '--remove', '--unmerged']).status).toBe(0);
    expect(existsSync(wt('98-probe-thing'))).toBe(false);
    expect(existsSync(wt('97-neighbour'))).toBe(true); // §97 untouched
    expect(git(repo, 'branch', '--list', 'fix/98-probe-thing')).toContain('fix/98-probe-thing'); // branch kept

    const r = run(SPAWN, ['98', '--no-install']);
    expect(r.status, r.stderr).toBe(0);
    expect(existsSync(join(wt('98-probe-thing'), 'intents', '98-probe-thing', 'metadata.yml'))).toBe(true);
    expect(existsSync(join(repo, 'intents', '98-probe-thing'))).toBe(false);
  });

  it('removes without --unmerged once the branch is merged', () => {
    git(repo, 'merge', '-q', '--no-ff', '-m', 'merge §98', 'fix/98-probe-thing');
    expect(run(SPAWN, ['98', '--remove']).status).toBe(0);
    expect(existsSync(wt('98-probe-thing'))).toBe(false);
    expect(existsSync(wt('97-neighbour'))).toBe(true);
    expect(logOf(repo)).toMatch(/"event":"removed"/);
  });
});

describe('npm run spawn — carrying an intent folder', { timeout: 60_000 }, () => {
  it('leaves an intent that is already committed in the main checkout where it is, and warns about local edits', () => {
    const dir = writeIntent(repo, 96, 'tracked');
    git(repo, 'add', 'intents/96-tracked');
    git(repo, 'commit', '-q', '-m', '§96 intent');
    writeFileSync(join(dir, 'intent.md'), '# §96 edited locally\n');

    const r = run(SPAWN, ['96', '--no-install']);
    expect(r.status, r.stderr).toBe(0);
    expect(r.stderr).toMatch(/uncommitted changes in the main checkout/);
    expect(readFileSync(join(dir, 'intent.md'), 'utf8')).toBe('# §96 edited locally\n'); // not moved or deleted
    expect(readFileSync(join(wt('96-tracked'), 'intents', '96-tracked', 'intent.md'), 'utf8')).toBe('# §96\n');
  });

  it('never overwrites a branch copy with an untracked one from the main checkout', () => {
    const tmp = join(sandbox, 'tmp-95');
    git(repo, 'worktree', 'add', '-q', '-b', 'fix/95-both', tmp, 'main');
    writeIntent(tmp, 95, 'both', '# §95 on the branch\n');
    git(tmp, 'add', 'intents');
    git(tmp, 'commit', '-q', '-m', '§95 intent');
    git(repo, 'worktree', 'remove', tmp);
    const local = writeIntent(repo, 95, 'both', '# §95 untracked draft\n');

    const r = run(SPAWN, ['95', '--no-install']);
    expect(r.status, r.stderr).toBe(0);
    expect(r.stderr).toMatch(/exists both on the branch and untracked/);
    expect(readFileSync(join(local, 'intent.md'), 'utf8')).toBe('# §95 untracked draft\n');
    expect(readFileSync(join(wt('95-both'), 'intents', '95-both', 'intent.md'), 'utf8')).toBe('# §95 on the branch\n');
  });

  it('runs the setup:worktree script when the project defines one, and only warns when it fails', () => {
    const base = (name, script) => {
      const tmp = join(sandbox, `tmp-${name}`);
      git(repo, 'worktree', 'add', '-q', '-b', name, tmp, 'main');
      writeFileSync(join(tmp, 'package.json'), JSON.stringify({ name: 'probe', private: true, scripts: { 'setup:worktree': script } }));
      git(tmp, 'add', 'package.json');
      git(tmp, 'commit', '-q', '-m', 'a project with a setup script');
      git(repo, 'worktree', 'remove', tmp);
    };
    base('with-setup', `node -e "require('fs').writeFileSync('setup-ran','')"`);
    base('with-bad-setup', 'node -e "process.exit(4)"');
    writeIntent(repo, 92, 'setup-ok');
    writeIntent(repo, 91, 'setup-bad');

    const ok = run(SPAWN, ['92', '--base', 'with-setup']);
    expect(ok.status, ok.stderr).toBe(0);
    expect(existsSync(join(wt('92-setup-ok'), 'setup-ran'))).toBe(true);

    const bad = run(SPAWN, ['91', '--base', 'with-bad-setup']);
    expect(bad.status, bad.stderr).toBe(0);
    expect(bad.stderr).toMatch(/setup:worktree --if-present` failed/);
    expect(existsSync(join(wt('91-setup-bad'), 'CLAUDE.local.md'))).toBe(true);
  });

  it('refuses an intent id that is on two branches instead of guessing', () => {
    git(repo, 'branch', 'fix/94-a', 'main');
    git(repo, 'branch', 'feat/94-b', 'main');
    const r = run(SPAWN, ['94', '--no-install']);
    expect(r.status).toBe(1);
    expect(r.stderr).toMatch(/more than one branch/);
    expect(r.stderr).toContain('fix/94-a');
    expect(r.stderr).toContain('feat/94-b');
  });
});

describe('session-event hook', { timeout: 30_000 }, () => {
  it('logs under CLAUDE_PROJECT_DIR, not the cwd, and never logs prompt text', () => {
    const other = join(sandbox, 'other');
    mkdirSync(other);
    git(other, 'init', '-q', '-b', 'main');
    const payload = { hook_event_name: 'UserPromptSubmit', session_id: 's1', cwd: other, prompt: 'token sk-SECRET-9' };
    const r = run(EVENT, [], { cwd: other, env: { ...GIT_ENV, CLAUDE_PROJECT_DIR: repo }, input: JSON.stringify(payload) });
    expect(r.status).toBe(0);
    expect(r.stdout).toBe('');
    expect(logOf(repo)).toMatch(/"event":"UserPromptSubmit".*"promptChars":17/);
    expect(logOf(repo)).not.toContain('SECRET');
    expect(logOf(other)).toBe('');
  });

  it('stays silent and exits 0 on garbage', () => {
    for (const input of ['', 'not json', '[]', 'null']) {
      const r = run(EVENT, [], { input, env: { ...GIT_ENV, CLAUDE_PROJECT_DIR: repo } });
      expect(r.status).toBe(0);
      expect(r.stdout + r.stderr).toBe('');
    }
  });
});
