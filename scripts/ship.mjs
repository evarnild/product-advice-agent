#!/usr/bin/env node
// `npm run ship -- <id> [--live-checked "<owner's words>"] [--dry-run] [--cleanup] [--trailer "<line>"]...`
//
// Ships a reviewed intent the way REVIEW-POLICY.md → "Merging" says: record the
// live check (only on the owner's word), check the merge preconditions from
// git, merge --no-ff with the message from a file, `npm run verify` on main,
// the bookkeeping commit, push, then remove the worktree and delete the
// branch. It stops at the first step that fails and names it; run again and
// it resumes (every step first checks whether it is already done). The
// decisions live in ship-lib.mjs; this file is the git half. A repository
// with no remote named `origin` is shipped without the push (the step reads
// "skipped"); with one, main must not be behind origin/main.
//
// Run it from the main checkout, on main. It never forces, resets, deletes with
// -D, stages anything but the files a step wrote, or stops a process.
//
// SDLC_SHIP_VERIFY, when set, is a command line that runs in place of
// `npm run verify` (ship.test.mjs sets it in a throwaway repository).
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseGate, parseMetadata, parseReviewHeader } from './intent-check-lib.mjs';
import { appendEvent, findIntentDir, git, mainCheckout, readIntentMetadataFromBranch } from './session-io.mjs';
import { branchFor, parseWorktreeList, pathKey, worktreePathFor } from './session-lib.mjs';
import {
  checkPreconditions,
  commitMessage,
  isBookkept,
  markLiveChecked,
  markMerged,
  mergeMessage,
  planSteps,
  routeReasonStated,
} from './ship-lib.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const CHECK_INTENT = join(here, 'check-intent.mjs');
const SPAWN = join(here, 'spawn-intent.mjs');

class Stop extends Error {
  constructor(step, message) {
    super(message);
    this.step = step;
  }
}

function parseShipArgs(argv) {
  const out = { id: null, liveChecked: null, dryRun: false, cleanup: false, trailers: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--live-checked') {
      out.liveChecked = (argv[++i] ?? '').trim();
      if (!out.liveChecked) throw new Error('--live-checked needs the owner words (quoted), not an empty string');
    } else if (a === '--trailer') out.trailers.push(argv[++i] ?? '');
    else if (a === '--dry-run') out.dryRun = true;
    else if (a === '--cleanup') out.cleanup = true;
    else if (/^\d+$/.test(a) && out.id === null) out.id = a;
    else throw new Error(`unexpected argument "${a}"`);
  }
  return out;
}

const gitOk = (cwd, ...args) => {
  try {
    git(cwd, ...args);
    return true;
  } catch {
    return false;
  }
};
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const hasOrigin = (root) => gitOk(root, 'remote', 'get-url', 'origin');
const errText = (e) => (e.stderr?.toString().trim() || e.stdout?.toString().trim() || e.message).trim();

