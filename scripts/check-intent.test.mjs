// End-to-end tests for `npm run check:intent`'s live-check enforcement,
// against a throwaway git repository in the OS temp dir — never this
// repository. The rules are unit-tested in intent-check-lib.test.mjs; these
// prove the CLI actually reads review.md (from the branch and from the
// working tree) and refuses a merge check that can't see what's uncommitted.
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';

const CHECK = join(dirname(fileURLToPath(import.meta.url)), 'check-intent.mjs');
const BRANCH = 'feat/97-probe';
const DIR = join('intents', '97-probe');

// Drop inherited GIT_* variables so the sandbox's git never points at this
// repository (a hook or a parent git process may have set them).
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
const check = (...args) => spawnSync(process.execPath, [CHECK, ...args], { cwd: repo, env: GIT_ENV, encoding: 'utf8' });
const write = (name, text) => writeFileSync(join(repo, DIR, name), text);
const metadata = (liveChecked = '') =>
  [
    'id: 97',
    'slug: probe',
    'type: feature',
    'status: in-review',
    'intent_accepted: 2026-10-08',
    'spec_accepted: 2026-10-08',
    'plan_approved: 2026-10-08',
    `live_checked: ${liveChecked}`,
    '',
  ].join('\n');

beforeAll(() => {
  sandbox = mkdtempSync(join(tmpdir(), 'sa-check-'));
  repo = join(sandbox, 'repo');
  mkdirSync(repo);
  git('init', '-q', '-b', 'main');
  git('config', 'core.autocrlf', 'false');
  writeFileSync(join(repo, 'README.md'), 'probe\n');
  git('add', '.');
  git('commit', '-q', '-m', 'init');

  git('checkout', '-q', '-b', BRANCH);
  mkdirSync(join(repo, DIR), { recursive: true });
  for (const f of ['intent.md', 'spec.md', 'plan.md']) write(f, `# §97 ${f}\n`);
  write('metadata.yml', metadata());
  write('review.md', 'verdict: attest\ntier: attested\nlive-check: owed\n\n## Live check\n- steps: …\n');
  git('add', '.');
  git('commit', '-q', '-m', '§97 reviewed, live check owed');
  git('checkout', '-q', 'main');
});

afterAll(() => {
  rmSync(sandbox, { recursive: true, force: true });
});

describe('check:intent and live checks, end to end', { timeout: 60_000 }, () => {
  it('reads a committed review.md in branch mode, from another checkout', () => {
    const r = check(BRANCH);
    expect(r.status, r.stdout + r.stderr).toBe(1);
    expect(r.stdout).toMatch(/A live check is owed and not recorded.*## Live check/);
  });

  it('reads review.md in working-tree mode', () => {
    git('checkout', '-q', BRANCH);
    const r = check();
    expect(r.status, r.stdout + r.stderr).toBe(1);
    expect(r.stdout).toMatch(/A live check is owed/);
  });

  it("fails the branch-mode check while the date is recorded but not committed, in the branch's own checkout", () => {
    write('metadata.yml', metadata('2026-11-09'));
    const wt = check();
    expect(wt.status, wt.stdout).toBe(0); // the working tree has the date
    const br = check(BRANCH);
    expect(br.status, br.stdout).toBe(1);
    expect(br.stdout).toMatch(/changes not committed to feat\/97-probe/);
    expect(br.stdout).toMatch(/A live check is owed/); // what git holds still lacks the date
  });

  it("fails the branch-mode check while review.md is changed but not committed, in the branch's own checkout", () => {
    // The round-1 case: a fresh report on disk that the merge check can't see.
    const committed = metadata('2026-11-09');
    write('metadata.yml', committed);
    git('commit', '-q', '-am', '§97 live check done');
    write('review.md', 'verdict: rework\ntier: attested\nlive-check: owed\n');
    try {
      const r = check(BRANCH);
      expect(r.status, r.stdout).toBe(1);
      expect(r.stdout).toMatch(/changes not committed to feat\/97-probe/);
    } finally {
      git('checkout', '-q', '--', join(DIR, 'review.md'));
    }
  });

  it('passes once the date is committed, from either checkout', () => {
    // Committed by the previous test; review.md was restored there.
    expect(git('status', '--porcelain')).toBe('');
    expect(check(BRANCH).status).toBe(0);
    git('checkout', '-q', 'main');
    const r = check(BRANCH);
    expect(r.status, r.stdout).toBe(0);
  });

  it("ignores another checkout's uncommitted files at the intent's path", () => {
    // The coordinator, on main, may have a stray draft there; it says nothing
    // about what the branch holds.
    mkdirSync(join(repo, DIR), { recursive: true });
    write('review.md', 'verdict: rework\nlive-check: owed\n');
    try {
      const r = check(BRANCH);
      expect(r.status, r.stdout).toBe(0);
    } finally {
      rmSync(join(repo, DIR), { recursive: true, force: true });
    }
  });
});
