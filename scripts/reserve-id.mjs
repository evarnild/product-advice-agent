#!/usr/bin/env node
// `npm run reserve-id -- <id>`
//
// Claims intent <id>'s number on `origin`: pushes ONE parentless commit that
// holds only the draft's intent.md and metadata.yml to a new branch
// `intent/<id>`. It builds the commit with plumbing (no checkout, no change to
// any local branch, the index or the working tree), so nothing of local `main`
// can travel with it. It never forces and never touches origin's main. The
// ref name is the id alone, so a second machine reserving the same number is
// refused by git as a non-fast-forward. Nothing in the kit deletes a
// reservation. Run it from the main checkout or a worktree.
//
// Exit 0 reserved (or already), 1 refused (no such draft, the number is taken,
// the commit would carry too much), 2 no remote named origin, 3 origin
// unreachable, timed out or rejected the push. The pure half is reserve-id-lib.mjs.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseMetadata } from './intent-check-lib.mjs';
import { EXIT, RESERVE_FILES, checkCarried, decide, parseReserveArgs, pushArgs, reservationSubject } from './reserve-id-lib.mjs';
import { fetchOrigin, failureReason, hasOrigin, runGitBounded } from './remote-io.mjs';
import { findIntentDir, git } from './session-io.mjs';

const say = (code, text) => {
  (code === EXIT.OK ? console.log : console.error)(text);
  process.exit(code);
};

/** git with input on stdin; throws on failure. */
const gitIn = (cwd, input, ...args) => execFileSync('git', args, { cwd, input, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();

/** Folder names in `ref`'s intents/, or null when the ref (or its intents/) does not exist. */
function foldersOn(root, ref) {
  try {
    git(root, 'rev-parse', '--verify', '--quiet', `${ref}^{commit}`);
  } catch {
    return null;
  }
  try {
    return git(root, 'ls-tree', '--name-only', `${ref}:intents`).split(/\r?\n/).filter(Boolean);
  } catch {
    return [];
  }
}

const parsed = parseReserveArgs(process.argv.slice(2));
if (parsed.error) say(EXIT.REFUSED, parsed.error);
const { id } = parsed;

const root = git(process.cwd(), 'rev-parse', '--show-toplevel');

// B3.1: the draft on disk, and its metadata names this id
const dir = findIntentDir(root, id); // intents/<id>-<slug>
if (!dir) say(EXIT.REFUSED, `no folder intents/${id}-* here: nothing was reserved`);
const metaPath = join(root, dir, 'metadata.yml');
if (!existsSync(metaPath)) say(EXIT.REFUSED, `${dir}/metadata.yml is missing: nothing was reserved`);
const metaId = parseMetadata(readFileSync(metaPath, 'utf8')).id;
if (String(metaId) !== id) say(EXIT.REFUSED, `${dir}/metadata.yml says id ${metaId ?? '(none)'}, not ${id}: nothing was reserved`);
const folder = dir.slice('intents/'.length);

// B3.2, B3.3: origin, fetched
if (!hasOrigin(root)) say(EXIT.NO_REMOTE, 'no remote named origin: nothing was reserved');
const fetched = await fetchOrigin(root);
if (!fetched.ok) say(EXIT.REMOTE_FAILED, `could not fetch origin (${fetched.reason}): nothing was reserved`);

// B3.4 to B3.6
const decision = decide({
  id,
  dir: folder,
  originMainDirs: foldersOn(root, 'refs/remotes/origin/main') ?? [],
  reservationDirs: foldersOn(root, `refs/remotes/origin/intent/${id}`),
});
if (decision.exit !== null) say(decision.exit, decision.message);

// B2: the commit, from plumbing only. `--path` makes git apply the same attributes as `git add`.
const entries = [];
for (const file of RESERVE_FILES) {
  const path = join(root, dir, file);
  if (!existsSync(path)) continue;
  const blob = git(root, 'hash-object', '-w', `--path=${dir}/${file}`, path);
  entries.push(`100644 blob ${blob}\t${file}`);
}
const mktree = (lines) => gitIn(root, `${lines.join('\n')}\n`, 'mktree');
const folderTree = mktree(entries);
const intentsTree = mktree([`040000 tree ${folderTree}\t${folder}`]);
const rootTree = mktree([`040000 tree ${intentsTree}\tintents`]);
const commit = gitIn(root, '', 'commit-tree', rootTree, '-m', reservationSubject(id, dir));

// B3.7: it carries nothing else
const parents = git(root, 'rev-list', '--parents', '-n', '1', commit).split(' ').slice(1);
const paths = git(root, 'ls-tree', '-r', '--name-only', commit).split(/\r?\n/).filter(Boolean);
const problem = checkCarried({ parents, paths, dir });
if (problem) say(EXIT.REFUSED, `${problem}: nothing was reserved`);

// B3.8: the one push
const pushed = await runGitBounded(root, pushArgs(commit, id));
if (pushed.code !== 0 || pushed.timedOut) {
  const why = pushed.timedOut ? failureReason(pushed) : (pushed.stderr || pushed.stdout).trim() || failureReason(pushed);
  say(EXIT.REMOTE_FAILED, `could not reserve §${id} on origin: ${why}`);
}
git(root, 'update-ref', `refs/remotes/origin/intent/${id}`, commit);
say(EXIT.OK, `reserved §${id} on origin as intent/${id} (${commit.slice(0, 7)})`);
