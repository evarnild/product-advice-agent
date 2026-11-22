// End-to-end tests for `npm run update-branch`, against throwaway git repositories
// (a main checkout, a bare `origin` and worktrees beside it) in the OS temp dir.
// Never the real repository: the script merges. `verify` is replaced by
// SDLC_UPDATE_BRANCH_VERIFY, a command that writes a marker file.
import { execFileSync, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const UPDATE = join(here, 'update-branch.mjs');

let sandbox;
let repo;
let origin;
let emptyConfig;
let seq = 0;

// No inherited GIT_* variable may point the sandbox's git at the real repository,
// and the machine's git config must not change what a merge does.
const gitEnv = () => ({
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^GIT_/i.test(k))),
  GIT_AUTHOR_NAME: 't',
  GIT_AUTHOR_EMAIL: 't@example.com',
  GIT_COMMITTER_NAME: 't',
  GIT_COMMITTER_EMAIL: 't@example.com',
  GIT_CONFIG_GLOBAL: emptyConfig,
  GIT_CONFIG_NOSYSTEM: '1',
});
const git = (cwd, ...args) => execFileSync('git', args, { cwd, env: gitEnv(), encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const wt = (name) => join(sandbox, 'product-advice-agent-wt', name);
const VERIFY_OK = `node -e "require('fs').writeFileSync(process.env.MARKER, process.cwd())"`;
const VERIFY_RED = `node -e "require('fs').writeFileSync(process.env.MARKER, process.cwd());console.error('boom');process.exit(3)"`;
const norm = (p) => realpathSync(p).replace(/\\/g, '/').toLowerCase();

function update(args, { cwd = repo, verify = VERIFY_OK } = {}) {
  const marker = join(sandbox, `marker-${++seq}`);
  const r = spawnSync(process.execPath, [UPDATE, ...args], {
    cwd,
    env: { ...gitEnv(), SDLC_UPDATE_BRANCH_VERIFY: verify, MARKER: marker },
    encoding: 'utf8',
  });
  return { ...r, marker, text: `${r.stdout}\n${r.stderr}` };
}

function commitFile(cwd, file, content, message = `add ${file}`) {
  mkdirSync(dirname(join(cwd, file)), { recursive: true });
  writeFileSync(join(cwd, file), content);
  git(cwd, 'add', '.');
  git(cwd, 'commit', '-q', '-m', message);
}

/** A worktree on feat/<id>-t<id> from main, with `own` commits of its own (file names). */
function makeBranch(id, own = [`own-${id}.txt`]) {
  const path = wt(`${id}-t${id}`);
  git(repo, 'worktree', 'add', '-q', '-b', `feat/${id}-t${id}`, path, 'main');
  for (const f of own) commitFile(path, f, `own ${id}\n`);
  return { path, branch: `feat/${id}-t${id}` };
}

const moveMain = (file, content = 'from main\n') => commitFile(repo, file, content, `main: ${file}`);

const state = (cwd) => ({
  head: git(cwd, 'rev-parse', 'HEAD'),
  status: git(cwd, 'status', '--porcelain'),
});

/** Everything the script must never change: main, every other branch, origin, remote-tracking refs, FETCH_HEAD. */
function snapshot(target) {
  const common = git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir');
  return {
    main: git(repo, 'rev-parse', 'main'),
    others: git(repo, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads').split(/\r?\n/).filter((l) => !l.startsWith(`refs/heads/${target}`)),
    origin: git(repo, 'ls-remote', 'origin'),
    remotes: git(repo, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/remotes'),
    fetchHead: existsSync(join(common, 'FETCH_HEAD')),
  };
}

beforeAll(() => {
  sandbox = mkdtempSync(join(tmpdir(), 'sdlc-update-'));
  emptyConfig = join(sandbox, 'empty-gitconfig');
  writeFileSync(emptyConfig, '');
  repo = join(sandbox, 'repo');
  origin = join(sandbox, 'origin.git');
  mkdirSync(repo);
  git(sandbox, 'init', '-q', '--bare', '-b', 'main', origin);
  git(repo, 'init', '-q', '-b', 'main');
  git(repo, 'config', 'core.autocrlf', 'false');
  commitFile(repo, 'README.md', 'probe\n', 'init');
  git(repo, 'remote', 'add', 'origin', origin);
  git(repo, 'push', '-q', 'origin', 'main');
});

afterAll(() => {
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

describe('npm run update-branch: outcomes', { timeout: 90_000 }, () => {
  it('up to date: exit 0, says it contains main, changes nothing, runs no verify', () => {
    const w = makeBranch(61);
    const head = git(w.path, 'rev-parse', 'HEAD');
    const snap = snapshot(w.branch);
    const r = update(['61']);
    expect(r.status, r.text).toBe(0);
    expect(r.stdout).toContain(`contains main at ${git(repo, 'rev-parse', '--short', 'main')}`);
    expect(git(w.path, 'rev-parse', 'HEAD')).toBe(head);
    expect(existsSync(r.marker)).toBe(false);
    expect(snapshot(w.branch)).toEqual(snap);
  });

  it('behind with own commits and green verify: a merge commit of old tip and main, verify ran in the worktree', () => {
    const w = makeBranch(62);
    const oldTip = git(w.path, 'rev-parse', 'HEAD');
    moveMain('m62a.txt');
    moveMain('m62b.txt');
    const snap = snapshot(w.branch);
    const r = update(['62']);
    expect(r.status, r.text).toBe(0);
    expect(r.stdout).toContain('behind main by 2');
    expect(r.stdout).toContain('verify green');
    const head = git(w.path, 'rev-parse', 'HEAD');
    expect(git(w.path, 'rev-list', '--parents', '-n1', 'HEAD')).toBe(`${head} ${oldTip} ${git(repo, 'rev-parse', 'main')}`);
    expect(r.stdout).toContain(head.slice(0, 7));
    expect(r.stdout).toContain(git(repo, 'rev-parse', '--short', 'main'));
    expect(norm(readFileSync(r.marker, 'utf8'))).toBe(norm(w.path));
    expect(git(w.path, 'status', '--porcelain')).toBe('');
    expect(snapshot(w.branch)).toEqual(snap);
  });

  it('behind with no commits of its own: a fast-forward, no merge commit', () => {
    const w = makeBranch(63, []);
    moveMain('m63.txt');
    const r = update(['63']);
    expect(r.status, r.text).toBe(0);
    expect(git(w.path, 'rev-parse', 'HEAD')).toBe(git(repo, 'rev-parse', 'main'));
    expect(existsSync(r.marker)).toBe(true);
  });

  it('red verify: exit 3, the output tail, the merge is kept', () => {
    const w = makeBranch(64);
    const oldTip = git(w.path, 'rev-parse', 'HEAD');
    moveMain('m64.txt');
    const snap = snapshot(w.branch);
    const r = update(['64'], { verify: VERIFY_RED });
    expect(r.status, r.text).toBe(3);
    expect(r.stdout).toContain('verify red after merging main');
    expect(r.stdout).toContain('boom');
    expect(git(w.path, 'rev-parse', 'HEAD^1')).toBe(oldTip);
    expect(git(w.path, 'rev-parse', 'HEAD^2')).toBe(git(repo, 'rev-parse', 'main'));
    expect(snapshot(w.branch)).toEqual(snap);
  });

  it('conflict: exit 2, the file named, HEAD unchanged, clean status, no MERGE_HEAD, no verify', () => {
    commitFile(repo, 'shared65.txt', 'line\n');
    const w = makeBranch(65, []);
    commitFile(w.path, 'shared65.txt', 'branch side\n');
    moveMain('shared65.txt', 'main side\n');
    const before = state(w.path);
    const snap = snapshot(w.branch);
    const r = update(['65']);
    expect(r.status, r.text).toBe(2);
    expect(r.stdout).toContain('shared65.txt');
    expect(state(w.path)).toEqual(before);
    expect(git(w.path, 'status', '--porcelain', '--untracked-files=no')).toBe('');
    expect(() => git(w.path, 'rev-parse', '-q', '--verify', 'MERGE_HEAD')).toThrow();
    expect(existsSync(r.marker)).toBe(false);
    expect(snapshot(w.branch)).toEqual(snap);
  });

  it('runs the same from the worktree itself', () => {
    const w = makeBranch(66);
    const oldTip = git(w.path, 'rev-parse', 'HEAD');
    moveMain('m66.txt');
    const r = update(['66'], { cwd: w.path });
    expect(r.status, r.text).toBe(0);
    expect(git(w.path, 'rev-parse', 'HEAD^1')).toBe(oldTip);
    expect(git(w.path, 'rev-parse', 'HEAD^2')).toBe(git(repo, 'rev-parse', 'main'));
  });

  it('keeps the old tip in history and never rebases', () => {
    const w = makeBranch(67, ['a67.txt', 'b67.txt']);
    const oldTip = git(w.path, 'rev-parse', 'HEAD');
    moveMain('m67.txt');
    const r = update(['67']);
    expect(r.status, r.text).toBe(0);
    expect(() => git(w.path, 'merge-base', '--is-ancestor', oldTip, 'HEAD')).not.toThrow();
  });
});

describe('npm run update-branch: refusals change nothing', { timeout: 90_000 }, () => {
  function refused(id, w, r, reason) {
    expect(r.status, r.text).toBe(1);
    expect(r.text).toMatch(reason);
    expect(existsSync(r.marker)).toBe(false);
  }

  it('usage: no id', () => {
    const r = update([]);
    expect(r.status).toBe(1);
    expect(r.text).toContain('usage');
  });

  it('no worktree for the id', () => {
    const snap = snapshot('none');
    const r = update(['68']);
    refused('68', null, r, /no worktree/);
    expect(snapshot('none')).toEqual(snap);
  });

  it('the id is checked out in the main checkout', () => {
    git(repo, 'checkout', '-q', '-b', 'feat/69-t69');
    try {
      moveMain('m69.txt'); // on feat/69, so main is not moved; the branch is behind nothing
      const head = git(repo, 'rev-parse', 'HEAD');
      const r = update(['69']);
      refused('69', null, r, /main checkout/);
      expect(git(repo, 'rev-parse', 'HEAD')).toBe(head);
    } finally {
      git(repo, 'checkout', '-q', 'main');
    }
  });

  it('a detached worktree at <id>-...', () => {
    const path = wt('70-x');
    git(repo, 'worktree', 'add', '-q', '--detach', path, 'main');
    const before = state(path);
    moveMain('m70.txt');
    const r = update(['70']);
    refused('70', null, r, /HEAD is detached/);
    expect(state(path)).toEqual(before);
  });

  it('a merge in progress', () => {
    commitFile(repo, 'shared71.txt', 'line\n');
    const w = makeBranch(71, []);
    commitFile(w.path, 'shared71.txt', 'branch\n');
    moveMain('shared71.txt', 'main\n');
    expect(() => git(w.path, 'merge', '--no-edit', 'main')).toThrow();
    const before = state(w.path);
    const snap = snapshot(w.branch);
    const r = update(['71']);
    refused('71', w, r, /merge is in progress/);
    expect(state(w.path)).toEqual(before);
    expect(git(w.path, 'rev-parse', '-q', '--verify', 'MERGE_HEAD')).toBeTruthy();
    expect(snapshot(w.branch)).toEqual(snap);
  });

  it('a cherry-pick in progress', () => {
    const w = makeBranch(72, []);
    const side = wt('72-side');
    git(repo, 'worktree', 'add', '-q', '-b', 'side-72', side, w.branch);
    commitFile(side, 'cp72.txt', 'side\n');
    commitFile(w.path, 'cp72.txt', 'branch\n');
    expect(() => git(w.path, 'cherry-pick', 'side-72')).toThrow();
    moveMain('m72.txt');
    const before = state(w.path);
    const r = update(['72']);
    refused('72', w, r, /cherry-pick is in progress/);
    expect(state(w.path)).toEqual(before);
  });

  it('a rebase in progress', () => {
    commitFile(repo, 'shared73.txt', 'line\n');
    const w = makeBranch(73, []);
    commitFile(w.path, 'shared73.txt', 'branch\n');
    moveMain('shared73.txt', 'main\n');
    expect(() => git(w.path, 'rebase', 'main')).toThrow();
    const before = state(w.path);
    const r = update(['73']);
    refused('73', w, r, /rebase is in progress/);
    expect(state(w.path)).toEqual(before);
  });

  it('a modified tracked file', () => {
    const w = makeBranch(74);
    writeFileSync(join(w.path, 'own-74.txt'), 'edited\n');
    moveMain('m74.txt');
    const before = state(w.path);
    const r = update(['74']);
    refused('74', w, r, /modified or staged/);
    expect(r.text).toContain('own-74.txt');
    expect(state(w.path)).toEqual(before);
  });

  it('a staged new file', () => {
    const w = makeBranch(75);
    writeFileSync(join(w.path, 'staged75.txt'), 'x\n');
    git(w.path, 'add', 'staged75.txt');
    moveMain('m75.txt');
    const before = state(w.path);
    const r = update(['75']);
    refused('75', w, r, /modified or staged/);
    expect(state(w.path)).toEqual(before);
  });

  it('an untracked file in the way of main: git refuses, its message is relayed, the file is intact', () => {
    const w = makeBranch(76);
    moveMain('docs/inway76.md', 'main version\n');
    mkdirSync(join(w.path, 'docs'), { recursive: true });
    writeFileSync(join(w.path, 'docs', 'inway76.md'), 'mine\n');
    const head = git(w.path, 'rev-parse', 'HEAD');
    const snap = snapshot(w.branch);
    const r = update(['76']);
    expect(r.status, r.text).toBe(1);
    expect(r.stdout).toContain('refused');
    expect(r.stdout).toContain('inway76.md');
    expect(existsSync(r.marker)).toBe(false);
    expect(git(w.path, 'rev-parse', 'HEAD')).toBe(head);
    expect(readFileSync(join(w.path, 'docs', 'inway76.md'), 'utf8')).toBe('mine\n');
    expect(() => git(w.path, 'rev-parse', '-q', '--verify', 'MERGE_HEAD')).toThrow();
    expect(snapshot(w.branch)).toEqual(snap);
  });
});
