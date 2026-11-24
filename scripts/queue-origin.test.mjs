// `npm run queue -- --next-id` and `origin` (§28), against throwaway bare
// repositories in the OS temp dir. Nothing reaches a network.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { makeSandbox } from './test-git-sandbox.mjs';

const QUEUE = join(dirname(fileURLToPath(import.meta.url)), 'queue.mjs');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const alive = (pid) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
};

/** A sandbox: origin with main (one intent, §1), clone A (the machine under test) and clone B (the other machine). */
function setup() {
  const s = makeSandbox('sdlc-queue-origin-');
  const origin = s.makeOrigin({ 'OVERVIEW.md': 'seed\n', 'intents/1-first/metadata.yml': s.meta(1, 'first') });
  const a = s.clone(origin, 'a');
  const b = s.clone(origin, 'b');
  const queue = (cwd, args = [], extraEnv = {}) => {
    const t0 = Date.now();
    const r = spawnSync(process.execPath, [QUEUE, ...args], { cwd, env: { ...s.env, ...extraEnv }, encoding: 'utf8' });
    return { ...r, out: r.stdout.trim(), ms: Date.now() - t0 };
  };
  return { s, origin, a, b, queue };
}

const withSandbox = (fn) => async () => {
  const x = setup();
  try {
    await fn(x);
  } finally {
    x.s.cleanup();
  }
};

