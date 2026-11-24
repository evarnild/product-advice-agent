// Git and process I/O for the commands that talk to `origin` (`npm run queue --
// --next-id`, `npm run reserve-id`): a fetch and a push that cannot wait for
// ever. No decisions are made here; the callers decide what a failure means.
//
// Why not `spawnSync(..., { timeout })`: it kills only the process it started.
// On Windows `git` is a shim that runs another git that runs `ssh` or a
// credential helper; those grandchildren hold the stderr pipe open and
// spawnSync waits for every pipe to close, so a "killed" fetch still blocks
// until the grandchild exits. `runBounded` kills the whole process tree and
// does not wait for the pipes after a timeout.
import { spawn, spawnSync } from 'node:child_process';

export const DEFAULT_TIMEOUT_MS = 10_000;

/** The bound on one fetch or push: SDLC_FETCH_TIMEOUT_MS when a positive integer, else 10 s. */
export function remoteTimeoutMs(env = process.env) {
  const raw = env.SDLC_FETCH_TIMEOUT_MS;
  return typeof raw === 'string' && /^[1-9]\d*$/.test(raw.trim()) ? Number(raw.trim()) : DEFAULT_TIMEOUT_MS;
}

/** Kill `pid` and everything it started. */
function killTree(pid) {
  if (!pid) return;
  try {
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true });
    } else {
      process.kill(-pid, 'SIGKILL'); // the child leads its own process group (detached)
    }
  } catch {
    // already gone
  }
}

/**
 * Run `command`, kill its whole tree after `timeoutMs`. Never rejects:
 * `{ code, timedOut, stdout, stderr }` (code null when killed or not started).
 */
export function runBounded(command, args, { cwd, timeoutMs = DEFAULT_TIMEOUT_MS, env = process.env } = {}) {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    let settled = false;
    let timer;
    let fallback;
    const finish = (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      clearTimeout(fallback);
      resolve({ code, timedOut, stdout, stderr });
    };
    let child;
    try {
      child = spawn(command, args, {
        cwd,
        env,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true,
        detached: process.platform !== 'win32',
      });
    } catch (e) {
      stderr = String(e?.message ?? e);
      finish(null);
      return;
    }
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (d) => (stdout += d));
    child.stderr.on('data', (d) => (stderr += d));
    child.on('error', (e) => {
      stderr += String(e?.message ?? e);
      finish(null);
    });
    // Normal end: wait for `close` so every byte of output is in. After a timeout the
    // pipes may be held by a grandchild: `exit` is enough, and the streams are destroyed.
    child.on('close', (code) => finish(timedOut ? null : code));
    child.on('exit', (code) => {
      if (timedOut) finish(null);
      else fallback = setTimeout(() => finish(code), 2000); // pipes held open by a survivor
    });
    timer = setTimeout(() => {
      timedOut = true;
      clearTimeout(fallback);
      killTree(child.pid);
      child.stdout.destroy();
      child.stderr.destroy();
      fallback = setTimeout(() => finish(null), 2000);
    }, timeoutMs);
  });
}

/** `git` through `runBounded`, with every credential prompt switched off. */
export function runGitBounded(root, args, { timeoutMs = remoteTimeoutMs(), env = process.env } = {}) {
  return runBounded('git', args, {
    cwd: root,
    timeoutMs,
    env: { ...env, GIT_TERMINAL_PROMPT: '0', GCM_INTERACTIVE: 'never' },
  });
}

/** Why a bounded git run failed: "timed out after <n> s" or git's last stderr line. */
export function failureReason(r, timeoutMs = remoteTimeoutMs()) {
  if (r.timedOut) return `timed out after ${Math.round((timeoutMs / 1000) * 10) / 10} s`;
  const lines = (r.stderr || r.stdout || '').split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  return lines.at(-1) ?? `git exited ${r.code}`;
}

/** Fetch every branch of `origin` into refs/remotes/origin/ (no prune, no tags). */
export async function fetchOrigin(root, { timeoutMs = remoteTimeoutMs(), env = process.env } = {}) {
  const r = await runGitBounded(root, ['fetch', '--quiet', '--no-tags', 'origin', '+refs/heads/*:refs/remotes/origin/*'], { timeoutMs, env });
  return r.code === 0 && !r.timedOut ? { ok: true } : { ok: false, reason: failureReason(r, timeoutMs) };
}

/** Is there a remote named `origin`? */
export function hasOrigin(root, env = process.env) {
  return spawnSync('git', ['remote', 'get-url', 'origin'], { cwd: root, env, stdio: 'ignore' }).status === 0;
}
