// End-to-end tests for `npm run ship`, against throwaway git repositories (a
// main checkout, a bare `origin` and the worktree folder beside it) in the OS temp
// dir. Never the real repository: the script merges and pushes.
import { execFileSync, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, rmdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const SHIP = join(here, 'ship.mjs');

// No inherited GIT_* variable may point the sandbox's git at the real repository.
const GIT_ENV = {
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^GIT_/i.test(k))),
  GIT_AUTHOR_NAME: 't',
  GIT_AUTHOR_EMAIL: 't@example.com',
  GIT_COMMITTER_NAME: 't',
  GIT_COMMITTER_EMAIL: 't@example.com',
};
const VERIFY_OK = 'node -e "process.exit(0)"';
const VERIFY_RED = 'node -e "console.error(\'boom\');process.exit(3)"';
const TRAILER = 'Co-Authored-By: T <t@example.com>';

let sandbox;
let repo;
let origin;
const wt = (name) => join(sandbox, 'product-advice-agent-wt', name);
const git = (cwd, ...args) => execFileSync('git', args, { cwd, env: GIT_ENV, encoding: 'utf8' }).trim();
const ship = (args, verify = VERIFY_OK, opts = {}) =>
  spawnSync(process.execPath, [SHIP, ...args], {
    cwd: opts.cwd ?? repo,
    env: { ...GIT_ENV, SDLC_SHIP_VERIFY: verify },
    encoding: 'utf8',
  });
const out = (r) => `${r.stdout}\n${r.stderr}`;
const read = (...p) => readFileSync(join(repo, ...p), 'utf8');
const branchExists = (b) => {
  try {
    git(repo, 'show-ref', '--verify', '--quiet', `refs/heads/${b}`);
    return true;
  } catch {
    return false;
  }
};

const metadataText = (id, eol, live = '', noMerged = false) =>
  [
    '# generated-by: test',
    `id: ${id}`,
    `slug: t${id}`,
    'type: feature',
    'status: in-review',
    `title: Thing ${id}`,
    'intent_accepted: 2026-10-01',
    'spec_accepted: 2026-10-01',
    'plan_approved: 2026-10-01',
    `live_checked:${live ? ` ${live}` : ''}`,
    ...(noMerged ? [] : ['merged:']),
    '',
  ].join(eol);

/**
 * An intent branch with a worktree: the work commit, then review.md naming it
 * as reviewed-commit. `extra` tunes the verdict, the live-check line, an
 * extra file in the work commit and the review text.
 */
function makeIntent(id, extra = {}) {
  const { verdict = 'escalate', liveCheck = 'not-needed', file = `docs/t${id}.md`, body = '', eol = '\n', live = '', afterReview, reviewedCommit, noMerged = false } = extra;
  const branch = `feat/${id}-t${id}`;
  const path = wt(`${id}-t${id}`);
  git(repo, 'worktree', 'add', '-q', '-b', branch, path, 'main');
  const dir = join(path, 'intents', `${id}-t${id}`);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'metadata.yml'), metadataText(id, eol, live, noMerged));
  for (const f of ['intent.md', 'spec.md', 'plan.md']) writeFileSync(join(dir, f), `# §${id} ${f}\n`);
  mkdirSync(dirname(join(path, file)), { recursive: true });
  writeFileSync(join(path, file), `work ${id}\n`);
  git(path, 'add', '.');
  git(path, 'commit', '-q', '-m', `§${id}: work`);
  let reviewed = git(path, 'rev-parse', '--short', 'HEAD');
  // a commit that is not in the branch's history: the branch was rebased or amended after the review
  if (reviewedCommit === 'sibling') reviewed = git(path, 'commit-tree', 'HEAD^{tree}', '-p', 'main', '-m', 'old review base').slice(0, 7);
  else if (reviewedCommit) reviewed = reviewedCommit;
  writeFileSync(
    join(dir, 'review.md'),
    `# §${id} review\n\nverdict: ${verdict}\ntier: reviewed\nreviewed-commit: ${reviewed}\nround: 2\nsampled: no\nlive-check: ${liveCheck}\n\n## Type check\nPASS\n\n## Findings\n- none\n${body}`,
  );
  git(path, 'add', '.');
  git(path, 'commit', '-q', '-m', `§${id}: review`);
  if (afterReview) afterReview(path);
  return { branch, path, dir: `intents/${id}-t${id}` };
}

