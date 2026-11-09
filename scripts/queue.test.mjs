// End-to-end test for `npm run queue`, against a throwaway git repository in
// the OS temp dir — never this repository (same harness as spawn-intent.test.mjs).
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';

const QUEUE = join(dirname(fileURLToPath(import.meta.url)), 'queue.mjs');

// No inherited GIT_* variables: they could point the sandbox's git at the real repository.
const GIT_ENV = {
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^GIT_/i.test(k))),
  GIT_AUTHOR_NAME: 't',
  GIT_AUTHOR_EMAIL: 't@example.com',
  GIT_COMMITTER_NAME: 't',
  GIT_COMMITTER_EMAIL: 't@example.com',
};

let sandbox;
let repo;
const git = (...args) => execFileSync('git', args, { cwd: repo, env: GIT_ENV, encoding: 'utf8' }).trim();
const queue = (...args) => spawnSync(process.execPath, [QUEUE, ...args], { cwd: repo, env: GIT_ENV, encoding: 'utf8' });
const meta = (id, slug, status, extra = '') =>
  `id: ${id}\nslug: ${slug}\ntype: fix\nstatus: ${status}\ntitle: Title ${id}\n${extra}`;
const write = (path, text) => {
  mkdirSync(dirname(join(repo, path)), { recursive: true });
  writeFileSync(join(repo, path), text);
};
const commit = (msg) => {
  git('add', '.');
  git('commit', '-q', '-m', msg);
};

beforeAll(() => {
  sandbox = mkdtempSync(join(tmpdir(), 'sdlc-queue-'));
  repo = join(sandbox, 'repo');
  mkdirSync(repo);
  git('init', '-q', '-b', 'main');
  git('config', 'core.autocrlf', 'false');
  write('OVERVIEW.md', 'old work §3\n');
  write('intents/1-first/metadata.yml', meta(1, 'first', 'accepted'));
  write('intents/2-second/metadata.yml', meta(2, 'second', 'accepted'));
  commit('init');
  // §2's implementer finished on its branch; main still says accepted.
  git('checkout', '-q', '-b', 'fix/2-second');
  write('intents/2-second/metadata.yml', meta(2, 'second', 'in-review'));
  commit('§2 in review');
  // A draft started on a branch that main has never seen.
  git('checkout', '-q', 'main');
  git('checkout', '-q', '-b', 'fix/60-elsewhere');
  write('intents/60-elsewhere/metadata.yml', meta(60, 'elsewhere', 'draft'));
  commit('§60 draft');
  git('checkout', '-q', 'main');
});

afterAll(() => {
  rmSync(sandbox, { recursive: true, force: true });
});

