// Tests for the bounded runner. The tree-kill test spawns its own sleeping
// grandchild and kills only that.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { failureReason, remoteTimeoutMs, runBounded, runGitBounded } from './remote-io.mjs';

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

describe('runBounded: a survivor of the tree kill', () => {
  it('returns near the bound although an orphaned grandchild still holds stderr', async () => {
    const pidFile = join(sandbox, 'orphan.pid');
    const q = (x) => JSON.stringify(x);
    writeFileSync(join(sandbox, 'orphan.mjs'), `import { writeFileSync } from 'node:fs';\nwriteFileSync(${q(pidFile)}, String(process.pid));\nsetTimeout(() => {}, 60000);\n`);
    writeFileSync(
      join(sandbox, 'middle.mjs'),
      `import { spawn } from 'node:child_process';\nspawn(process.execPath, [${q(join(sandbox, 'orphan.mjs'))}], { stdio: 'inherit', detached: true }).unref();\nsetTimeout(() => process.exit(0), 800);\n`,
    );
    writeFileSync(
      join(sandbox, 'top.mjs'),
      `import { spawn } from 'node:child_process';\nspawn(process.execPath, [${q(join(sandbox, 'middle.mjs'))}], { stdio: 'inherit', detached: true }).unref();\nsetTimeout(() => {}, 60000);\n`,
    );
    let orphan = null;
    try {
      const t0 = Date.now();
      const r = await runBounded(process.execPath, [join(sandbox, 'top.mjs')], { timeoutMs: 1500 });
      const took = Date.now() - t0;
      expect(r.timedOut).toBe(true);
      expect(took).toBeLessThan(1500 + 1500);
      expect(existsSync(pidFile)).toBe(true);
      orphan = Number(readFileSync(pidFile, 'utf8'));
      expect(alive(orphan)).toBe(true); // it survived the tree kill, and holds the pipe
    } finally {
      if (orphan) {
        try {
          process.kill(orphan); // the one this test started
        } catch {
          // already gone
        }
      }
    }
  });
});

describe('runBounded: the process that called it can exit while an orphan holds the pipe', () => {
  it('destroys its stdio streams, so the event loop is not kept alive by the survivor', () => {
    const pidFile = join(sandbox, 'orphan2.pid');
    const q = (x) => JSON.stringify(x);
    writeFileSync(join(sandbox, 'orphan2.mjs'), `import { writeFileSync } from 'node:fs';\nwriteFileSync(${q(pidFile)}, String(process.pid));\nsetTimeout(() => {}, 60000);\n`);
    writeFileSync(
      join(sandbox, 'middle2.mjs'),
      `import { spawn } from 'node:child_process';\nspawn(process.execPath, [${q(join(sandbox, 'orphan2.mjs'))}], { stdio: 'inherit', detached: true }).unref();\nsetTimeout(() => process.exit(0), 800);\n`,
    );
    writeFileSync(
      join(sandbox, 'top2.mjs'),
      `import { spawn } from 'node:child_process';\nspawn(process.execPath, [${q(join(sandbox, 'middle2.mjs'))}], { stdio: 'inherit', detached: true }).unref();\nsetTimeout(() => {}, 60000);\n`,
    );
    const io = pathToFileURL(join(dirname(fileURLToPath(import.meta.url)), 'remote-io.mjs')).href;
    writeFileSync(
      join(sandbox, 'harness.mjs'),
      `import { runBounded } from ${q(io)};\nconst r = await runBounded(process.execPath, [${q(join(sandbox, 'top2.mjs'))}], { timeoutMs: 1000 });\nconsole.log(r.timedOut ? 'timed out' : 'not timed out');\n`,
    );
    try {
      const t0 = Date.now();
      const r = spawnSync(process.execPath, [join(sandbox, 'harness.mjs')], { encoding: 'utf8', timeout: 15000 });
      const took = Date.now() - t0;
      expect(r.stdout.trim()).toBe('timed out');
      expect(r.error, 'the harness had to be killed: it was kept alive by the orphan\'s pipe').toBe(undefined);
      expect(took).toBeLessThan(8000);
    } finally {
      if (existsSync(pidFile)) {
        try {
          process.kill(Number(readFileSync(pidFile, 'utf8'))); // the orphan this test started
        } catch {
          // already gone
        }
      }
    }
  });
});

describe('runGitBounded', () => {
  it('switches the credential prompts off even when the caller env lacks them', async () => {
    writeFileSync(join(sandbox, 'empty.gitconfig'), '');
    const env = { ...process.env, GIT_CONFIG_GLOBAL: join(sandbox, 'empty.gitconfig'), GIT_CONFIG_NOSYSTEM: '1' };
    delete env.GIT_TERMINAL_PROMPT;
    delete env.GCM_INTERACTIVE;
    const r = await runGitBounded(sandbox, ['-c', 'alias.show-prompts=!echo "$GIT_TERMINAL_PROMPT $GCM_INTERACTIVE"', 'show-prompts'], { timeoutMs: 20000, env });
    expect(r.stdout.trim(), r.stderr).toBe('0 never');
  });
});

describe('failureReason', () => {
  const run = (stderr, extra = {}) => ({ code: 128, timedOut: false, stdout: '', stderr, ...extra });
  it("is git's first fatal: or error: line, not its boilerplate last line", () => {
    const stderr = "fatal: '/x/missing.git' does not appear to be a git repository\nfatal: Could not read from remote repository.\n\nPlease make sure you have the correct access rights\nand the repository exists.\n";
    expect(failureReason(run(stderr))).toBe("fatal: '/x/missing.git' does not appear to be a git repository");
    expect(failureReason(run('hint: x\nerror: first\nfatal: second\n'))).toBe('error: first');
  });
  it('else the first non-empty line, else git exited <code>; a timeout stays a timeout', () => {
    expect(failureReason(run('\n  something odd\nmore\n'))).toBe('something odd');
    expect(failureReason(run(''))).toBe('git exited 128');
    expect(failureReason(run('fatal: x', { timedOut: true, code: null }), 1500)).toBe('timed out after 1.5 s');
  });
});