beforeAll(() => {
  sandbox = mkdtempSync(join(tmpdir(), 'sdlc-ship-'));
  repo = join(sandbox, 'repo');
  origin = join(sandbox, 'origin.git');
  mkdirSync(repo);
  git(sandbox, 'init', '-q', '--bare', '-b', 'main', origin);
  git(repo, 'init', '-q', '-b', 'main');
  git(repo, 'config', 'core.autocrlf', 'false'); // byte-exact whatever the machine's global setting
  writeFileSync(join(repo, 'README.md'), 'probe\n');
  git(repo, 'add', '.');
  git(repo, 'commit', '-q', '-m', 'init');
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

describe('npm run ship', { timeout: 90_000 }, () => {
  it('refuses to run without an id', () => {
    const r = ship([]);
    expect(r.status).toBe(1);
    expect(r.stderr).toMatch(/usage/);
  });

  it('records the live check, merges, verifies, books, pushes and removes worktree and branch', () => {
    const w = makeIntent(11, { liveCheck: 'owed', eol: '\r\n' });
    const r = ship(['11', '--live-checked', 'it looks "right"', '--trailer', TRAILER]);
    expect(r.status, out(r)).toBe(0);

    const merge = git(repo, 'log', '-1', '--merges', '--format=%h', 'main');
    expect(git(repo, 'log', '-1', '--merges', '--format=%B', 'main')).toBe(`Merge §11: Thing 11\n\n${TRAILER}`);
    expect(git(repo, 'rev-parse', 'origin/main')).toBe(git(repo, 'rev-parse', 'main'));
    expect(git(origin, 'rev-parse', 'main')).toBe(git(repo, 'rev-parse', 'main'));
    expect(existsSync(w.path)).toBe(false);
    expect(branchExists(w.branch)).toBe(false);

    const meta = read('intents', '11-t11', 'metadata.yml');
    expect(meta).toContain('status: done\r\n');
    expect(meta).toContain(`merged: ${merge}    # `);
    expect(meta).toContain(`by-agent    # owner: "it looks 'right'"\r\n`);
    expect(meta.replace(/\r\n/g, '')).not.toMatch(/[\r\n]/); // every line ending stayed CRLF
    expect(git(repo, 'status', '--porcelain')).toBe('');
    expect(git(repo, 'log', '-1', '--format=%B')).toContain(TRAILER);
    const events = readFileSync(join(repo, '.git', 'product-advice-agent-sessions.jsonl'), 'utf8').split(/\r?\n/);
    expect(events.some((l) => l.includes('"event":"shipped"') && l.includes('"id":"11"'))).toBe(true);
    // the order of the report is the order of the steps
    const o = r.stdout;
    for (const [a, b] of [['live-check', 'preconditions'], ['preconditions', 'merge'], ['merge', 'verify'], ['verify', 'bookkeeping'], ['bookkeeping', 'push'], ['push', 'remove']]) {
      expect(o.indexOf(a)).toBeLessThan(o.lastIndexOf(b));
    }
  });

  it('stops at the preconditions on a rework verdict and changes nothing, even with --live-checked', () => {
    const w = makeIntent(12, { verdict: 'rework', liveCheck: 'owed' });
    const before = { main: git(repo, 'rev-parse', 'main'), branch: git(repo, 'rev-parse', w.branch) };
    const r = ship(['12', '--live-checked', 'ok']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+preconditions\s+verdict/);
    expect(git(repo, 'rev-parse', 'main')).toBe(before.main);
    expect(git(repo, 'rev-parse', w.branch)).toBe(before.branch);
    expect(git(repo, 'rev-parse', 'origin/main')).toBe(before.main);
    expect(existsSync(w.path)).toBe(true);
    expect(git(repo, 'status', '--porcelain')).toBe('');
  });

  it('stops when a live check is owed and the owner gave no word', () => {
    const w = makeIntent(17, { liveCheck: 'owed' });
    const before = git(repo, 'rev-parse', w.branch);
    const r = ship(['17']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+preconditions\s+check-intent/);
    expect(r.stdout).toMatch(/live check is owed/);
    expect(git(repo, 'rev-parse', w.branch)).toBe(before);
  });

  it('resumes after a red verify: merged once, no bookkeeping or push until it is green', () => {
    const w = makeIntent(14);
    const origin0 = git(origin, 'rev-parse', 'main');
    const red = ship(['14'], VERIFY_RED);
    expect(red.status, out(red)).toBe(1);
    expect(red.stdout).toMatch(/STOPPED\s+verify/);
    expect(red.stdout).toMatch(/boom/);
    expect(git(repo, 'log', '-1', '--format=%s', 'main')).toBe('Merge §14: Thing 14');
    expect(git(origin, 'rev-parse', 'main')).toBe(origin0);
    expect(read('intents', '14-t14', 'metadata.yml')).toContain('status: in-review');
    expect(existsSync(w.path)).toBe(true);

    const green = ship(['14']);
    expect(green.status, out(green)).toBe(0);
    expect(green.stdout).toMatch(/skipped\s+merge/);
    expect(git(repo, 'log', '--merges', '--format=%s', 'main').split('\n').filter((s) => s === 'Merge §14: Thing 14')).toHaveLength(1);
    expect(git(origin, 'rev-parse', 'main')).toBe(git(repo, 'rev-parse', 'main'));
    expect(read('intents', '14-t14', 'metadata.yml')).toContain('status: done');
    // the hash is the merge commit of the branch tip (second parent), found again after a restart
    const mergeOf14 = git(repo, 'log', '-1', '--merges', '--format=%h', '--grep=^Merge §14:', 'main');
    expect(read('intents', '14-t14', 'metadata.yml')).toContain(`merged: ${mergeOf14}    # `);
    expect(existsSync(w.path)).toBe(false);
    expect(branchExists(w.branch)).toBe(false);

    // and a run after everything is done changes nothing
    const head = git(repo, 'rev-parse', 'main');
    const again = ship(['14']);
    expect(again.status, out(again)).toBe(0);
    expect(again.stdout).toMatch(/skipped\s+bookkeeping/);
    expect(again.stdout).toMatch(/skipped\s+push/);
    expect(git(repo, 'rev-parse', 'main')).toBe(head);
  });

  it('--dry-run prints the plan and changes nothing', () => {
    const w = makeIntent(15, { liveCheck: 'owed' });
    const before = { main: git(repo, 'rev-parse', 'main'), branch: git(repo, 'rev-parse', w.branch) };
    const r = ship(['15', '--dry-run', '--live-checked', 'ok']);
    expect(r.status, out(r)).toBe(0);
    expect(r.stdout).toMatch(/dry run/);
    expect(r.stdout).toMatch(/would\s+live-check/);
    expect(r.stdout).toMatch(/would\s+push/);
    expect(r.stdout).toMatch(/ok\s+preconditions/);
    expect(git(repo, 'rev-parse', 'main')).toBe(before.main);
    expect(git(repo, 'rev-parse', w.branch)).toBe(before.branch);
    expect(git(repo, 'status', '--porcelain')).toBe('');
    expect(git(w.path, 'status', '--porcelain')).toBe('');
    expect(existsSync(w.path)).toBe(true);
  });

  it('reports a worktree it cannot remove, and --cleanup finishes once it can', () => {
    const w = makeIntent(16);
    writeFileSync(join(w.path, 'open-in-an-editor.txt'), 'untracked: git worktree remove refuses this\n');
    const r = ship(['16']);
    expect(r.status, out(r)).toBe(0);
    expect(r.stdout).toMatch(/LEFT\s+remove\s+could not remove/);
    expect(r.stdout).toContain(`npm run ship -- 16 --cleanup`);
    expect(git(origin, 'rev-parse', 'main')).toBe(git(repo, 'rev-parse', 'main')); // everything before it was done
    expect(branchExists(w.branch)).toBe(true);
    expect(existsSync(w.path)).toBe(true);

    const still = ship(['16', '--cleanup']);
    expect(still.stdout).toMatch(/LEFT\s+remove/);
    expect(branchExists(w.branch)).toBe(true);

    rmSync(join(w.path, 'open-in-an-editor.txt'));
    const c = ship(['16', '--cleanup']);
    expect(c.status, out(c)).toBe(0);
    expect(existsSync(w.path)).toBe(false);
    expect(branchExists(w.branch)).toBe(false);
  });

  it('stops on a ROUTE that review.md does not explain, and ships one it does', () => {
    // core code (CORE_CODE) without a test routes the change to a fuller path
    const bad = makeIntent(18, { file: 'src/advisor/models/x18.txt' });
    const before = git(repo, 'rev-parse', 'main');
    const r = ship(['18']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+preconditions\s+check-intent/);
    expect(git(repo, 'rev-parse', 'main')).toBe(before);
    expect(branchExists(bad.branch)).toBe(true);

    const ok = makeIntent(19, { file: 'src/advisor/models/x19.txt', body: '\n## Not checked\n- ROUTE, reason stated: a one-line constant, no behaviour changes.\n' });
    const r2 = ship(['19']);
    expect(r2.status, out(r2)).toBe(0);
    expect(r2.stdout).toMatch(/hold \(check:intent ROUTE\)/);
    expect(branchExists(ok.branch)).toBe(false);
  });
});

/** Another clone pushes a commit to origin, so origin/main is ahead of the repo's main. */
function pushFromElsewhere(name) {
  const clone = join(sandbox, name);
  git(sandbox, 'clone', '-q', origin, clone);
  writeFileSync(join(clone, `${name}.txt`), 'someone else\n');
  git(clone, 'add', '.');
  git(clone, 'commit', '-q', '-m', `elsewhere ${name}`);
  git(clone, 'push', '-q', 'origin', 'main');
}

/** Fetches and fast-forwards main to origin/main; never throws, so it can sit in a finally. */
function catchUpWithOrigin() {
  try {
    git(repo, 'fetch', '-q', 'origin');
    git(repo, 'merge', '-q', '--ff-only', 'origin/main');
  } catch {
    // the failing assertion is the thing to read
  }
}

const snapshot = (w) => ({
  main: git(repo, 'rev-parse', 'main'),
  origin: git(origin, 'rev-parse', 'main'),
  branch: w ? git(repo, 'rev-parse', w.branch) : null,
});

describe('npm run ship: preconditions, wiring and refusals', { timeout: 90_000 }, () => {
  it('refuses a commit added after the reviewed commit, naming the file, and changes nothing', () => {
    const w = makeIntent(28, {
      afterReview: (p) => {
        writeFileSync(join(p, 'docs', 'sneaky.md'), 'not reviewed\n');
        git(p, 'add', '.');
        git(p, 'commit', '-q', '-m', 'sneaky');
      },
    });
    const before = snapshot(w);
    const r = ship(['28']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+preconditions\s+unreviewed-changes/);
    expect(r.stdout).toContain('docs/sneaky.md');
    expect(snapshot(w)).toEqual(before);
    expect(existsSync(w.path)).toBe(true);
  });

  it('refuses a branch whose reviewed-commit is no longer in its history, or does not exist', () => {
    const rebased = makeIntent(29, { reviewedCommit: 'sibling' });
    const before = snapshot(rebased);
    const r = ship(['29']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+preconditions\s+reviewed-commit/);
    expect(r.stdout).toMatch(/not an ancestor/);
    expect(snapshot(rebased)).toEqual(before);

    const bogus = makeIntent(30, { reviewedCommit: 'deadbee' });
    const r2 = ship(['30']);
    expect(r2.stdout).toMatch(/STOPPED\s+preconditions\s+reviewed-commit/);
    expect(existsSync(bogus.path)).toBe(true);
  });

  it('stops when the intent folder on main has uncommitted changes', () => {
    const w = makeIntent(31);
    mkdirSync(join(repo, 'intents', '31-t31'), { recursive: true });
    writeFileSync(join(repo, 'intents', '31-t31', 'note.md'), 'a draft from another session\n');
    try {
      const before = snapshot(w);
      const r = ship(['31']);
      expect(r.status, out(r)).toBe(1);
      expect(r.stdout).toMatch(/STOPPED\s+start\s+intents\/31-t31/);
      expect(snapshot(w)).toEqual(before);
    } finally {
      // only the file this test wrote: were the folder tracked (a mutant let the run merge), it is not ours to delete
      rmSync(join(repo, 'intents', '31-t31', 'note.md'), { force: true });
      try {
        rmdirSync(join(repo, 'intents', '31-t31'));
      } catch {
        // not empty or already gone
      }
    }
  });

  it("stops at the merge on another session's staged file, and keeps their unstaged and untracked files out of every commit", () => {
    const w = makeIntent(32);
    const readme = read('README.md');
    writeFileSync(join(repo, 'staged.txt'), 'staged by someone else\n');
    git(repo, 'add', 'staged.txt');
    try {
      // git itself refuses to merge over a staged change: the run stops there and touches nothing
      const before = snapshot(w);
      const stopped = ship(['32']);
      expect(stopped.status, out(stopped)).toBe(1);
      expect(stopped.stdout).toMatch(/STOPPED\s+merge/);
      expect(snapshot(w)).toEqual(before);
      expect(git(repo, 'status', '--porcelain')).toBe('A  staged.txt');
    } finally {
      git(repo, 'restore', '--staged', 'staged.txt');
    }
    // unstaged and untracked files can stay; they must not be swept into the commits
    writeFileSync(join(repo, 'README.md'), `${readme}edited by someone else\n`);
    try {
      const r = ship(['32']);
      expect(r.status, out(r)).toBe(0);
      expect(git(repo, 'status', '--porcelain').split(/\r?\n/).sort()).toEqual(['?? staged.txt', 'M README.md']);
      expect(git(repo, 'diff', '--name-only', 'HEAD~1', 'HEAD').split(/\r?\n/).sort()).toEqual(['intents/32-t32/metadata.yml']);
      const merge = git(repo, 'log', '-1', '--merges', '--format=%H', 'main');
      const merged = git(repo, 'diff', '--name-only', `${merge}^1`, merge).split(/\r?\n/);
      expect(merged).not.toContain('staged.txt');
      expect(merged).not.toContain('README.md');
    } finally {
      rmSync(join(repo, 'staged.txt'), { force: true });
      writeFileSync(join(repo, 'README.md'), readme);
    }
  });

  it('stops before recording the live check when the worktree metadata.yml has uncommitted changes', () => {
    const w = makeIntent(33, { liveCheck: 'owed' });
    const meta = join(w.path, w.dir, 'metadata.yml');
    writeFileSync(meta, `${readFileSync(meta, 'utf8')}# a half-written edit\n`);
    const before = snapshot(w);
    const r = ship(['33', '--live-checked', 'ok']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+live-check\s+.*uncommitted/);
    expect(snapshot(w)).toEqual(before);
    expect(readFileSync(meta, 'utf8')).toContain('# a half-written edit');
  });

  it('stops when the main checkout is on another branch', () => {
    const w = makeIntent(34);
    git(repo, 'switch', '-q', '-c', 'other');
    try {
      const before = snapshot(w);
      const r = ship(['34']);
      expect(r.status, out(r)).toBe(1);
      expect(r.stdout).toMatch(/STOPPED\s+start\s+the main checkout is on "other"/);
      expect(snapshot(w)).toEqual(before);
    } finally {
      git(repo, 'switch', '-q', 'main');
    }
  });

  it('refuses to run from inside a worktree, even for that worktree', () => {
    const w = makeIntent(35);
    const before = snapshot(w);
    const r = ship(['35'], VERIFY_OK, { cwd: w.path });
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+start\s+run from the main checkout/);
    expect(snapshot(w)).toEqual(before);
  });

  it('ships without the push when there is no origin, and says so', () => {
    const w = makeIntent(36, { liveCheck: 'owed' });
    git(repo, 'remote', 'rename', 'origin', 'upstream');
    try {
      const dry = ship(['36', '--dry-run', '--live-checked', 'ok']);
      expect(dry.status, out(dry)).toBe(0);
      expect(dry.stdout).toMatch(/n\/a\s+push/);
      expect(dry.stdout).not.toMatch(/does not fetch/);
      const r = ship(['36', '--live-checked', 'ok']);
      expect(r.status, out(r)).toBe(0);
      expect(r.stdout).toMatch(/skipped\s+push\s+no remote named origin/);
      expect(git(repo, 'log', '-1', '--merges', '--format=%s', 'main')).toBe('Merge §36: Thing 36');
      expect(read('intents', '36-t36', 'metadata.yml')).toContain('status: done');
      expect(branchExists(w.branch)).toBe(false);
    } finally {
      git(repo, 'remote', 'rename', 'upstream', 'origin');
    }
    // with origin back, the next run pushes what the remote-less run left local
    const again = ship(['36']);
    expect(again.status, out(again)).toBe(0);
    expect(again.stdout).toMatch(/done\s+push/);
    expect(git(origin, 'rev-parse', 'main')).toBe(git(repo, 'rev-parse', 'main'));
  });

  it('stops when origin/main has commits main lacks, before merging anything', () => {
    const w = makeIntent(37);
    pushFromElsewhere('elsewhere37');
    const before = git(repo, 'rev-parse', 'main');
    try {
      const r = ship(['37']);
      expect(r.status, out(r)).toBe(1);
      expect(r.stdout).toMatch(/STOPPED\s+start\s+origin\/main has commits that main lacks/);
      expect(git(repo, 'rev-parse', 'main')).toBe(before);
      expect(branchExists(w.branch)).toBe(true);
    } finally {
      catchUpWithOrigin(); // for the tests after this one, whatever happened here
    }
  });

  it('refuses empty --live-checked words', () => {
    for (const words of ['', '   ']) {
      const r = ship(['11', '--live-checked', words]);
      expect(r.status).toBe(1);
      expect(r.stderr).toMatch(/--live-checked needs the owner/);
    }
  });

  it('does not fetch on --dry-run, and says so', () => {
    makeIntent(45);
    pushFromElsewhere('elsewhere45');
    const remoteTracking = git(repo, 'rev-parse', 'origin/main');
    try {
      const r = ship(['45', '--dry-run']);
      expect(r.status, out(r)).toBe(0);
      expect(r.stdout).toMatch(/does not fetch/);
      expect(git(repo, 'rev-parse', 'origin/main')).toBe(remoteTracking);
    } finally {
      catchUpWithOrigin();
    }
  });

  it('names an existing merge of the branch when its tip moved after a red verify', () => {
    const w = makeIntent(46);
    expect(ship(['46'], VERIFY_RED).status).toBe(1);
    writeFileSync(join(w.path, 'docs', 'more46.md'), 'later\n');
    git(w.path, 'add', '.');
    git(w.path, 'commit', '-q', '-m', 'more work after the merge');
    const r = ship(['46']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+preconditions/);
    expect(r.stdout).toMatch(/main already carries [0-9a-f]+ "Merge §46/);
  });

  it('does not re-record a live check that is already on the branch', () => {
    makeIntent(39, { liveCheck: 'owed', live: '2026-10-01 by-agent    # owner: "earlier"' });
    const r = ship(['39', '--live-checked', 'new words']);
    expect(r.status, out(r)).toBe(0);
    expect(r.stdout).not.toMatch(/done\s+live-check/);
    expect(git(repo, 'log', 'main', '--format=%s', '--grep=§39: live check')).toBe('');
    const meta = read('intents', '39-t39', 'metadata.yml');
    expect(meta).toContain('"earlier"');
    expect(meta).not.toContain('new words');
  });

  it('stops on an intent with no branch and no merge record, and on an unknown id', () => {
    const dir = join(repo, 'intents', '44-t44');
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'metadata.yml'), metadataText(44, '\n'));
    git(repo, 'add', 'intents/44-t44');
    git(repo, 'commit', '-q', '-m', 'an intent on main with no branch');
    git(repo, 'push', '-q', 'origin', 'main');
    const r = ship(['44']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+start\s+the branch for §44 does not exist and main has no merged/);
    const r2 = ship(['99']);
    expect(r2.status).toBe(1);
    expect(r2.stdout).toMatch(/nothing to ship for §99/);
  });
});

