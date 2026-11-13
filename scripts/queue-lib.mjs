// Pure logic behind `npm run queue`: the intent queue, generated from
// each intent's metadata.yml instead of hand-kept in a file. Kept free
// of git/fs calls so it can be unit-tested; see queue-lib.test.mjs. The git
// half is queue.mjs.
import { findCycles, isMerged, openChain, parseBlockers } from './blockers-lib.mjs';
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

/**
 * What `blocked_by` says across the queue. An entry's blockers read from its
 * picked metadata; "merged" reads from main only (`entry.mainMerged`, else the
 * metadata when it came from main). `knownIds` adds intents that exist only on
 * a branch. Returns `{ byId, problems }`: per intent id the open `direct` and
 * `further` ids and the raw `items`, and the problem lines (cycles, broken
 * records, ids that exist nowhere).
 */
export function blockerReport(entries, knownIds = []) {
  const known = new Set([...entries.map((e) => String(Number(e.id))), ...knownIds.map((i) => String(Number(i)))]);
  const merged = new Set(
    entries.filter((e) => e.mainMerged ?? (e.source === 'main' && isMerged(e.metadata))).map((e) => String(Number(e.id))),
  );
  const isOpen = (id) => known.has(id) && !merged.has(id);
  const graph = {};
  const items = {};
  const problems = [];
  for (const e of [...entries].sort((a, b) => Number(a.id) - Number(b.id))) {
    const id = String(Number(e.id));
    const parsed = parseBlockers(e.metadata, id);
    for (const p of parsed.problems) problems.push(`§${id}: ${p}`);
    for (const it of parsed.items) {
      if (!known.has(it.id)) problems.push(`§${id}: blocked_by names §${it.id}, which is on no branch.`);
    }
    items[id] = parsed.items;
    graph[id] = parsed.items.map((it) => it.id).filter((b) => known.has(b));
  }
  for (const cycle of findCycles(graph)) {
    problems.push(`blocked_by cycle: ${[...cycle, cycle[0]].map((i) => `§${i}`).join(' -> ')}.`);
  }
  const byId = {};
  for (const id of Object.keys(graph)) {
    const { direct, further } = openChain(id, graph, isOpen);
    byId[id] = { direct, further, items: items[id] };
  }
  return { byId, problems };
}

/** `blocked by §14 (§13)`, or '' when nothing open blocks the intent. */
export function blockedText(info) {
  if (!info || !info.direct.length) return '';
  const tail = info.further.length ? ` (${info.further.map((i) => `§${i}`).join(', ')})` : '';
  return `blocked by ${info.direct.map((i) => `§${i}`).join(', ')}${tail}`;
}

/** One line: `§47  title  [feature] in-review  I·S·P  branch` plus `  d2d841a` for a shipped intent. */
export function queueLine(entry, blocked = '') {
  const m = entry.metadata;
  const parts = [`§${entry.id}`, m.title || m.slug || '', `[${m.type ?? '?'}] ${m.status ?? '?'}`];
  const gates = gateSummary(m);
  if (gates) parts.push(gates);
  const auto = autoSummary(m);
  if (auto) parts.push(auto);
  if (blocked) parts.push(blocked);
  parts.push(entry.source);
  if (m.status === 'done' && m.merged) parts.push(m.merged);
  return parts.join('  ');
}

/** The whole report: a heading per non-empty group (the first four always), one line per intent. */
export function formatQueue(entries, { knownIds = [] } = {}) {
  const groups = groupIntents(entries);
  const report = blockerReport(entries, knownIds);
  const line = (e) => queueLine(e, blockedText(report.byId[String(Number(e.id))]));
  const blocks = [];
  GROUPS.forEach(([key, heading], i) => {
    if (i >= 4 && !groups[key].length) return;
    const lines = groups[key].length ? groups[key].map(line) : ['(none)'];
    blocks.push([`${heading} (${groups[key].length})`, ...lines.map((l) => `  ${l}`)].join('\n'));
  });
  if (report.problems.length) blocks.push(['Problems', ...report.problems.map((p) => `  ${p}`)].join('\n'));
  return `${blocks.join('\n\n')}\n`;
}

/** The same data for `--json`: each group's entries with the line's fields spelled out. */
export function queueData(entries, { knownIds = [] } = {}) {
  const groups = groupIntents(entries);
  const report = blockerReport(entries, knownIds);
  const flat = (e) => {
    const info = report.byId[String(Number(e.id))];
    return {
    id: Number(e.id),
    slug: e.metadata.slug ?? null,
    title: e.metadata.title ?? null,
    type: e.metadata.type ?? null,
    status: e.metadata.status ?? null,
    gates: gateSummary(e.metadata),
    auto: autoSummary(e.metadata),
    source: e.source,
    merged: e.metadata.status === 'done' ? e.metadata.merged || null : null,
    blocked_by: (info?.items ?? []).map((it) => ({ id: Number(it.id), reason: it.reason })),
    blocked_by_open: info ? [...info.direct, ...info.further].map(Number) : [],
    };
  };
  const out = Object.fromEntries(Object.entries(groups).map(([k, v]) => [k, v.map(flat)]));
  out.problems = report.problems;
  return out;
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
