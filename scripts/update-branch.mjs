#!/usr/bin/env node
// `npm run update-branch -- <id>`
//
// Brings intent §id's branch up to date with local `main` before a review
// round: in the branch's own worktree, `git merge --no-edit main` when the
// branch is behind, then `npm run verify` there. Never a rebase, so no commit
// is rewritten and an earlier round's `reviewed-commit` stays valid. Exit 0
// up to date, or merged and green; 1 refused (nothing changed); 2 conflict
// (the merge is aborted, the worktree as before); 3 merged but verify is red
// (the merge is kept). The decisions live in update-branch-lib.mjs; this file
// is the git half. It can be run from any checkout; the coordinator runs it
// from the main checkout.
//
// It never fetches, pushes, resets, stashes, rebases, writes a file, appends
// to the session log, or touches `main` or another worktree.
//
// SDLC_UPDATE_BRANCH_VERIFY, when set, is a command line that runs in place
// of `npm run verify` (update-branch.test.mjs sets it in a throwaway repository).
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { isAbsolute, join } from 'node:path';
import { git } from './session-io.mjs';
import { parseWorktreeList } from './session-lib.mjs';
import {
  classifyAbort,
  classifyMerge,
  findTarget,
  formatReport,
  outputTail,
  parseUpdateArgs,
  planUpdate,
  preflight,
} from './update-branch-lib.mjs';

const short = (cwd, rev) => git(cwd, 'rev-parse', '--short', rev);

/** Runs git in `cwd`, never throwing: `{ status, stdout, stderr }`. */
function run(cwd, ...args) {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8' });
  return { status: r.status ?? 1, stdout: (r.stdout ?? '').trim(), stderr: (r.stderr ?? '').trim() };
}

const lines = (s) => s.split(/\r?\n/).filter(Boolean);

/** Is `name` (a file or dir under the worktree's git dir) there? */
function gitPathExists(wt, name) {
  const p = git(wt, 'rev-parse', '--git-path', name);
  return existsSync(isAbsolute(p) ? p : join(wt, p));
}

function inProgressOps(wt) {
  const ops = [];
  if (gitPathExists(wt, 'MERGE_HEAD')) ops.push('merge');
  if (gitPathExists(wt, 'rebase-merge') || gitPathExists(wt, 'rebase-apply')) ops.push('rebase');
  if (gitPathExists(wt, 'CHERRY_PICK_HEAD')) ops.push('cherry-pick');
  return ops;
}

const dirtyLines = (wt) => lines(git(wt, 'status', '--porcelain', '--untracked-files=no'));

function finish(outcome) {
  const { exit, lines: out } = formatReport(outcome);
  console.log(out.join('\n'));
  process.exit(exit);
}

function main() {
  const args = parseUpdateArgs(process.argv.slice(2));
  if (!args.ok) {
    console.error(args.error);
    process.exit(1);
  }
  const worktrees = parseWorktreeList(git(process.cwd(), 'worktree', 'list', '--porcelain'));
  const mainPath = worktrees[0].path;
  const found = findTarget(worktrees, args.id);
  if (!found.ok && found.detachedPath) {
    // a rebase leaves HEAD detached: name the operation when there is one
    const ops = inProgressOps(found.detachedPath);
    finish({ kind: 'refused', reason: ops.length ? preflight({ path: found.detachedPath, branch: null, mainPath, inProgress: ops }).reason : found.reason });
  }
  if (!found.ok) finish({ kind: 'refused', reason: found.reason });
  const wt = found.worktree.path;
  const check = preflight({ path: wt, branch: found.worktree.branch, mainPath, inProgress: inProgressOps(wt), dirty: dirtyLines(wt) });
  if (!check.ok) finish({ kind: 'refused', reason: check.reason });

  const mainShort = short(wt, 'main');
  const behind = Number(git(wt, 'rev-list', '--count', `${found.worktree.branch}..main`));
  if (planUpdate(behind) === 'up-to-date') finish({ kind: 'up-to-date', mainShort });

  const headBefore = git(wt, 'rev-parse', 'HEAD');
  const merge = run(wt, 'merge', '--no-edit', 'main');
  const headAfter = git(wt, 'rev-parse', 'HEAD');
  const mergeHead = gitPathExists(wt, 'MERGE_HEAD');
  const unmerged = lines(run(wt, 'diff', '--name-only', '--diff-filter=U').stdout);
  const kind = classifyMerge({ status: merge.status, mergeHead, headBefore, headAfter, unmerged });
  const gitMessage = [merge.stdout, merge.stderr].filter(Boolean).join('\n');

  if (kind === 'refused') finish({ kind: 'refused', reason: 'git refused to merge main; nothing changed', gitMessage });
  if (kind === 'conflict' || kind === 'unexpected') {
    run(wt, 'merge', '--abort');
    const after = classifyAbort({
      headBefore,
      headAfter: git(wt, 'rev-parse', 'HEAD'),
      mergeHead: gitPathExists(wt, 'MERGE_HEAD'),
      dirty: dirtyLines(wt),
    });
    if (!after.clean) finish({ kind: 'abort-left', left: after.left });
    if (kind === 'unexpected') finish({ kind: 'refused', reason: 'git merge failed unexpectedly; the merge was aborted', gitMessage });
    finish({ kind: 'conflict', behind, files: unmerged });
  }

  const command = process.env.SDLC_UPDATE_BRANCH_VERIFY || 'npm run verify';
  const v = spawnSync(command, { cwd: wt, shell: true, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  const verify = v.status === 0 ? { ok: true } : { ok: false, tail: outputTail(`${v.stdout ?? ''}${v.stderr ?? ''}`) };
  finish({ kind: 'merged', behind, headShort: short(wt, 'HEAD'), mainShort: short(wt, 'main'), verify });
}

try {
  main();
} catch (e) {
  console.error(`update-branch: ${e.stderr?.toString().trim() || e.message}`);
  process.exit(1);
}