describe('--next-id and origin', { timeout: 120_000 }, () => {
  it(
    'AC1: fetches origin, so another machine\'s folder on main counts',
    withSandbox(({ s, b, a, queue }) => {
      s.commitFile(b, 'intents/30-x/metadata.yml', s.meta(30, 'x'));
      s.git(b, 'push', '-q', 'origin', 'main');
      expect(s.git(a, 'ls-tree', '--name-only', 'origin/main:intents')).not.toContain('30-x'); // never fetched
      const r = queue(a, ['--next-id']);
      expect(r.status).toBe(0);
      expect(r.out).toBe('31');
    }),
  );

  it(
    'AC2: a reservation branch counts, by its name and by its tree',
    withSandbox(({ s, b, a, queue }) => {
      const c = s.orphanCommit(b, { 'intents/40-r/metadata.yml': s.meta(40, 'r') });
      s.git(b, 'push', '-q', 'origin', `${c}:refs/heads/intent/40`);
      expect(queue(a, ['--next-id']).out).toBe('41');
      const d = s.orphanCommit(b, { 'notes.txt': 'no intents folder\n' });
      s.git(b, 'push', '-q', 'origin', `${d}:refs/heads/intent/45`);
      expect(queue(a, ['--next-id']).out).toBe('46');
    }),
  );

  it(
    'AC4: an origin that cannot be fetched is a warning, and origin counts as last fetched',
    withSandbox(({ s, b, a, queue }) => {
      s.commitFile(b, 'intents/30-x/metadata.yml', s.meta(30, 'x'));
      s.git(b, 'push', '-q', 'origin', 'main');
      expect(queue(a, ['--next-id']).out).toBe('31'); // fetched
      s.git(a, 'remote', 'set-url', 'origin', join(s.dir, 'missing.git'));
      const r = queue(a, ['--next-id']);
      expect(r.status).toBe(0);
      expect(r.stderr).toMatch(/could not fetch origin \(.+\): counted origin as last fetched/);
      expect(r.out).toBe('31');
    }),
  );

  it(
    'AC5: a fetch that hangs is killed at the timeout, with a warning and the local answer',
    withSandbox(({ s, a, queue }) => {
      const hang = join(s.dir, 'hang.mjs');
      const started = join(s.dir, 'hang.started');
      const pidFile = join(s.dir, 'hang.pid');
      s.write(
        s.dir,
        'hang.mjs',
        `import { writeFileSync } from 'node:fs';\nwriteFileSync(${JSON.stringify(started)}, 'started');\nwriteFileSync(${JSON.stringify(pidFile)}, String(process.pid));\nsetTimeout(() => {}, 60000);\n`,
      );
      s.git(a, 'remote', 'set-url', 'origin', 'ssh://example.invalid/r.git');
      s.git(a, 'config', 'ssh.variant', 'simple');
      s.git(a, 'config', 'core.sshCommand', `"${process.execPath.replace(/\\/g, '/')}" "${hang.replace(/\\/g, '/')}"`);
      const r = queue(a, ['--next-id'], { SDLC_FETCH_TIMEOUT_MS: '1000' });
      console.log(`# AC5 hanging fetch returned after ${r.ms} ms`);
      expect(r.status).toBe(0);
      expect(r.out).toBe('2');
      expect(r.stderr).toMatch(/could not fetch origin \(timed out/);
      expect(r.ms).toBeGreaterThanOrEqual(1000);
      expect(r.ms).toBeLessThan(10_000);
      expect(existsSync(started)).toBe(true); // the fake ssh ran, so the test timed out for real
      const pid = Number(readFileSync(pidFile, 'utf8'));
      return (async () => {
        for (let i = 0; i < 20 && alive(pid); i++) await sleep(100);
        expect(alive(pid)).toBe(false);
      })();
    }),
  );

  it(
    'AC6: changes nothing but remote-tracking refs; --no-fetch not even those',
    withSandbox(({ s, b, a, queue }) => {
      const snap = () => ({
        heads: s.git(a, 'for-each-ref', 'refs/heads'),
        head: s.git(a, 'rev-parse', 'HEAD'),
        status: s.git(a, 'status', '--porcelain'),
        index: s.git(a, 'ls-files', '--stage'),
        remotes: s.git(a, 'for-each-ref', 'refs/remotes'),
      });
      s.commitFile(b, 'intents/30-x/metadata.yml', s.meta(30, 'x'));
      s.git(b, 'push', '-q', 'origin', 'main');
      const before = snap();
      const noFetch = queue(a, ['--next-id', '--no-fetch']);
      expect(noFetch.out).toBe('2'); // as last fetched: §30 is not known yet
      expect(snap()).toEqual(before);
      const fetched = queue(a, ['--next-id']);
      expect(fetched.out).toBe('31');
      const after = snap();
      expect(after.remotes === before.remotes).toBe(false); // positive control: the fetch did move origin/main
      expect({ ...after, remotes: '' }).toEqual({ ...before, remotes: '' });
      const again = queue(a, ['--next-id', '--no-fetch']);
      expect(again.out).toBe('31'); // now as last fetched
    }),
  );

  it(
    'AC7: reports a clash on stderr and still prints highest plus one',
    withSandbox(({ s, b, a, queue }) => {
      s.write(a, 'intents/23-a/metadata.yml', s.meta(23, 'a'));
      s.commitFile(b, 'intents/23-b/metadata.yml', s.meta(23, 'b'));
      s.git(b, 'push', '-q', 'origin', 'main');
      const r = queue(a, ['--next-id']);
      expect(r.status).toBe(0);
      expect(r.stderr).toContain('§23 clash: intents/23-a here, intents/23-b on origin (origin/main)');
      expect(r.out).toBe('24');
    }),
  );

  it(
    'AC8: the listing and --json do not fetch; --next-id does',
    withSandbox(({ s, a, queue }) => {
      const fetchHead = join(s.git(a, 'rev-parse', '--absolute-git-dir'), 'FETCH_HEAD');
      // the clone's own fetch made a FETCH_HEAD; remove it and the remote-tracking refs to see what the commands do
      for (const ref of s.git(a, 'for-each-ref', '--format=%(refname)', 'refs/remotes').split('\n').filter(Boolean)) s.git(a, 'update-ref', '-d', ref);
      rmSync(fetchHead, { force: true });
      queue(a, []);
      queue(a, ['--json']);
      expect(existsSync(fetchHead)).toBe(false);
      expect(s.git(a, 'for-each-ref', 'refs/remotes')).toBe('');
      queue(a, ['--next-id']);
      expect(existsSync(fetchHead)).toBe(true); // positive control
    }),
  );
});
