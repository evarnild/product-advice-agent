// Pure logic for `blocked_by:` in metadata.yml (intents/18-intent-dependencies).
// A blocker is a hard prerequisite: the intent cannot be built correctly until
// that intent is merged. Not a gate (any agent may write it). Free of git/fs
// calls; the git half lives in session-io.mjs, queue.mjs and check-intent.mjs.

/**
 * Reads `blocked_by` from parsed metadata. Each item is `<id>    <reason>`.
 * Returns `{ items: [{id, reason}], problems: string[], notes: string[] }`: a non-digit id or
 * the intent's own id is a problem (and not an item); a missing reason keeps
 * the item valid (reason is '').
 */
export function parseBlockers(metadata, selfId = null) {
  const raw = metadata?.blocked_by;
  const list = Array.isArray(raw) ? raw : [];
  const items = [];
  const problems = [];
  const notes = [];
  for (const entry of list) {
    const m = /^(\S+)(?:\s+(.*\S))?\s*$/.exec(String(entry));
    if (!m) continue;
    const [, id, reason = ''] = m;
    if (!/^\d+$/.test(id)) {
      problems.push(`blocked_by item "${entry}": "${id}" is not an intent id (digits).`);
    } else if (selfId !== null && String(Number(id)) === String(Number(selfId))) {
      problems.push(`blocked_by item "${entry}": an intent cannot block itself.`);
    } else {
      items.push({ id: String(Number(id)), reason });
      if (!reason) notes.push(`blocked_by item "${entry}": no reason given.`);
    }
  }
  return { items, problems, notes };
}

/** True when metadata carries a non-empty `merged:` (an empty value parses to `[]`, which is not merged). */
export function isMerged(meta) {
  return typeof meta?.merged === 'string' && meta.merged.trim() !== '';
}

/**
 * 'cleared' when main's metadata for `id` has a non-empty `merged:`; 'open'
 * when main has the intent without it, or only a branch has it; 'unknown' when
 * no intent has that id anywhere. `mainMetaOf(id)` returns main's parsed
 * metadata or null; `exists(id)` (optional) says whether any branch has it.
 * Only main's `merged:` counts, whatever a branch copy says.
 */
export function blockerState(id, mainMetaOf, exists = () => false) {
  const meta = mainMetaOf(id);
  if (meta) return isMerged(meta) ? 'cleared' : 'open';
  return exists(id) ? 'open' : 'unknown';
}

/**
 * `graph` maps id to its direct blocker ids; `isOpen(id)` says whether a
 * blocker is still open. Returns `{ direct, further }`: the open direct
 * blockers (ascending), then the further open ones reached through them,
 * breadth first, each id once and never the intent itself.
 */
export function openChain(id, graph, isOpen) {
  const num = (a, b) => Number(a) - Number(b);
  const direct = [...new Set(graph[id] ?? [])].filter(isOpen).sort(num);
  const seen = new Set([String(id), ...direct]);
  const further = [];
  let frontier = direct;
  while (frontier.length) {
    const next = [];
    for (const f of frontier) {
      for (const b of [...new Set(graph[f] ?? [])].sort(num)) {
        if (seen.has(b) || !isOpen(b)) continue;
        seen.add(b);
        further.push(b);
        next.push(b);
      }
    }
    frontier = next;
  }
  return { direct, further };
}

/** Each cycle in `graph` once, as ids starting at its smallest, e.g. `['15', '17']`. */
export function findCycles(graph) {
  const cycles = new Map();
  const visit = (node, path) => {
    const at = path.indexOf(node);
    if (at >= 0) {
      const cyc = path.slice(at);
      const min = cyc.reduce((a, b) => (Number(b) < Number(a) ? b : a));
      const i = cyc.indexOf(min);
      const canon = [...cyc.slice(i), ...cyc.slice(0, i)];
      cycles.set(canon.join('>'), canon);
      return;
    }
    for (const next of graph[node] ?? []) visit(next, [...path, node]);
  };
  for (const start of Object.keys(graph)) visit(start, []);
  return [...cycles.values()];
}
