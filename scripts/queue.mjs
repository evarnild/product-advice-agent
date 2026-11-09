#!/usr/bin/env node
// `npm run queue [-- --json | --next-id]`
//
// The intent queue, generated on demand from each intent's
// metadata.yml and git; nothing is written to disk and nobody edits a queue
// by hand. Lists every intent in intents/ on `main`, taking status and gates
// from the intent's branch while that branch exists and is not merged (an
// implementer sets `in-review` there), else from main. `--next-id` prints the
// id `/intent` should take next: one more than the highest §N in
// OVERVIEW.md (main's copy and the working copy), the intents/ of main and of
// every local branch, and the intents/ folders on disk here (a draft /intent
// has not committed yet). The listing shows committed intents only (those on
// main). `--json` prints the groups as data. The pure half is queue-lib.mjs.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseMetadata } from './intent-check-lib.mjs';
import { formatQueue, nextId, pickSource, queueData } from './queue-lib.mjs';
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
    entries.push({ id, ...picked, mergeRank: picked.metadata.status === 'done' ? rankOf(picked.metadata.merged) : null });
  }
  return entries;
}

function allIntentIds() {
  const refs = (tryGit('for-each-ref', '--format=%(refname:short)', 'refs/heads') ?? '').split(/\r?\n/).filter(Boolean);
  const ids = new Set();
  for (const ref of new Set([MAIN, ...refs])) {
    for (const dir of intentDirs(ref)) ids.add(dir.slice(0, dir.indexOf('-')));
  }
  const onDisk = join(root, 'intents');
  if (existsSync(onDisk)) {
    for (const dir of readdirSync(onDisk)) if (/^[0-9]+-/.test(dir)) ids.add(dir.slice(0, dir.indexOf('-')));
  }
  return [...ids];
}

if (args.includes('--next-id')) {
  console.log(nextId({ overviewText: textOf('OVERVIEW.md'), ids: allIntentIds() }));
} else if (args.includes('--json')) {
  console.log(JSON.stringify(queueData(collectEntries()), null, 2));
} else {
  process.stdout.write(formatQueue(collectEntries()));
}
