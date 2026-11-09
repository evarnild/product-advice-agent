#!/usr/bin/env node
// `npm run sessions [-- --log [N]]`
//
// The coordinator's view of parallel work: every worktree with its
// intent status and gates (read live from that worktree's metadata.yml),
// commits ahead/behind main, uncommitted files, and what its Claude Code
// session last did (from the hook-written event log). Sessions waiting on
// the owner sort first. `--log` tails the event log instead; `--json` prints
// the rows as data.
import { existsSync, readFileSync } from 'node:fs';
import { eventLogPath, git, mainCheckout, readIntentMetadata } from './session-io.mjs';
import {
  formatEvent,
  formatStatusTable,
  latestEventByWorktree,
  metadataColumns,
  parseEvents,
  parseWorktreeList,
  pathKey,
  portFor,
  sessionState,
  sessionsData,
} from './session-lib.mjs';
import { parseBranch } from './intent-check-lib.mjs';

const args = process.argv.slice(2);
const root = mainCheckout(process.cwd());
const logFile = eventLogPath(root);
const events = existsSync(logFile) ? parseEvents(readFileSync(logFile, 'utf8')) : [];

function aheadBehind(branch) {
  if (!branch || branch === 'main') return { ahead: null, behind: null };
  const [behind, ahead] = git(root, 'rev-list', '--left-right', '--count', `main...${branch}`).split(/\s+/).map(Number);
  return { ahead, behind };
}

function dirtyCount(path) {
  try {
    return git(path, 'status', '--porcelain').split('\n').filter(Boolean).length;
  } catch {
    return null; // prunable: the directory is gone
  }
}

function rowFor(wt, latest) {
  const parsed = wt.branch ? parseBranch(wt.branch) : null;
  const intent = parsed && existsSync(wt.path) ? readIntentMetadata(wt.path, parsed.id) : null;
  return {
    id: parsed?.id ?? null,
    branch: wt.branch,
    path: wt.path,
    ...metadataColumns(intent?.metadata),
    ...aheadBehind(wt.branch),
    dirty: dirtyCount(wt.path),
    port: parsed ? portFor(parsed.id) : null,
    session: sessionState(latest.get(pathKey(wt.path))),
  };
}

function printTable(rows) {
  console.log(formatStatusTable(rows, Date.now()));
  const behind = rows.filter((r) => r.id && r.behind > 0 && r.session.state !== 'closed');
  if (behind.length) {
    console.log(`
Behind main (rebase before review): ${behind.map((r) => `§${r.id} (-${r.behind})`).join(', ')}`);
  }
  const ready = rows.filter((r) => r.status === 'in-review');
  if (ready.length) console.log(`Ready for /review: ${ready.map((r) => `§${r.id} ${r.branch}`).join(', ')}`);
  console.log(`
Event log: ${logFile}`);
}

if (args.includes('--log')) {
  const n = Number(args[args.indexOf('--log') + 1]) || 20;
  console.log(events.slice(-n).map(formatEvent).join('\n') || '(no events yet)');
} else {
  const latest = latestEventByWorktree(events);
  const rows = parseWorktreeList(git(root, 'worktree', 'list', '--porcelain')).map((wt) => rowFor(wt, latest));
  if (args.includes('--json')) {
    console.log(JSON.stringify(sessionsData(rows, Date.now()), null, 2));
  } else {
    printTable(rows);
  }
}
