// End-to-end tests for `npm run reserve-id`, against throwaway bare
// repositories in the OS temp dir. Never GitHub.
import { spawnSync } from 'node:child_process';
import { chmodSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { reservationSubject } from './reserve-id-lib.mjs';
import { makeSandbox } from './test-git-sandbox.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const RESERVE = join(here, 'reserve-id.mjs');
const QUEUE = join(here, 'queue.mjs');

function setup() {
  const s = makeSandbox('sdlc-reserve-');
  const origin = s.makeOrigin({ 'OVERVIEW.md': 'seed\n', 'app.txt': 'one\n', 'intents/1-first/metadata.yml': s.meta(1, 'first') });
  const a = s.clone(origin, 'a');
  const b = s.clone(origin, 'b');
  const run = (script, cwd, args = []) => {
    const r = spawnSync(process.execPath, [script, ...args], { cwd, env: s.env, encoding: 'utf8' });
    return { ...r, out: r.stdout.trim(), all: `${r.stdout}\n${r.stderr}` };
  };
  const reserve = (cwd, id) => run(RESERVE, cwd, [String(id)]);
  const next = (cwd) => run(QUEUE, cwd, ['--next-id']);
  const draft = (cwd, id, slug, extra = {}) => {
    s.write(cwd, `intents/${id}-${slug}/metadata.yml`, s.meta(id, slug));
    s.write(cwd, `intents/${id}-${slug}/intent.md`, `# §${id}\nthe draft\n`);
    for (const [f, t] of Object.entries(extra)) s.write(cwd, `intents/${id}-${slug}/${f}`, t);
  };
  const remoteRefs = () => s.git(a, 'ls-remote', 'origin');
  return { s, origin, a, b, run, reserve, next, draft, remoteRefs };
}

const withSandbox = (fn) => async () => {
  const x = setup();
  try {
    await fn(x);
  } finally {
    x.s.cleanup();
  }
};

describe('npm run reserve-id', { timeout: 120_000 }, () => {
  it(
    'AC9a: the 2026-11-24 replay: unpushed commits on main do not stop it, and the other machine gets the next number',
    withSandbox(({ s, a, b, reserve, next, draft }) => {
      for (let i = 0; i < 15; i++) s.commitFile(a, `work/${i}.txt`, `${i}\n`, `work ${i}`);
      draft(a, 23, 'a');
      const originMain = s.git(a, 'rev-parse', 'origin/main');
      const localMain = s.git(a, 'rev-parse', 'main');
      const r = reserve(a, 23);
      expect(r.status).toBe(0);
      expect(s.git(a, 'ls-remote', 'origin', 'refs/heads/main').split('\t')[0]).toBe(originMain);
      expect(s.git(a, 'ls-remote', 'origin', 'refs/heads/intent/23')).toMatch(/refs\/heads\/intent\/23/);
      expect(s.git(a, 'rev-parse', 'main')).toBe(localMain);
      expect(s.git(a, 'rev-list', '--count', 'origin/main..main')).toBe('15');
      const n = next(b);
      expect(n.out).toBe('24');
    }),
  );

  it(
    'AC9b: a draft that was never reserved is reported as a clash, and the number moves on',
    withSandbox(({ s, a, b, next, draft }) => {
      draft(a, 23, 'a');
      s.commitFile(b, 'intents/23-b/metadata.yml', s.meta(23, 'b'));
      s.git(b, 'push', '-q', 'origin', 'main');
      const r = next(a);
      expect(r.out).toBe('24');
      expect(r.stderr).toContain('§23 clash: intents/23-a here, intents/23-b on origin (origin/main)');
    }),
  );

  it(
    'AC10: pushes one parentless commit with the two files only, and changes nothing local',
    withSandbox(({ s, a, reserve, draft, remoteRefs }) => {
      draft(a, 7, 'x', { 'spec.md': 'not for origin\n' });
      s.write(a, 'app.txt', 'modified\n'); // unrelated tracked change
      s.write(a, 'untracked.txt', 'u\n');
      const snap = () => ({
        heads: s.git(a, 'for-each-ref', 'refs/heads'),
        index: s.git(a, 'ls-files', '--stage'),
        status: s.git(a, 'status', '--porcelain'),
      });
      const before = snap();
      const refsBefore = remoteRefs().split('\n').filter(Boolean);
      const r = reserve(a, 7);
      expect(r.status).toBe(0);
      expect(r.stdout).toMatch(/reserved §7 on origin as intent\/7 \([0-9a-f]{7,}\)/);
      const refsAfter = remoteRefs().split('\n').filter(Boolean);
      expect(refsAfter.filter((l) => !refsBefore.includes(l)).length).toBe(1);
      expect(refsBefore.filter((l) => !refsAfter.includes(l))).toEqual([]);
      const commit = s.git(a, 'ls-remote', 'origin', 'refs/heads/intent/7').split('\t')[0]; // positive control: it is on origin
      expect(commit).toMatch(/^[0-9a-f]{40}$/);
      expect(s.git(a, 'rev-list', '--parents', '-n', '1', commit).split(' ').length).toBe(1);
      expect(s.git(a, 'ls-tree', '-r', '--name-only', commit).split('\n')).toEqual(['intents/7-x/intent.md', 'intents/7-x/metadata.yml']);
      expect(s.git(a, 'log', '-1', '--format=%s', commit)).toBe(reservationSubject(7, 'intents/7-x'));
      expect(s.git(a, 'rev-parse', 'refs/remotes/origin/intent/7')).toBe(commit);
      expect(snap()).toEqual(before);
    }),
  );

  it(
    'AC10: a folder with only metadata.yml reserves one path',
    withSandbox(({ s, a, reserve }) => {
      s.write(a, 'intents/8-y/metadata.yml', s.meta(8, 'y'));
      expect(reserve(a, 8).status).toBe(0);
      const commit = s.git(a, 'ls-remote', 'origin', 'refs/heads/intent/8').split('\t')[0];
      expect(s.git(a, 'ls-tree', '-r', '--name-only', commit)).toBe('intents/8-y/metadata.yml');
    }),
  );

  it(
    'AC10: works from a worktree',
    withSandbox(({ s, a, reserve }) => {
      const wt = join(s.dir, 'wt');
      s.git(a, 'worktree', 'add', '-q', '-b', 'feat/9-z', wt, 'main');
      s.write(wt, 'intents/9-z/metadata.yml', s.meta(9, 'z'));
      expect(reserve(wt, 9).status).toBe(0);
      expect(s.git(a, 'ls-remote', 'origin', 'refs/heads/intent/9')).toMatch(/intent\/9/);
    }),
  );

  it(
    'AC11: refuses a number another folder holds on origin/main or in a reservation',
    withSandbox(({ s, a, b, reserve, draft, remoteRefs }) => {
      draft(a, 11, 'mine');
      s.commitFile(b, 'intents/11-other/metadata.yml', s.meta(11, 'other'));
      s.git(b, 'push', '-q', 'origin', 'main');
      const before = remoteRefs();
      const r = reserve(a, 11);
      expect(r.status).toBe(1);
      expect(r.all).toContain('taken on origin by intents/11-other (origin/main)');
      expect(remoteRefs()).toBe(before);

      draft(a, 12, 'mine');
      const c = s.orphanCommit(b, { 'intents/12-other/metadata.yml': s.meta(12, 'other') });
      s.git(b, 'push', '-q', 'origin', `${c}:refs/heads/intent/12`);
      const before2 = remoteRefs();
      const r2 = reserve(a, 12);
      expect(r2.status).toBe(1);
      expect(r2.all).toContain('taken on origin by intents/12-other (origin/intent/12)');
      expect(remoteRefs()).toBe(before2);
    }),
  );

  it(
    'AC12: a retry is idempotent, and a folder already on origin/main pushes nothing',
    withSandbox(({ s, a, reserve, draft, remoteRefs }) => {
      draft(a, 13, 'x');
      expect(reserve(a, 13).status).toBe(0);
      const before = remoteRefs();
      const again = reserve(a, 13);
      expect(again.status).toBe(0);
      expect(again.all).toContain('already reserved');
      expect(remoteRefs()).toBe(before);

      s.commitFile(a, 'intents/14-y/metadata.yml', s.meta(14, 'y'));
      s.git(a, 'push', '-q', 'origin', 'main');
      const before2 = remoteRefs();
      const r = reserve(a, 14);
      expect(r.status).toBe(0);
      expect(r.all).toContain('already on origin/main');
      expect(remoteRefs()).toBe(before2);
    }),
  );

  it(
    'AC13: a push that origin refuses is exit 3 with its reason, and no local reservation ref',
    withSandbox(({ s, origin, a, reserve, draft, remoteRefs }) => {
      draft(a, 15, 'x');
      const hook = join(origin, 'hooks', 'pre-receive');
      mkdirSync(dirname(hook), { recursive: true });
      writeFileSync(hook, '#!/bin/sh\necho "refused by test hook" >&2\nexit 1\n');
      chmodSync(hook, 0o755);
      const before = remoteRefs();
      try {
        const r = reserve(a, 15);
        expect(r.status).toBe(3);
        expect(r.all).toContain('refused by test hook');
        expect(remoteRefs()).toBe(before);
        expect(s.git(a, 'for-each-ref', 'refs/remotes/origin/intent')).toBe('');
      } finally {
        rmSync(hook, { force: true });
      }
    }),
  );

  it(
    'AC14: no remote is exit 2, an unreachable origin exit 3, and nothing is written',
    withSandbox(({ s, a, reserve, draft }) => {
      draft(a, 16, 'x');
      const url = s.git(a, 'remote', 'get-url', 'origin');
      s.git(a, 'remote', 'set-url', 'origin', join(s.dir, 'missing.git'));
      const unreachable = reserve(a, 16);
      expect(unreachable.status).toBe(3);
      expect(s.git(a, 'for-each-ref', 'refs/remotes/origin/intent')).toBe('');
      s.git(a, 'remote', 'set-url', 'origin', url);
      s.git(a, 'remote', 'remove', 'origin');
      const none = reserve(a, 16);
      expect(none.status).toBe(2);
      expect(none.all).toContain('nothing was reserved');
    }),
  );

  it(
    'AC15: no folder for the id, or a metadata.yml of another id, pushes nothing',
    withSandbox(({ s, a, reserve, remoteRefs }) => {
      const before = remoteRefs();
      expect(reserve(a, 40).status).toBe(1);
      s.write(a, 'intents/98-x/metadata.yml', s.meta(99, 'x'));
      expect(reserve(a, 98).status).toBe(1);
      expect(remoteRefs()).toBe(before);
    }),
  );

  it(
    'AC16: the source holds no force, no plus refspec, no deletion and no main in a push',
    () => {
      for (const f of ['reserve-id.mjs', 'reserve-id-lib.mjs']) {
        const text = readFileSync(join(here, f), 'utf8');
        for (const bad of ['--force', 'force-with-lease', '--delete', "'+", '"+', '`+', ':refs/heads/main', "'main'"]) {
          expect(text.includes(bad)).toBe(false);
        }
      }
    },
  );
});
