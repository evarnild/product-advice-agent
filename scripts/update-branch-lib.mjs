// Pure decisions behind `npm run update-branch -- <id>`: which worktree is the
// target, whether it may be touched, whether it is behind, what a merge's
// facts mean and what the report says. No git, no files, no processes (a test
// reads this file and fails on an import of either); update-branch.mjs is the
// I/O half.
import { parseBranch } from './intent-check-lib.mjs';
import { pathKey } from './session-lib.mjs';

/** 0 up to date or merged and green; 1 refused or unexpected; 2 conflict (aborted); 3 merged but verify is red. */
export const EXIT = { OK: 0, REFUSED: 1, CONFLICT: 2, RED: 3 };

export const USAGE = 'usage: npm run update-branch -- <id>';

/** Exactly one all-digits id, else a usage error. */
export function parseUpdateArgs(argv) {
  if (argv.length === 1 && /^\d+$/.test(argv[0])) return { ok: true, id: argv[0] };
  return { ok: false, error: USAGE };
}

const folderName = (p) => p.replace(/\\/g, '/').replace(/\/+$/, '').split('/').pop();

/**
 * The worktree whose checked-out branch carries intent `id`. With no branch
 * match, a detached worktree whose folder is `<id>-...` (the name spawn gives)
 * is reported as detached rather than as missing.
 */
export function findTarget(worktrees, id) {
  const byBranch = worktrees.filter((w) => w.branch && parseBranch(w.branch)?.id === id);
  if (byBranch.length > 1) {
    return { ok: false, reason: `§${id} is on more than one worktree: ${byBranch.map((w) => `${w.path} (${w.branch})`).join(', ')}` };
  }
  if (byBranch.length === 1) return { ok: true, worktree: byBranch[0] };
  const detached = worktrees.filter((w) => !w.branch && folderName(w.path).startsWith(`${id}-`));
  if (detached.length) return { ok: false, reason: `HEAD is detached in ${detached[0].path}`, detachedPath: detached[0].path };
  return { ok: false, reason: `no worktree has §${id}'s branch checked out` };
}

/**
 * May the target be touched? First fault wins: an operation in progress, the
 * main checkout, branch `main`, a detached HEAD, tracked changes.
 * `inProgress` names the operations (`merge`, `rebase`, `cherry-pick`);
 * `dirty` is `git status --porcelain --untracked-files=no` split into lines.
 */
export function preflight({ path, branch, mainPath, inProgress = [], dirty = [] }) {
  if (inProgress.length) return { ok: false, reason: `a ${inProgress.join(' and a ')} is in progress in ${path}` };
  if (pathKey(path) === pathKey(mainPath)) return { ok: false, reason: `${path} is the main checkout` };
  if (branch === 'main') return { ok: false, reason: `the branch in ${path} is main` };
  if (!branch) return { ok: false, reason: `HEAD is detached in ${path}` };
  if (dirty.length) return { ok: false, reason: `tracked files are modified or staged in ${path}:\n${dirty.join('\n')}` };
  return { ok: true };
}

/** Behind means at least one commit on main that the branch lacks. */
export function planUpdate(behindCount) {
  return behindCount > 0 ? 'merge' : 'up-to-date';
}

/** What a `git merge` meant, from facts only (never git's message). */
export function classifyMerge({ status, mergeHead, headBefore, headAfter, unmerged = [] }) {
  if (status === 0) return 'merged';
  if (mergeHead && unmerged.length > 0) return 'conflict';
  if (!mergeHead && headBefore === headAfter) return 'refused';
  return 'unexpected';
}

/** After `git merge --abort`: what, if anything, is not back as it was. */
export function classifyAbort({ headBefore, headAfter, mergeHead, dirty = [] }) {
  const left = [];
  if (headBefore !== headAfter) left.push(`HEAD moved from ${headBefore.slice(0, 7)} to ${headAfter.slice(0, 7)}`);
  if (mergeHead) left.push('MERGE_HEAD is still present');
  if (dirty.length) left.push(`tracked changes remain: ${dirty.join(', ')}`);
  return { clean: left.length === 0, left };
}

/** The last `n` lines of command output. */
export function outputTail(text, n = 25) {
  return String(text ?? '')
    .trim()
    .split(/\r?\n/)
    .slice(-n)
    .join('\n');
}

/**
 * The report and exit status for an outcome:
 * `up-to-date`, `merged` (with `verify: {ok, tail}`), `conflict`, `abort-left`, `refused`.
 */
export function formatReport(o) {
  switch (o.kind) {
    case 'up-to-date':
      return { exit: EXIT.OK, lines: [`branch contains main at ${o.mainShort}`] };
    case 'merged': {
      const lines = [`behind main by ${o.behind}; merged main (now ${o.headShort}, main ${o.mainShort})`];
      if (o.verify.ok) return { exit: EXIT.OK, lines: [...lines, 'verify green'] };
      return { exit: EXIT.RED, lines: [...lines, o.verify.tail, 'verify red after merging main (the merge is kept)'] };
    }
    case 'conflict':
      return {
        exit: EXIT.CONFLICT,
        lines: [`behind main by ${o.behind}; merging main conflicts, merge aborted, branch unchanged`, 'conflicted files:', ...o.files.map((f) => `  ${f}`)],
      };
    case 'abort-left':
      return { exit: EXIT.REFUSED, lines: ['merging main conflicts and the abort left something behind; nothing more was changed:', ...o.left.map((l) => `  ${l}`)] };
    case 'refused':
      return { exit: EXIT.REFUSED, lines: [`refused: ${o.reason}`, ...(o.gitMessage ? [o.gitMessage] : [])] };
    default:
      throw new Error(`unknown outcome ${o.kind}`);
  }
}
