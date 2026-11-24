#!/usr/bin/env node
// `npm run queue [-- --json | --next-id [--no-fetch]]`
//
// The intent queue, generated on demand from each intent's
// metadata.yml and git; nothing is written to disk and nobody edits a queue
// by hand. Lists every intent in intents/ on `main`, taking status and gates
// from the intent's branch while that branch exists and is not merged (an
// implementer sets `in-review` there), else from main. `--next-id` prints the
// id `/intent` should take next: one more than the highest §N in
// OVERVIEW.md (main's copy and the working copy), the intents/ of main and of
// every local branch, the intents/ folders on disk here (a draft /intent
// has not committed yet) and, from `origin`, the intents/ folders of every
// branch and each reservation branch `intent/<n>` (see reserve-id.mjs).
// `--next-id` first fetches origin, bounded at 10 s (`--no-fetch` skips it);
// no origin or a failed fetch is a warning on stderr, never an error, and a
// number with a different folder here and on origin is a clash line on
// stderr. The listing and `--json` never fetch. The listing shows committed intents only (those on
// main). `--json` prints the groups as data. The pure half is queue-lib.mjs.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { isMerged } from './blockers-lib.mjs';
import { parseMetadata } from './intent-check-lib.mjs';
import { clashLine, findClashes, formatQueue, idOfDir, nextId, pickSource, queueData, reservationIds } from './queue-lib.mjs';
import { fetchOrigin, hasOrigin } from './remote-io.mjs';
import { git, readIntentMetadataFromBranch } from './session-io.mjs';

const args = process.argv.slice(2);
const root = git(process.cwd(), 'rev-parse', '--show-toplevel');
const MAIN = 'main';

/** `git`, or null when it fails (a missing path in a tree, say). */
function tryGit(...a) {
  try {
    return git(root, ...a);
  } catch {
    return null;
  }
}

/** Intent folder names (`47-slug`) in `ref`'s intents/ directory. */
function intentDirs(ref) {
  const out = tryGit('ls-tree', '--name-only', `${ref}:intents`);
  return (out ?? '').split(/\r?\n/).filter((d) => /^\d+-/.test(d));
}

/** Text of `path` as `main` has it plus the working copy here, so a branch's own edit counts. */
function textOf(path) {
  const onMain = tryGit('show', `${MAIN}:${path}`) ?? '';
  const file = join(root, path);
  return `${onMain}\n${existsSync(file) ? readFileSync(file, 'utf8') : ''}`;
}

/** Position of the merge commit `hash` on main's first-parent history, 0 = newest; null if not found. */
function mergeRankFinder() {
  const log = (tryGit('log', '--first-parent', '--format=%H', MAIN) ?? '').split(/\r?\n/).filter(Boolean);
  return (hash) => {
    if (!hash || hash.length < 7) return null;
    const i = log.findIndex((h) => h.startsWith(hash));
    return i < 0 ? null : i;
  };
}

function collectEntries() {
  const rankOf = mergeRankFinder();
  const entries = [];
  for (const dir of intentDirs(MAIN)) {
    const id = dir.slice(0, dir.indexOf('-'));
    const text = tryGit('show', `${MAIN}:intents/${dir}/metadata.yml`);
    const mainMeta = text === null ? null : parseMetadata(text);
    let found = null;
    let conflict = false;
    try {
      found = readIntentMetadataFromBranch(root, id);
    } catch {
      conflict = true; // two local branches carry this id: say so, and show what main holds
    }
    const merged = found ? tryGit('merge-base', '--is-ancestor', found.branch, MAIN) !== null : false;
    const picked = pickSource(mainMeta, found?.metadata ?? null, merged);
    if (!picked) continue;
    if (conflict) picked.source = 'branch conflict';
    entries.push({ id, ...picked, mainMerged: isMerged(mainMeta), mergeRank: picked.metadata.status === 'done' ? rankOf(picked.metadata.merged) : null });
  }
  return entries;
}

/** Folder names (`47-slug`) of main, every local branch and the disk here. */
function localIntentDirs() {
  const refs = (tryGit('for-each-ref', '--format=%(refname:short)', 'refs/heads') ?? '').split(/\r?\n/).filter(Boolean);
  const dirs = new Set();
  for (const ref of new Set([MAIN, ...refs])) {
    for (const dir of intentDirs(ref)) dirs.add(dir);
  }
  const onDisk = join(root, 'intents');
  if (existsSync(onDisk)) {
    for (const dir of readdirSync(onDisk)) if (/^[0-9]+-/.test(dir)) dirs.add(dir);
  }
  return [...dirs];
}

function allIntentIds() {
  return [...new Set(localIntentDirs().map((d) => idOfDir(d)))];
}

/** Every ref under refs/remotes/origin/ (full names; the origin/HEAD symref skipped). */
function originRefs() {
  const out = tryGit('for-each-ref', '--format=%(refname) %(symref)', 'refs/remotes/origin') ?? '';
  return out
    .split(/\r?\n/)
    .map((l) => l.trim().split(' '))
    .filter((parts) => parts[0] && parts.length === 1)
    .map((parts) => parts[0]);
}

/** The ids and clashes `origin` adds (as fetched, or as last fetched); warnings go to stderr first. */
async function originView() {
  if (!hasOrigin(root)) {
    console.error('no remote named origin: counted local intents only');
    return { ids: [], clashes: [] };
  }
  if (!args.includes('--no-fetch')) {
    const f = await fetchOrigin(root);
    if (!f.ok) console.error(`could not fetch origin (${f.reason}): counted origin as last fetched`);
  }
  const refs = originRefs();
  const remote = [];
  for (const ref of refs) {
    const shown = ref.replace(/^refs\/remotes\//, '');
    for (const dir of intentDirs(ref)) remote.push({ ref: shown, dir });
  }
  const ids = [...reservationIds(refs), ...remote.map((r) => idOfDir(r.dir))];
  return { ids, clashes: findClashes({ local: localIntentDirs(), remote }) };
}

if (args.includes('--next-id')) {
  const origin = await originView();
  for (const c of origin.clashes) console.error(clashLine(c));
  console.log(nextId({ overviewText: textOf('OVERVIEW.md'), ids: [...allIntentIds(), ...origin.ids] }));
} else if (args.includes('--json')) {
  console.log(JSON.stringify(queueData(collectEntries(), { knownIds: allIntentIds() }), null, 2));
} else {
  process.stdout.write(formatQueue(collectEntries(), { knownIds: allIntentIds() }));
}
