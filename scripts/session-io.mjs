// The git/fs half of parallel sessions, shared by spawn-intent.mjs,
// sessions.mjs and session-event.mjs. Logic that can be tested without a
// repository lives in session-lib.mjs.
import { execFileSync } from 'node:child_process';
import { appendFileSync, existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { parseBranch, parseMetadata } from './intent-check-lib.mjs';
import { EVENT_LOG } from './session-lib.mjs';

/** Runs git in `cwd` and returns trimmed stdout. Throws on a non-zero exit. */
export function git(cwd, ...args) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
}

/** The shared log: one file in the git common dir, reachable from every worktree. */
export function eventLogPath(cwd) {
  return join(resolve(cwd, git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir')), EVENT_LOG);
}

/** The main checkout: the first entry `git worktree list` reports. */
export function mainCheckout(cwd) {
  const first = git(cwd, 'worktree', 'list', '--porcelain').split(/\r?\n/)[0];
  return first.slice('worktree '.length);
}

/** Facts about the worktree containing `cwd`: its root, branch and intent id. */
export function describeWorktree(cwd) {
  const worktree = git(cwd, 'rev-parse', '--show-toplevel');
  const branch = git(cwd, 'rev-parse', '--abbrev-ref', 'HEAD');
  const parsed = parseBranch(branch);
  return { worktree, branch: branch === 'HEAD' ? null : branch, id: parsed?.id ?? null };
}

/** Appends one event. `fields` must carry at least `event`; worktree facts are filled in from `cwd`. */
export function appendEvent(cwd, fields) {
  const record = { ts: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'), ...describeWorktree(cwd), ...fields };
  appendFileSync(eventLogPath(cwd), `${JSON.stringify(record)}\n`);
}

/** `intents/<id>-*` under `root`, or null. */
export function findIntentDir(root, id) {
  const base = join(root, 'intents');
  if (!existsSync(base)) return null;
  const dir = readdirSync(base).find((d) => d.startsWith(`${id}-`));
  return dir ? `intents/${dir}` : null;
}

/**
 * Intent `id` read from git rather than a working tree: from the first local
 * branch whose name carries that id. This is where an intent lives after
 * spawn has carried its uncommitted folder into the worktree.
 */
export function readIntentMetadataFromBranch(root, id) {
  const branches = git(root, 'for-each-ref', '--format=%(refname:short)', 'refs/heads')
    .split(/\r?\n/)
    .filter((b) => parseBranch(b)?.id === String(id));
  if (branches.length > 1) {
    // Picking one by ref order would spawn whichever sorts first.
    throw new Error(`§${id} is on more than one branch (${branches.join(', ')}). Delete or rename all but one.`);
  }
  const [branch] = branches;
  if (!branch) return null;
  let dirs;
  try {
    dirs = git(root, 'ls-tree', '--name-only', `${branch}:intents`).split(/\r?\n/);
  } catch {
    return null;
  }
  const name = dirs.find((d) => d.startsWith(`${id}-`));
  if (!name) return null;
  const dir = `intents/${name}`;
  try {
    return { dir, metadata: parseMetadata(git(root, 'show', `${branch}:${dir}/metadata.yml`)), branch };
  } catch {
    return null;
  }
}

/** Parsed `metadata.yml` of intent `id` as it stands in the worktree at `root`, or null. */
export function readIntentMetadata(root, id) {
  const dir = findIntentDir(root, id);
  const file = dir && join(root, dir, 'metadata.yml');
  return file && existsSync(file) ? { dir, metadata: parseMetadata(readFileSync(file, 'utf8')) } : null;
}