describe('npm run ship: failures after the merge', { timeout: 90_000 }, () => {
  const hook = () => join(repo, '.git', 'hooks', 'pre-commit');
  const marker = () => join(repo, '.git', 'reject-commit');

  it('stops before writing anything when metadata.yml has no merged: line', () => {
    const w = makeIntent(50, { noMerged: true });
    const r = ship(['50']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+bookkeeping[\s\S]*could not prepare the bookkeeping \(nothing was written\)/);
    expect(git(repo, 'status', '--porcelain')).toBe('');
    expect(git(repo, 'log', '-1', '--merges', '--format=%s', 'main')).toBe('Merge §50: Thing 50');
    expect(read('intents', '50-t50', 'metadata.yml')).toContain('status: in-review');
    expect(branchExists(w.branch)).toBe(true);
  });

  it('puts the file back and unstages it when the bookkeeping commit is rejected, then resumes', () => {
    makeIntent(41);
    writeFileSync(
      hook(),
      '#!/bin/sh\n[ -e "$(git rev-parse --git-dir)/reject-commit" ] && { echo "rejected by the test hook" >&2; exit 1; }\nexit 0\n',
      { mode: 0o755 },
    );
    writeFileSync(marker(), '');
    try {
      const r = ship(['41']);
      expect(r.status, out(r)).toBe(1);
      expect(r.stdout).toMatch(/STOPPED\s+bookkeeping/);
      expect(r.stdout).toMatch(/rejected by the test hook/);
      expect(git(repo, 'status', '--porcelain')).toBe('');
      expect(read('intents', '41-t41', 'metadata.yml')).toContain('status: in-review');
      rmSync(marker());
      const again = ship(['41']);
      expect(again.status, out(again)).toBe(0);
      expect(read('intents', '41-t41', 'metadata.yml')).toContain('status: done');
    } finally {
      rmSync(hook(), { force: true });
      rmSync(marker(), { force: true });
    }
  });

  it('aborts a conflicting merge and leaves main as it was', () => {
    const w = makeIntent(42, { file: 'docs/c42.md' });
    writeFileSync(join(repo, 'docs', 'c42.md'), 'main says something else\n');
    git(repo, 'add', 'docs/c42.md');
    git(repo, 'commit', '-q', '-m', 'a conflicting change on main');
    git(repo, 'push', '-q', 'origin', 'main');
    const before = snapshot(w);
    const r = ship(['42']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+merge/);
    expect(snapshot(w)).toEqual(before);
    expect(git(repo, 'status', '--porcelain')).toBe('');
    expect(existsSync(join(repo, '.git', 'MERGE_HEAD'))).toBe(false);
    expect(existsSync(w.path)).toBe(true);
  });

  it('resumes a push that was rejected, without a second bookkeeping commit', () => {
    const w = makeIntent(38);
    const good = git(repo, 'remote', 'get-url', 'origin');
    git(repo, 'remote', 'set-url', 'origin', join(sandbox, 'no-such-origin.git'));
    const originBefore = git(origin, 'rev-parse', 'main');
    try {
      const r = ship(['38']);
      expect(r.status, out(r)).toBe(1);
      expect(r.stdout).toMatch(/STOPPED\s+push/);
      expect(git(origin, 'rev-parse', 'main')).toBe(originBefore);
      expect(existsSync(w.path)).toBe(true);
    } finally {
      git(repo, 'remote', 'set-url', 'origin', good);
    }
    const again = ship(['38']);
    expect(again.status, out(again)).toBe(0);
    expect(again.stdout).toMatch(/skipped\s+merge/);
    expect(again.stdout).toMatch(/skipped\s+bookkeeping/);
    expect(again.stdout).toMatch(/done\s+push/);
    expect(git(origin, 'rev-parse', 'main')).toBe(git(repo, 'rev-parse', 'main'));
    expect(git(repo, 'log', 'main', '--format=%s', '--grep=^§38: merged').split(/\r?\n/)).toHaveLength(1);
  });

  it('refuses --cleanup on a branch that is not merged, and keeps it (branch -d, never -D)', () => {
    const w = makeIntent(43);
    git(repo, 'worktree', 'remove', w.path);
    const r = ship(['43', '--cleanup']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+remove/);
    expect(branchExists(w.branch)).toBe(true);
  });
});

