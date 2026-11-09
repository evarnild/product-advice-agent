// Pure logic behind `npm run queue`: the intent queue, generated from
// each intent's metadata.yml instead of hand-kept in a file. Kept free
// of git/fs calls so it can be unit-tested; see queue-lib.test.mjs. The git
// half is queue.mjs.
import { autoSummary, gateSummary } from './session-lib.mjs';

/** Status → the group it is listed under. Anything else lands in `other`. */
export const GROUP_OF_STATUS = {
  accepted: 'inFlight',
  'in-progress': 'inFlight',
  'in-review': 'inFlight',
  draft: 'queued',
  done: 'shipped',
  abandoned: 'stopped',
  deferred: 'stopped',
};

/** Group keys in print order, with their headings. */
export const GROUPS = [
  ['inFlight', 'In flight'],
  ['queued', 'Queued'],
  ['shipped', 'Shipped'],
  ['stopped', 'Stopped'],
  ['other', 'Unrecognised status'],
];

/** Statuses that end an intent's life: once `main` says one of them, no branch can reopen it. */
export const TERMINAL_STATUSES = ['done', 'abandoned', 'deferred'];

/**
 * Which metadata.yml speaks for an intent. An implementer sets `in-review`
 * on the intent's branch, not on `main`, so while that branch exists and is
 * not merged, the branch wins; a merged branch not yet deleted must not, or a
 * shipped intent would read as in-review. Main wins when it holds a terminal
 * status: the branch is then ignored, so a branch kept unmerged on purpose
 * (a probe, say) does not show a finished intent as in flight.
 * Returns `{ metadata, source }`, or null when neither side has one.
 */
export function pickSource(mainMeta, branchMeta, branchMerged) {
  if (mainMeta && TERMINAL_STATUSES.includes(mainMeta.status)) return { metadata: mainMeta, source: 'main' };
  if (branchMeta && !branchMerged) return { metadata: branchMeta, source: 'branch' };
  if (mainMeta) return { metadata: mainMeta, source: 'main' };
  return null;
}

/**
 * Entries are `{ id, metadata, source, mergeRank }`; mergeRank is the
 * position of the merge on main's first-parent history, 0 = newest, or null
 * when unknown. Returns `{ inFlight, queued, shipped, stopped, other }`;
 * shipped are newest merge first, unknown ranks after them, then by id.
 */
export function groupIntents(entries) {
  const out = { inFlight: [], queued: [], shipped: [], stopped: [], other: [] };
  for (const e of entries) out[GROUP_OF_STATUS[e.metadata.status] ?? 'other'].push(e);
  const rank = (e) => (e.mergeRank ?? Infinity);
  out.shipped.sort((a, b) => (rank(a) === rank(b) ? 0 : rank(a) < rank(b) ? -1 : 1) || Number(b.id) - Number(a.id));
  for (const key of ['inFlight', 'queued', 'stopped', 'other']) out[key].sort((a, b) => Number(a.id) - Number(b.id));
  return out;
}

/** One line: `§47  title  [feature] in-review  I·S·P  branch` plus `  d2d841a` for a shipped intent. */
export function queueLine(entry) {
  const m = entry.metadata;
  const parts = [`§${entry.id}`, m.title || m.slug || '', `[${m.type ?? '?'}] ${m.status ?? '?'}`];
  const gates = gateSummary(m);
  if (gates) parts.push(gates);
  const auto = autoSummary(m);
  if (auto) parts.push(auto);
  parts.push(entry.source);
  if (m.status === 'done' && m.merged) parts.push(m.merged);
  return parts.join('  ');
}

/** The whole report: a heading per non-empty group (the first four always), one line per intent. */
export function formatQueue(entries) {
  const groups = groupIntents(entries);
  const blocks = [];
  GROUPS.forEach(([key, heading], i) => {
    if (i >= 4 && !groups[key].length) return;
    const lines = groups[key].length ? groups[key].map(queueLine) : ['(none)'];
    blocks.push([`${heading} (${groups[key].length})`, ...lines.map((l) => `  ${l}`)].join('\n'));
  });
  return `${blocks.join('\n\n')}\n`;
}

/** The same data for `--json`: each group's entries with the line's fields spelled out. */
export function queueData(entries) {
  const groups = groupIntents(entries);
  const flat = (e) => ({
    id: Number(e.id),
    slug: e.metadata.slug ?? null,
    title: e.metadata.title ?? null,
    type: e.metadata.type ?? null,
    status: e.metadata.status ?? null,
    gates: gateSummary(e.metadata),
    auto: autoSummary(e.metadata),
    source: e.source,
    merged: e.metadata.status === 'done' ? e.metadata.merged || null : null,
  });
  return Object.fromEntries(Object.entries(groups).map(([k, v]) => [k, v.map(flat)]));
}

/**
 * One more than the highest `§N` in `overviewText` (OVERVIEW.md, the owner's
 * snapshot, which may name an intent before its folder exists) and the
 * highest id in `ids` (the intent folders on main, on every local branch and
 * on disk). `§6.13` counts as 6.
 */
export function nextId({ overviewText = '', ids = [] } = {}) {
  let max = 0;
  for (const m of overviewText.matchAll(/§(\d+)/g)) max = Math.max(max, Number(m[1]));
  for (const id of ids) max = Math.max(max, Number(id));
  return max + 1;
}