/** Runs `fn(path)` with `text` in a temporary file (messages go by -F, never by stdin, so no shell can mangle them). */
function withMessageFile(text, fn) {
  const dir = mkdtempSync(join(tmpdir(), 'ship-msg-'));
  const file = join(dir, 'message.txt');
  writeFileSync(file, text);
  try {
    return fn(file);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

/** Commits exactly `paths` (pathspec form: anything else staged by another session stays out). */
function commitPaths(cwd, paths, message) {
  git(cwd, 'add', '--', ...paths);
  withMessageFile(message, (file) => git(cwd, 'commit', '-q', '-F', file, '--', ...paths));
  return git(cwd, 'rev-parse', '--short', 'HEAD');
}

// ---- inspecting the repository ------------------------------------------------

function worktreeOf(root, branch) {
  return parseWorktreeList(git(root, 'worktree', 'list', '--porcelain')).find(
    (w) => w.branch === branch && pathKey(w.path) !== pathKey(root),
  );
}

/** What the run needs to know about intent `id`, from git. Stops if it can't be found. */
function locate(root, id) {
  const onBranch = readIntentMetadataFromBranch(root, id);
  if (onBranch) {
    const { dir, metadata, branch } = onBranch;
    return { dir, metadata, branch, branchExists: true };
  }
  // The branch is gone: valid only for a run resuming after the merge.
  const dir = findIntentDir(root, id);
  const file = dir && join(root, dir, 'metadata.yml');
  if (!file || !existsSync(file)) throw new Stop('start', `no branch and no intents/${id}-*/ on main: nothing to ship for §${id}.`);
  const metadata = parseMetadata(readFileSync(file, 'utf8'));
  if (typeof metadata.merged !== 'string' || !metadata.merged) throw new Stop('start', `the branch for §${id} does not exist and main has no merged: record for it.`);
  return { dir, metadata, branch: branchFor({ type: metadata.type, id, slug: metadata.slug }), branchExists: false };
}

/** The intent's folder on main has no uncommitted changes (another session's work: never committed as ours). */
function checkMetadataClean(root, loc) {
  const dirty = git(root, 'status', '--porcelain', '--', loc.dir);
  if (dirty) throw new Stop('start', `${loc.dir} has uncommitted changes on main (another session's work?). Commit or discard them, then re-run:
${dirty}`);
}

/** Where it runs and what must be clean. */
function checkStart(root, loc, dryRun) {
  if (pathKey(git(process.cwd(), 'rev-parse', '--show-toplevel')) !== pathKey(root)) {
    throw new Stop('start', `run from the main checkout (${root}), not from a worktree.`);
  }
  const current = git(root, 'rev-parse', '--abbrev-ref', 'HEAD');
  if (current !== 'main') throw new Stop('start', `the main checkout is on "${current}", not main.`);
  checkMetadataClean(root, loc);
  if (!hasOrigin(root)) return; // nothing to push to, so nothing to be behind: the push step is skipped
  // --dry-run does not fetch (it changes nothing, remote-tracking refs included): origin/main is as last fetched.
  if (!dryRun) gitOk(root, 'fetch', '-q', 'origin');
  if (gitOk(root, 'rev-parse', '--verify', '-q', 'origin/main') && !gitOk(root, 'merge-base', '--is-ancestor', 'origin/main', 'main')) {
    throw new Stop('start', 'origin/main has commits that main lacks, so the push would be rejected. Bring main up to date with origin first, then re-run.');
  }
}

function readState(root, id, loc, opts) {
  const merged = !loc.branchExists || gitOk(root, 'merge-base', '--is-ancestor', loc.branch, 'main');
  const wt = loc.branchExists ? worktreeOf(root, loc.branch) : undefined;
  let bookkept = false;
  if (merged && existsSync(join(root, loc.dir, 'metadata.yml'))) {
    const meta = parseMetadata(readFileSync(join(root, loc.dir, 'metadata.yml'), 'utf8'));
    bookkept = isBookkept(meta);
  }
  const originMain = (() => {
    try {
      return git(root, 'rev-parse', '--verify', '-q', 'origin/main');
    } catch {
      return null;
    }
  })();
  return {
    wt,
    state: {
      liveCheckRequested: opts.liveChecked !== null,
      liveCheckRecorded: parseGate(loc.metadata.live_checked).state === 'recorded',
      merged,
      bookkept,
      // Not "pushed" before the bookkeeping commit: main will still move.
      pushed: bookkept && originMain !== null && originMain === git(root, 'rev-parse', 'main'),
      hasRemote: hasOrigin(root),
      cleanedUp: !wt && !loc.branchExists && !leftoverFolder(root, id, loc),
    },
  };
}

// ---- preconditions ------------------------------------------------------------

function readReview(root, branch, dir) {
  try {
    const text = git(root, 'show', `${branch}:${dir}/review.md`);
    return { text, header: parseReviewHeader(text) };
  } catch {
    return { text: '', header: null };
  }
}

function preconditionInputs(root, loc) {
  const review = readReview(root, loc.branch, loc.dir);
  const rc = review.header?.['reviewed-commit'];
  const isAncestor = !!rc && gitOk(root, 'merge-base', '--is-ancestor', rc, loc.branch);
  const changedFiles = isAncestor ? git(root, 'diff', '--name-only', rc, loc.branch).split(/\r?\n/).filter(Boolean) : [];
  return { reviewHeader: review.header, isAncestor, changedFiles, intentDir: loc.dir, reviewText: review.text };
}

function runCheckIntent(root, branch, reviewText) {
  const r = spawnSync(process.execPath, [CHECK_INTENT, branch], { cwd: root, encoding: 'utf8' });
  const verdict = r.status === 0 ? 'PASS' : r.status === 2 ? 'ROUTE' : 'FAIL';
  return { verdict, reasonStated: routeReasonStated(reviewText), output: (r.stdout || r.stderr || '').trim() };
}

/** Evaluates preconditions; `withCheck` false evaluates the review part only (before anything is written). */
function evaluatePreconditions(root, loc, withCheck) {
  const input = preconditionInputs(root, loc);
  const checkIntent = withCheck ? runCheckIntent(root, loc.branch, input.reviewText) : undefined;
  const result = checkPreconditions({ ...input, checkIntent });
  return { result, checkIntent };
}

// ---- steps --------------------------------------------------------------------

function recordLiveCheck(root, loc, wt, opts, trailers) {
  if (!wt) throw new Stop('live-check', `${loc.branch} has no worktree to commit the live check in. Spawn one (npm run spawn -- ${loc.metadata.id}) or record live_checked: by hand.`);
  const file = join(wt.path, loc.dir, 'metadata.yml');
  if (git(wt.path, 'status', '--porcelain', '--', `${loc.dir}/metadata.yml`)) {
    throw new Stop('live-check', `${loc.dir}/metadata.yml has uncommitted changes in ${wt.path}.`);
  }
  writeFileSync(file, markLiveChecked(readFileSync(file, 'utf8'), today(), opts.liveChecked));
  const hash = commitPaths(wt.path, [`${loc.dir}/metadata.yml`], commitMessage(`§${loc.metadata.id}: live check recorded (on the owner's word)`, trailers));
  return `recorded live_checked: ${today()} by-agent on ${loc.branch} (${hash})`;
}

function mergeBranch(root, loc, trailers) {
  const before = git(root, 'rev-parse', 'HEAD');
  try {
    withMessageFile(mergeMessage(loc.metadata.id, loc.metadata.title, trailers), (file) =>
      git(root, 'merge', '--no-ff', loc.branch, '-F', file),
    );
  } catch (e) {
    gitOk(root, 'merge', '--abort'); // leaves main as it was; nothing of anyone's work is dropped
    throw new Stop('merge', `git merge failed (main left at ${before.slice(0, 7)}): ${errText(e)}`);
  }
  return git(root, 'rev-parse', 'HEAD');
}

function runVerify(root) {
  const command = process.env.SDLC_SHIP_VERIFY || 'npm run verify';
  const r = spawnSync(command, { cwd: root, shell: true, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  if (r.status === 0) return `\`${command}\` is green on main`;
  const tail = `${r.stdout ?? ''}${r.stderr ?? ''}`.trim().split(/\r?\n/).slice(-25).join('\n');
  throw new Stop('verify', `\`${command}\` failed on main AFTER the merge. Nothing was undone, pushed or removed; undoing a merge is the owner's call.\n${tail}`);
}

/** The merge commit of `branch` on main: the commit whose second parent is the branch tip. */
function findMergeCommit(root, branch) {
  const tip = git(root, 'rev-parse', branch);
  const lines = git(root, 'rev-list', '--merges', '--parents', '--ancestry-path', `${tip}..main`).split(/\r?\n/).filter(Boolean);
  const found = lines.map((l) => l.split(' ')).filter((p) => p[2] === tip);
  if (!found.length) throw new Stop('bookkeeping', `cannot find the merge commit of ${branch} on main (was it merged without --no-ff?).`);
  return found.at(-1)[0];
}

/** The bookkeeping edit: `merged:` and `status: done` in metadata.yml (old and new text; bookkeeping() writes them). */
function bookkeepMetadata(root, loc, hash) {
  const file = join(root, loc.dir, 'metadata.yml');
  const before = readFileSync(file, 'utf8');
  return { rel: `${loc.dir}/metadata.yml`, file, before, after: markMerged(before, hash, today()) };
}

/**
 * All or nothing: the new text is computed before anything is written, and a
 * failed write or commit puts the file back and unstages it, so the leftover
 * is never mistaken for another session's work by the next run.
 */
function bookkeeping(root, loc, trailers) {
  const id = loc.metadata.id;
  const hash = findMergeCommit(root, loc.branch).slice(0, 7);
  let edits;
  try {
    edits = [bookkeepMetadata(root, loc, hash)];
  } catch (e) {
    throw new Stop('bookkeeping', `could not prepare the bookkeeping (nothing was written): ${errText(e)}`);
  }
  try {
    for (const x of edits) writeFileSync(x.file, x.after);
    const message = commitMessage(`§${id}: merged (${hash}); status done`, trailers);
    const commit = commitPaths(root, edits.map((x) => x.rel), message);
    return `merged: ${hash}, status done (${commit})`;
  } catch (e) {
    for (const x of edits) writeFileSync(x.file, x.before);
    gitOk(root, 'restore', '--staged', '--', ...edits.map((x) => x.rel));
    throw new Stop('bookkeeping', `the bookkeeping commit failed; the file was restored and unstaged (the merge stays): ${errText(e)}`);
  }
}

function push(root) {
  const before = gitOk(root, 'rev-parse', '--verify', '-q', 'origin/main') ? git(root, 'rev-parse', '--short', 'origin/main') : 'new';
  try {
    git(root, 'push', 'origin', 'main');
  } catch (e) {
    throw new Stop('push', `git push origin main was rejected: ${errText(e)} (never forced; fetch, look at origin/main, then re-run).`);
  }
  return `pushed origin/main ${before}..${git(root, 'rev-parse', '--short', 'main')}`;
}

/**
 * The worktree folder, when it is still on disk although git has removed or
 * never lists the worktree: removal unregistered it but something (a session,
 * an editor) held the folder open. Looked up by the path spawn creates, so it
 * is found whether or not the branch still exists. Call it only after a
 * registered worktree has been removed (a failed removal returns earlier).
 */
function leftoverFolder(root, id, loc) {
  const path = worktreePathFor(root, id, loc.metadata.slug);
  return existsSync(path) ? path : null;
}

const folderLeft = (path, id) => `${path} is still on disk (something held it open); delete it by hand, then run: npm run ship -- ${id} --cleanup`;

/** Step 7. Returns report text and what, if anything, is left for the owner. */
function cleanup(root, id, loc) {
  const parts = [];
  const wt = loc.branchExists ? worktreeOf(root, loc.branch) : undefined;
  if (wt) {
    const r = spawnSync(process.execPath, [SPAWN, String(id), '--remove'], { cwd: root, encoding: 'utf8' });
    if (r.status !== 0) {
      const why = (r.stderr || r.stdout || '').trim();
      return { text: `could not remove ${wt.path}: ${why}`, left: `exit any session or program using ${wt.path}, then run: npm run ship -- ${id} --cleanup` };
    }
    parts.push(`removed worktree ${wt.path}`);
  }
  if (loc.branchExists && gitOk(root, 'show-ref', '--verify', '--quiet', `refs/heads/${loc.branch}`)) {
    try {
      git(root, 'branch', '-d', loc.branch);
    } catch (e) {
      throw new Stop('remove', `git branch -d ${loc.branch} refused: ${errText(e)}`);
    }
    parts.push(`deleted branch ${loc.branch}`);
  }
  const folder = (wt && existsSync(wt.path) ? wt.path : null) ?? leftoverFolder(root, id, loc);
  if (folder) return { text: parts.join('; ') || 'worktree and branch already gone', left: folderLeft(folder, id) };
  return { text: parts.join('; ') || 'worktree and branch already gone', left: null };
}

// ---- the run ------------------------------------------------------------------

const log = [];
const say = (status, id, text) => log.push(`  ${status.padEnd(8)} ${id.padEnd(13)} ${text}`);

function dryRun(root, loc, steps) {
  if (loc.state.hasRemote) say('note', 'fetch', 'a dry run does not fetch: origin/main is as last fetched');
  for (const s of steps) say(s.status === 'done' || s.status === 'n/a' ? s.status : 'would', s.id, s.label);
  if (loc.state.merged) return;
  // check:intent would fail only because the live check is not recorded yet; the run records it first.
  const pending = loc.state.liveCheckRequested && !loc.state.liveCheckRecorded;
  const { result, checkIntent } = evaluatePreconditions(root, loc, !pending);
  const note = pending ? ' (review only; check:intent runs after the live check is recorded)' : ` (check:intent ${checkIntent.verdict})`;
  if (result.ok) say('ok', 'preconditions', `hold${note}`);
  else say('WOULD STOP', 'preconditions', `${result.failed}: ${result.message}`);
}

/** A hint for a refusal: main may already carry a merge of an older tip of this branch (a red verify, then more commits). */
function priorMergeHint(root, id) {
  try {
    const found = git(root, 'log', 'main', '--merges', '--format=%h', `--grep=^Merge §${id}:`).split(/\r?\n/).filter(Boolean);
    return found.length ? `\nNote: main already carries ${found[0]} "Merge §${id}: …", a merge of an earlier tip of this branch. Decide with the owner what to do with it; the script changes nothing.` : '';
  } catch {
    return '';
  }
}

/** Steps 1 to 3: live check, preconditions, merge. Throws Stop. */
function beforeMerge(root, loc, opts, wt) {
  if (loc.state.merged) return say('skipped', 'merge', 'already merged into main');
  const id = loc.metadata.id;
  // Review-only preconditions first, so a refusal happens before anything is written.
  const first = evaluatePreconditions(root, loc, false).result;
  if (!first.ok) throw new Stop('preconditions', `${first.failed}: ${first.message}${priorMergeHint(root, id)}`);
  if (opts.liveChecked !== null && !loc.state.liveCheckRecorded) {
    say('done', 'live-check', recordLiveCheck(root, loc, wt, opts, opts.trailers));
  }
  const { result, checkIntent } = evaluatePreconditions(root, loc, true);
  if (!result.ok) throw new Stop('preconditions', `${result.failed}: ${result.message}\n${checkIntent?.output ?? ''}${priorMergeHint(root, id)}`);
  say('done', 'preconditions', `hold (check:intent ${checkIntent.verdict})`);
  say('done', 'merge', `merged ${loc.branch} into main (${mergeBranch(root, loc, opts.trailers).slice(0, 7)})`);
}

/** Steps 4 to 6: verify, bookkeeping, push. */
function afterMerge(root, loc, opts) {
  if (loc.state.bookkept) {
    say('skipped', 'bookkeeping', 'already on main');
  } else {
    say('done', 'verify', runVerify(root));
    say('done', 'bookkeeping', bookkeeping(root, loc, opts.trailers));
  }
  // pushed is only ever true once the bookkeeping is on main, so a run that just booked always pushes
  if (!loc.state.hasRemote) say('skipped', 'push', 'no remote named origin: nothing pushed');
  else if (loc.state.pushed) say('skipped', 'push', 'origin/main is already at main');
  else say('done', 'push', push(root));
}

function execute(root, id, loc, opts, wt) {
  if (!opts.cleanup) {
    beforeMerge(root, loc, opts, wt);
    afterMerge(root, loc, opts);
  }
  const c = cleanup(root, id, loc);
  say(c.left ? 'LEFT' : 'done', 'remove', c.text);
  return c.left;
}

function main() {
  let opts;
  try {
    opts = parseShipArgs(process.argv.slice(2));
  } catch (e) {
    console.error(`ship: ${e.message}`);
    process.exit(1);
  }
  if (!opts.id) {
    console.error('usage: npm run ship -- <id> [--live-checked "<owner\'s words>"] [--dry-run] [--cleanup] [--trailer "<line>"]...');
    process.exit(1);
  }
  const root = mainCheckout(process.cwd());
  let step = 'start';
  let left = null;
  try {
    const loc = locate(root, opts.id);
    checkStart(root, loc, opts.dryRun);
    const { wt, state } = readState(root, opts.id, loc, opts);
    loc.state = state;
    if (opts.dryRun) {
      dryRun(root, loc, planSteps(state));
    } else {
      step = 'run';
      left = execute(root, opts.id, loc, opts, wt);
    }
    finish(root, opts, 'shipped', opts.dryRun ? 'dry run' : left ?? 'complete', left);
  } catch (e) {
    const stop = e instanceof Stop ? e : new Stop(step, errText(e));
    say('STOPPED', stop.step, stop.message);
    finish(root, opts, 'ship-stopped', `${stop.step}: ${stop.message.split('\n')[0]}`, null, true);
  }
}

function finish(root, opts, event, detail, left, failed = false) {
  const title = opts.dryRun ? `§${opts.id} dry run (nothing changed)` : `§${opts.id} ${failed ? 'ship stopped' : 'ship report'}`;
  console.log([title, ...log].join('\n'));
  if (left) console.log(`\nLeft for you: ${left}`);
  if (!opts.dryRun) {
    try {
      appendEvent(root, { event, id: String(opts.id), detail: detail.slice(0, 200) });
    } catch {
      // the log is a convenience; a missing one must not hide the report
    }
  }
  process.exit(failed ? 1 : 0);
}

main();
