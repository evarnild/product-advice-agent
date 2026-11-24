// Tests for the bounded runner. The tree-kill test spawns its own sleeping
// grandchild and kills only that.
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { remoteTimeoutMs, runBounded } from './remote-io.mjs';

let sandbox;
beforeAll(() => {
  sandbox = mkdtempSync(join(tmpdir(), 'remote-io-'));
});
afterAll(() => rmSync(sandbox, { recursive: true, force: true, maxRetries: 5 }));

const alive = (pid) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

describe('remoteTimeoutMs', () => {
  it('defaults to 10 s and takes a positive integer', () => {
    expect(remoteTimeoutMs({})).toBe(10000);
    expect(remoteTimeoutMs({ SDLC_FETCH_TIMEOUT_MS: '1500' })).toBe(1500);
    for (const bad of ['0', '-5', 'abc', '1.5', '']) expect(remoteTimeoutMs({ SDLC_FETCH_TIMEOUT_MS: bad })).toBe(10000);
  });
});

describe('runBounded', () => {
  it('passes the exit code and output through', async () => {
    const r = await runBounded(process.execPath, ['-e', "console.log('hi');console.error('boom');process.exit(3)"], { timeoutMs: 10000 });
    expect(r.code).toBe(3);
    expect(r.timedOut).toBe(false);
    expect(r.stdout).toContain('hi');
    expect(r.stderr).toContain('boom');
  });

  it('never rejects when the command does not exist', async () => {
    const r = await runBounded('definitely-not-a-command-28', [], { timeoutMs: 5000 });
    expect(r.code).toBe(null);
  });

  it('kills a sleeping grandchild that holds stderr, and returns at the timeout', async () => {
    const pidFile = join(sandbox, 'grandchild.pid');
    writeFileSync(join(sandbox, 'child.mjs'), `import { writeFileSync } from 'node:fs';\nwriteFileSync(${JSON.stringify(pidFile)}, String(process.pid));\nsetTimeout(() => {}, 60000);\n`);
    // On Windows libuv puts a node child in a job object that dies with its parent, which would
    // hide a missing tree kill; a detached grandchild (as git's ssh is) escapes it.
    writeFileSync(
      join(sandbox, 'parent.mjs'),
      `import { spawn } from 'node:child_process';\nspawn(process.execPath, [${JSON.stringify(join(sandbox, 'child.mjs'))}], { stdio: 'inherit', detached: process.platform === 'win32' });\nsetTimeout(() => {}, 60000);\n`,
    );
    const t0 = Date.now();
    const r = await runBounded(process.execPath, [join(sandbox, 'parent.mjs')], { timeoutMs: 1500 });
    const took = Date.now() - t0;
    console.log(`# tree-kill test: runBounded returned after ${took} ms`);
    expect(r.timedOut).toBe(true);
    expect(took).toBeLessThan(10000);
    expect(took).toBeGreaterThanOrEqual(1500);
    expect(existsSync(pidFile)).toBe(true); // the grandchild ran
    const pid = Number(readFileSync(pidFile, 'utf8'));
    for (let i = 0; i < 20 && alive(pid); i++) await sleep(100);
    expect(alive(pid)).toBe(false);
  });
});