describe('npm run queue', { timeout: 60_000 }, () => {
  it('reads an unmerged branch for status and main for the rest, and says which', () => {
    const r = queue();
    expect(r.status).toBe(0);
    expect(r.stdout).toMatch(/In flight \(2\)/);
    expect(r.stdout).toMatch(/§1 {2}Title 1 {2}\[fix\] accepted {2}.* main/);
    expect(r.stdout).toMatch(/§2 {2}Title 2 {2}\[fix\] in-review {2}.* branch/);
  });

  it('reads main again once the branch is merged', () => {
    git('merge', '-q', '--no-ff', '-m', 'Merge §2', 'fix/2-second');
    const sha = git('rev-parse', '--short=7', 'HEAD');
    write('intents/2-second/metadata.yml', meta(2, 'second', 'done', `merged: ${sha}\n`));
    commit('§2 done');
    const out = queue().stdout;
    expect(out).toMatch(/Shipped \(1\)\n {2}§2 .*\[fix\] done .* main {2}[0-9a-f]{7}/);
    expect(out).toMatch(/In flight \(1\)/);
  });

  it('counts an intent folder that exists only on a branch in --next-id', () => {
    expect(queue('--next-id').stdout.trim()).toBe('61');
  });

  it('--json has the same entries', () => {
    const data = JSON.parse(queue('--json').stdout);
    expect(data.inFlight.map((e) => [e.id, e.source])).toEqual([[1, 'main']]);
    expect(data.shipped.map((e) => [e.id, e.status])).toEqual([[2, 'done']]);
  });

  it('lists Shipped by merge order, newest first, not by id', () => {
    git('checkout', '-q', '-b', 'fix/1-first');
    write('intents/1-first/metadata.yml', meta(1, 'first', 'in-review'));
    commit('§1 in review');
    git('checkout', '-q', 'main');
    git('merge', '-q', '--no-ff', '-m', 'Merge §1', 'fix/1-first');
    const sha = git('rev-parse', '--short=7', 'HEAD');
    write('intents/1-first/metadata.yml', meta(1, 'first', 'done', `merged: ${sha}\n`));
    commit('§1 done');
    // §1 merged after §2, so it is the newer merge although its id is lower
    expect(queue().stdout).toMatch(/Shipped \(2\)\n {2}§1 .*\n {2}§2 /);
  });

  it('lets main win when it says done, although the branch is unmerged and says in-review', () => {
    write('intents/4-fourth/metadata.yml', meta(4, 'fourth', 'done', 'merged: abc1234\n'));
    commit('§4 done');
    git('checkout', '-q', '-b', 'fix/4-fourth');
    write('intents/4-fourth/metadata.yml', meta(4, 'fourth', 'in-review'));
    commit('§4 in review on a kept branch');
    git('checkout', '-q', 'main');
    const out = queue().stdout;
    expect(out).toMatch(/Shipped \(3\)[\s\S]*§4 .*\[fix\] done .* main {2}abc1234/);
    expect(out).toMatch(/In flight \(0\)/);
    const data = JSON.parse(queue('--json').stdout);
    expect(data.shipped.find((e) => e.id === 4)).toMatchObject({ status: 'done', source: 'main' });
  });

  it('--json says branch for an entry read from its unmerged branch', () => {
    write('intents/3-third/metadata.yml', meta(3, 'third', 'accepted'));
    commit('§3 accepted');
    git('checkout', '-q', '-b', 'fix/3-third');
    write('intents/3-third/metadata.yml', meta(3, 'third', 'in-review'));
    commit('§3 in review');
    git('checkout', '-q', 'main');
    const data = JSON.parse(queue('--json').stdout);
    expect(data.inFlight.find((e) => e.id === 3)).toMatchObject({ status: 'in-review', source: 'branch' });
    expect(data.inFlight.find((e) => e.id === 1)).toBeUndefined();
  });

  it('--next-id counts an intent folder that is not committed yet, and the listing does not show it', () => {
    write('intents/70-draft/metadata.yml', meta(70, 'draft', 'draft'));
    try {
      expect(queue('--next-id').stdout.trim()).toBe('71');
      expect(queue().stdout).not.toContain('§70');
    } finally {
      rmSync(join(repo, 'intents', '70-draft'), { recursive: true, force: true });
    }
    expect(queue('--next-id').stdout.trim()).toBe('61');
  });

  it('--next-id reads a higher §N from a working-copy OVERVIEW.md, then from main alone', () => {
    write('OVERVIEW.md', 'a note on §90\n');
    expect(queue('--next-id').stdout.trim()).toBe('91'); // only in the working copy
    write('OVERVIEW.md', 'a note on §95\n');
    commit('OVERVIEW on main');
    write('OVERVIEW.md', 'no section numbers here\n'); // uncommitted edit: §95 is now only on main
    expect(queue('--next-id').stdout.trim()).toBe('96');
    git('checkout', '--', 'OVERVIEW.md');
  });

  it('shows a branch conflict instead of crashing when two branches carry one id', () => {
    write('intents/5-fifth/metadata.yml', meta(5, 'fifth', 'accepted'));
    commit('§5 accepted');
    git('branch', 'fix/5-aaa');
    git('branch', 'fix/5-bbb');
    const r = queue();
    expect(r.status).toBe(0);
    expect(r.stdout).toMatch(/§5 .*\[fix\] accepted .* branch conflict/);
  });
});