describe('npm run ship: leftovers and what a commit may hold', { timeout: 90_000 }, () => {
  const slashes = (t) => t.replace(/\\/g, '/').toLowerCase();

  it('reports a folder left behind after git unregistered the worktree, until the folder is gone', () => {
    const w = makeIntent(47);
    writeFileSync(join(w.path, 'busy.txt'), 'untracked: git worktree remove refuses this\n');
    const first = ship(['47']);
    expect(first.stdout).toMatch(/LEFT\s+remove\s+could not remove/);
    // what a held-open folder does on Windows: git unregisters the worktree, the folder stays
    rmSync(join(w.path, 'busy.txt'));
    git(repo, 'worktree', 'remove', w.path);
    mkdirSync(w.path, { recursive: true });
    writeFileSync(join(w.path, 'held-open.txt'), 'still here\n');

    const second = ship(['47', '--cleanup']);
    expect(second.status, out(second)).toBe(0);
    expect(second.stdout).toMatch(/LEFT\s+remove/);
    expect(slashes(second.stdout)).toContain(slashes(w.path));
    expect(second.stdout).toMatch(/delete it by hand/);
    expect(branchExists(w.branch)).toBe(false); // the branch goes even so

    const third = ship(['47', '--cleanup']); // the branch is gone now; the folder is still reported
    expect(third.stdout).toMatch(/LEFT\s+remove/);
    expect(slashes(third.stdout)).toContain(slashes(w.path));

    rmSync(w.path, { recursive: true, force: true });
    const fourth = ship(['47', '--cleanup']);
    expect(fourth.status, out(fourth)).toBe(0);
    expect(fourth.stdout).toMatch(/done\s+remove/);
    expect(fourth.stdout).not.toMatch(/Left for you/);
  });

  it('never commits a file another session stages while verify runs', () => {
    makeIntent(48);
    const stageDuringVerify = `node -e "require('fs').writeFileSync('other.txt','x');require('child_process').execFileSync('git',['add','other.txt'])"`;
    try {
      const r = ship(['48'], stageDuringVerify);
      expect(r.status, out(r)).toBe(0);
      expect(git(repo, 'diff', '--name-only', 'HEAD~1', 'HEAD').split(/\r?\n/).sort()).toEqual(['intents/48-t48/metadata.yml']);
      expect(git(repo, 'status', '--porcelain')).toBe('A  other.txt');
    } finally {
      try {
        git(repo, 'restore', '--staged', 'other.txt');
      } catch {
        // not staged: nothing to undo
      }
      rmSync(join(repo, 'other.txt'), { force: true });
    }
  });

  it('does not take an unrelated merge for the branch merge when the branch went in without one', () => {
    const w = makeIntent(49);
    git(repo, 'merge', '-q', '--ff-only', w.branch); // merged by hand, fast-forward: no merge commit of its own
    git(repo, 'switch', '-q', '-c', 'side49');
    writeFileSync(join(repo, 'side49.txt'), 'unrelated\n');
    git(repo, 'add', 'side49.txt');
    git(repo, 'commit', '-q', '-m', 'unrelated work');
    git(repo, 'switch', '-q', 'main');
    git(repo, 'merge', '-q', '--no-ff', 'side49', '-m', 'merge of an unrelated branch');
    git(repo, 'push', '-q', 'origin', 'main');
    const r = ship(['49']);
    expect(r.status, out(r)).toBe(1);
    expect(r.stdout).toMatch(/STOPPED\s+bookkeeping\s+cannot find the merge commit/);
    expect(git(repo, 'status', '--porcelain')).toBe('');
    expect(read('intents', '49-t49', 'metadata.yml')).toContain('status: in-review');
  });
});
