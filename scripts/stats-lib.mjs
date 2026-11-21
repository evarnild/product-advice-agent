// Pure logic behind `npm run stats` (§19): phases from git milestones, token
// sums from Claude Code transcripts, owner wait from the session log and the
// gate commits. No git, no fs, no clock (the caller passes `now`): tested in
// stats-lib.test.mjs. The I/O half is scripts/stats.mjs.
//
// Nothing is guessed (B4, B7): a coordinator turn touching several intents is
// "shared", a line the parser cannot read is skipped and counted, and no
// prompt or response text is ever read into a result: only ids, times,
// model names and token counts leave this module.

export const PHASE_ORDER = ['intent', 'spec', 'plan', 'build', 'review', 'live check', 'ship'];
const UNPHASED = 'unphased';
/** One owner-wait gap counts at most this long; the rest is idle (B6). */
export const WAIT_CAP_MS = 2 * 60 * 60 * 1000;
/** The agent tag's phase, as the phase of the intent it belongs to (B2). */
const AGENT_PHASE = { implement: 'build', rework: 'review', review: 'review' };

const ZERO = () => ({ input: 0, output: 0, cacheRead: 0, cacheWrite: 0 });

// ---- commits ------------------------------------------------------------------

/** `git log --format="%H %at %s"` (author time, which a rebase keeps) text to `[{hash, ts (ms), subject}]`; unreadable lines are dropped. */
export function parseCommitLog(text) {
  const out = [];
  for (const line of String(text ?? '').split(/\r?\n/)) {
    const m = /^([0-9a-f]{7,40}) (\d+) (.*)$/.exec(line);
    if (m) out.push({ hash: m[1], ts: Number(m[2]) * 1000, subject: m[3] });
  }
  return out;
}

/** `{id, rest}` for a subject that starts `§<id>: `, else null. */
export function intentOf(subject) {
  const m = /^§(\d+):\s*(.*)$/.exec(subject ?? '');
  return m ? { id: Number(m[1]), rest: m[2] } : null;
}

/** All commits, by intent id, oldest first (duplicates by hash are dropped). Commits in the same second keep the order given, so pass them oldest first (`git log --topo-order --reverse`). */
export function commitsByIntent(commits) {
  const seen = new Set();
  const by = new Map();
  for (const c of [...commits].sort((a, b) => a.ts - b.ts)) {
    if (seen.has(c.hash)) continue;
    seen.add(c.hash);
    const i = intentOf(c.subject);
    if (!i) continue;
    if (!by.has(i.id)) by.set(i.id, []);
    by.get(i.id).push({ ...c, rest: i.rest });
  }
  return by;
}

const M = {
  intentAccepted: /^intent (?:drafted and )?accepted/i,
  specAccepted: /^spec accepted/i,
  planApproved: /^plan approved/i,
  buildEnd: /^(?:auto round \d+|in[- ]review)/i,
  reviewRound: /^review round \d+/i,
  live: /^live check recorded/i,
  merged: /^merged \(/i,
};
const first = (cs, re) => cs.find((c) => re.test(c.rest));
const last = (cs, re) => cs.findLast((c) => re.test(c.rest));

/**
 * Phase spans of one intent from its commits (B3): each phase runs from the
 * end of the previous phase that has a milestone to its own milestone, so a
 * missing milestone merges its span into the next. Times never go backwards.
 * Without a `merged` commit the last span is open: the next phase in order,
 * from the last milestone to `now`.
 *
 * @returns {{id:number, startedAt:number|null, mergedAt:number|null, phases:{name:string,start:number,end:number,open?:boolean}[]}}
 */
export function milestones(cs, id, now) {
  if (!cs.length) return { id, startedAt: null, mergedAt: null, phases: [] };
  const start = cs[0].ts;
  const buildEnd = first(cs, M.buildEnd) ?? first(cs, M.reviewRound);
  const reviews = cs.filter((c) => M.reviewRound.test(c.rest) && (!buildEnd || c.ts >= buildEnd.ts));
  const ends = [
    ['intent', first(cs, M.intentAccepted)],
    ['spec', first(cs, M.specAccepted)],
    ['plan', first(cs, M.planApproved)],
    ['build', buildEnd],
    ['review', reviews.at(-1) ?? null],
    ['live check', last(cs, M.live)],
    ['ship', last(cs, M.merged)],
  ];
  const phases = [];
  let at = start;
  for (const [name, c] of ends) {
    if (!c) continue;
    const end = Math.max(at, c.ts);
    phases.push({ name, start: at, end });
    at = end;
  }
  const merged = last(cs, M.merged);
  if (!merged && now != null) {
    const done = phases.at(-1)?.name;
    const next = PHASE_ORDER[PHASE_ORDER.indexOf(done) + 1] ?? 'ship';
    phases.push({ name: phases.length ? next : 'intent', start: at, end: Math.max(at, now), open: true });
  }
  return { id, startedAt: start, mergedAt: merged?.ts ?? null, phases };
}

/** The phase containing `t`; before the first it is the first, after the last the last (clamped). */
export function phaseAt(phases, t) {
  if (!phases.length) return null;
  return (phases.find((p) => t >= p.start && t < p.end) ?? (t < phases[0].start ? phases[0] : phases.at(-1))).name;
}

// ---- transcripts ----------------------------------------------------------------

/**
 * Reads one transcript's text (B4, B7). Every assistant message with usage
 * counts once (Claude Code writes one line per content block with the same
 * message id and the same usage). Returns the usage turns, the first and last
 * timestamp seen on any line (the file's span), and the lines it could not
 * read. A line that is not JSON, or an assistant line without a numeric
 * usage, is skipped and counted; other line types are not usage and are not
 * counted. Only numbers, ids, the model name and timestamps are kept.
 */
export function usageLines(text) {
  const turns = [];
  const seen = new Set();
  let skipped = 0;
  let firstTs = null;
  let lastTs = null;
  for (const line of String(text ?? '').split(/\r?\n/)) {
    if (!line.trim()) continue;
    let o;
    try {
      o = JSON.parse(line);
    } catch {
      skipped += 1;
      continue;
    }
    if (!o || typeof o !== 'object' || Array.isArray(o)) {
      skipped += 1;
      continue;
    }
    const ts = typeof o.timestamp === 'string' ? Date.parse(o.timestamp) : NaN;
    if (Number.isFinite(ts)) {
      firstTs = firstTs === null ? ts : Math.min(firstTs, ts);
      lastTs = lastTs === null ? ts : Math.max(lastTs, ts);
    }
    if (o.type !== 'assistant') continue;
    const u = o.message?.usage;
    const n = (v) => (typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : v == null ? 0 : NaN);
    const usage = u && typeof u === 'object' ? { input: n(u.input_tokens), output: n(u.output_tokens), cacheRead: n(u.cache_read_input_tokens), cacheWrite: n(u.cache_creation_input_tokens) } : null;
    if (!usage || !Number.isFinite(ts) || typeof o.message?.model !== 'string' || Object.values(usage).some(Number.isNaN)) {
      skipped += 1;
      continue;
    }
    const key = typeof o.message.id === 'string' ? o.message.id : null;
    if (key) {
      if (seen.has(key)) continue;
      seen.add(key);
    }
    turns.push({ ts, model: o.message.model, usage });
  }
  return { turns, firstTs, lastTs, skipped };
}

/** `{id, phase}` for a description starting `§<id> implement|rework|review`, else null (unattributed). */
export function agentTag(description) {
  const m = /^§(\d+)\s+(implement|rework|review)\b/.exec(String(description ?? '').trim());
  return m ? { id: Number(m[1]), phase: m[2] } : null;
}

// ---- the session log --------------------------------------------------------------

/**
 * Coordinator turns from the session log: per session, a turn runs from a
 * `UserPromptSubmit` to the next `Stop` of that session, or to the next
 * prompt when no Stop came. Events carry only what B1 allows.
 * Also the waits' starting points: each Stop or permission Notification and
 * the prompt that ends the wait.
 */
export function sessionTurns(events) {
  const bySession = new Map();
  for (const e of events) {
    const ts = Date.parse(e?.ts);
    if (!e || typeof e.session !== 'string' || !Number.isFinite(ts)) continue;
    if (!bySession.has(e.session)) bySession.set(e.session, []);
    bySession.get(e.session).push({ ...e, tsMs: ts });
  }
  const turns = [];
  const gaps = [];
  for (const [session, list] of bySession) {
    list.sort((a, b) => a.tsMs - b.tsMs);
    let turn = null;
    let waitFrom = null;
    const close = (end) => {
      if (!turn) return;
      turn.end = end;
      turns.push(turn);
      turn = null;
    };
    for (const e of list) {
      if (e.event === 'UserPromptSubmit') {
        close(e.tsMs);
        if (waitFrom !== null) gaps.push({ session, from: waitFrom.ts, to: e.tsMs, who: waitFrom.who });
        waitFrom = null;
        turn = { session, start: e.tsMs, end: Infinity, stopped: false, skill: e.skill ?? null, skillId: Number.isInteger(e.skillId) ? e.skillId : null, worktreeId: Number.isInteger(e.id) ? e.id : null };
      } else if (e.event === 'Stop') {
        // A Stop restarts the gap: a permission prompt earlier in the turn was answered inside it, and the log cannot say when.
        if (turn) {
          waitFrom = { ts: e.tsMs, who: turn };
          turn.stopped = true;
        }
        close(e.tsMs);
      } else if (e.event === 'Notification' && e.kind === 'permission_prompt') {
        if (waitFrom === null && turn) waitFrom = { ts: e.tsMs, who: turn };
      } else if (e.event === 'SessionEnd') {
        close(e.tsMs);
        waitFrom = null;
      }
    }
    if (turn) turns.push(turn);
  }
  return { turns: turns.sort((a, b) => a.start - b.start), gaps };
}

// ---- attribution ----------------------------------------------------------------

/**
 * Which intent a coordinator turn belongs to (B4), in order: the prompt's
 * `skillId`; the worktree session's own intent id; the one intent with a
 * `§N:` commit inside the turn; several of them is "shared" (never split);
 * none is unattributed.
 *
 * @returns {{kind:'intent', id:number}|{kind:'shared', ids:number[]}|{kind:'none'}}
 */
export function attributeTurn(turn, commitTimes) {
  if (turn.skillId !== null) return { kind: 'intent', id: turn.skillId };
  if (turn.worktreeId !== null) return { kind: 'intent', id: turn.worktreeId };
  const ids = [...new Set(commitTimes.filter((c) => c.ts >= turn.start && c.ts <= turn.end).map((c) => c.id))].sort((a, b) => a - b);
  if (ids.length === 1) return { kind: 'intent', id: ids[0] };
  if (ids.length > 1) return { kind: 'shared', ids };
  return { kind: 'none' };
}

const addUsage = (into, u) => {
  for (const k of Object.keys(u)) into[k] += u[k];
};
const bucket = () => ({ coordinator: new Map(), agents: new Map() });
function addTokens(b, source, model, u) {
  if (!b[source].has(model)) b[source].set(model, ZERO());
  addUsage(b[source].get(model), u);
}

const unionMs = (spans) => {
  const out = [];
  for (const s of [...spans].sort((a, b) => a[0] - b[0])) {
    if (out.length && s[0] <= out.at(-1)[1]) out.at(-1)[1] = Math.max(out.at(-1)[1], s[1]);
    else out.push([...s]);
  }
  return out;
};
const overlapMs = (from, to, spans) => unionMs(spans).reduce((n, [a, b]) => n + Math.max(0, Math.min(to, b) - Math.max(from, a)), 0);

/**
 * How a gap `[from, to]` divides over an intent's phases: `[[name, share]]`,
 * the shares (summing to 1) being each phase's part of the gap's length, so a
 * wait that straddles a milestone is not all booked to the phase it began in.
 * A gap inside no phase, or of no length, goes whole to the clamped phase at `from`.
 */
export function spread(phases, from, to) {
  const len = to - from;
  const parts = len > 0 ? phases.map((p) => [p.name, Math.max(0, Math.min(to, p.end) - Math.max(from, p.start))]).filter(([, ms]) => ms > 0) : [];
  const covered = parts.reduce((s, [, ms]) => s + ms, 0);
  if (!covered) return [[phaseAt(phases, from) ?? UNPHASED, 1]];
  const out = parts.map(([name, ms]) => [name, ms / len]);
  // time outside every phase (before the first or after the last) goes to the nearest one, so the shares sum to 1
  const rest = 1 - covered / len;
  if (rest > 1e-12) out[from < phases[0].start ? 0 : out.length - 1][1] += rest;
  return out;
}

/**
 * A wait counts only inside the intent's life (F2): from its first commit to
 * its `merged` commit, or to `now` while unmerged. Returns the gap cut to that
 * span, or null when nothing of it is inside (or the intent has no commits).
 */
export function clipToLife(it, gap, now) {
  if (it.startedAt === null) return null;
  const from = Math.max(gap.from, it.startedAt);
  const to = Math.min(gap.to, it.mergedAt ?? Math.max(now, it.startedAt));
  return to > from ? { ...gap, from, to } : null;
}

/** Splits one gap, after taking agent time out of it, into counted wait and idle (B6). */
export function capWait(gapMs, agentMs = 0, cap = WAIT_CAP_MS) {
  const net = Math.max(0, gapMs - agentMs);
  return { wait: Math.min(net, cap), idle: Math.max(0, net - cap) };
}

const GATE_START = /^(?:(?:intent|spec|plan) drafted|auto stopped:)/i;
const GATE_END = /^(?:intent accepted|spec accepted|plan approved|auto run resumed|auto run started|live check|merged \()/i;
const NOT_THE_OWNER = /^auto stopped:\s*(?:blocked by §?\d+|waiting for §?\d+ to merge)/i; // only a dependency stop is not the owner's wait (F3)

/** Gate gaps of one intent from its commits: `[{from, to}]`. */
export function gateGaps(cs) {
  const gaps = [];
  let open = null;
  for (const c of cs) {
    if (/^intent drafted and accepted/i.test(c.rest)) continue;
    if (GATE_END.test(c.rest)) {
      if (open !== null) gaps.push({ from: open, to: c.ts });
      open = null;
    }
    if (GATE_START.test(c.rest) && !NOT_THE_OWNER.test(c.rest) && open === null) open = c.ts;
  }
  return gaps;
}

// ---- the whole computation ---------------------------------------------------------

/**
 * @param {object} input
 * @param {{hash:string, ts:number, subject:string}[]} input.commits
 * @param {object[]} input.events  session log events (already parsed)
 * @param {{file:string, session:string, usage:ReturnType<typeof usageLines>}[]} input.coordinators
 * @param {{file:string, session:string, description:string, usage:ReturnType<typeof usageLines>}[]} input.agents
 * @param {number} input.now  ms
 * @param {number|null} [input.cutover]  ms; intents merged before it are `partial`
 * @param {number[]} [input.only]  restrict the intents reported
 */
export function computeStats({ commits, events, coordinators, agents, now, cutover = null, only = null }) {
  const byIntent = commitsByIntent(commits);
  const ms = new Map([...byIntent].map(([id, cs]) => [id, milestones(cs, id, now)]));
  const commitTimes = [...byIntent].flatMap(([id, cs]) => cs.map((c) => ({ id, ts: c.ts })));
  const { turns, gaps } = sessionTurns(events);
  const skipped = [];

  const intents = new Map();
  const getIntent = (id) => {
    if (!intents.has(id)) {
      const m = ms.get(id) ?? { id, startedAt: null, mergedAt: null, phases: [] };
      intents.set(id, { id, startedAt: m.startedAt, mergedAt: m.mergedAt, partial: cutover !== null ? m.mergedAt !== null && m.mergedAt < cutover : m.mergedAt !== null, spans: m.phases, phases: new Map() });
    }
    return intents.get(id);
  };
  const phase = (id, name) => {
    const it = getIntent(id);
    if (!it.phases.has(name)) it.phases.set(name, { name, elapsedMs: 0, open: false, coordWorkMs: 0, agentWorkMs: 0, gateWaitMs: 0, sessionWaitMs: 0, idleMs: 0, tokens: bucket() });
    return it.phases.get(name);
  };
  for (const id of byIntent.keys()) {
    for (const p of getIntent(id).spans) Object.assign(phase(id, p.name), { elapsedMs: p.end - p.start, open: p.open === true });
  }

  const shared = new Map();
  const unattributed = { ...bucket(), workMs: 0 };
  const sharedBucket = (ids) => {
    const key = `shared: ${ids.map((i) => `§${i}`).join(', ')}`;
    if (!shared.has(key)) shared.set(key, { ...bucket(), workMs: 0 });
    return shared.get(key);
  };

  // coordinator tokens: each turn of the session, by the turn it falls in
  const turnsBySession = new Map();
  for (const t of turns) turnsBySession.set(t.session, [...(turnsBySession.get(t.session) ?? []), t]);
  const attributionCache = new Map();
  const attribution = (t) => {
    if (!attributionCache.has(t)) attributionCache.set(t, attributeTurn(t, commitTimes));
    return attributionCache.get(t);
  };
  for (const c of coordinators) {
    if (c.usage.skipped) skipped.push({ file: c.file, count: c.usage.skipped });
    for (const u of c.usage.turns) {
      const t = (turnsBySession.get(c.session) ?? []).find((x) => u.ts >= x.start && u.ts <= x.end);
      const a = t ? attribution(t) : { kind: 'none' };
      if (a.kind === 'intent') addTokens(phase(a.id, phaseAt(getIntent(a.id).spans, t.start) ?? UNPHASED).tokens, 'coordinator', u.model, u.usage);
      else if (a.kind === 'shared') addTokens(sharedBucket(a.ids), 'coordinator', u.model, u.usage);
      else addTokens(unattributed, 'coordinator', u.model, u.usage);
    }
  }

  // coord work (B5a): each turn's length, spread over the phases of the intent it is attributed to, not clipped to
  // its life; a turn that never reached its Stop counts at most WAIT_CAP_MS (an open last turn ends at now)
  const coordSpans = new Map(); // intent id -> [[from, to]], taken out of its gate waits (W2)
  for (const t of turns) {
    const end = Number.isFinite(t.end) ? t.end : Math.max(t.start, now);
    const len = t.stopped ? end - t.start : Math.min(end - t.start, WAIT_CAP_MS);
    const a = attribution(t);
    if (a.kind === 'intent') {
      // B4/B5a: a turn attributed to an intent with no commits yet lands in its unphased bucket, as its tokens do
      coordSpans.set(a.id, [...(coordSpans.get(a.id) ?? []), [t.start, t.start + len]]);
      for (const [name, share] of spread(getIntent(a.id).spans, t.start, t.start + len)) phase(a.id, name).coordWorkMs += len * share;
    } else if (a.kind === 'shared') sharedBucket(a.ids).workMs += len;
    else unattributed.workMs += len;
  }

  // agent tokens, and the spans in which agents ran (not owner wait)
  const agentSpans = []; // {session, id|null, span}
  const agentWork = new Map(); // id -> [{name, span}]: agent runs (B5a), by the tag's phase
  for (const a of agents) {
    if (a.usage.skipped) skipped.push({ file: a.file, count: a.usage.skipped });
    const tag = agentTag(a.description);
    if (a.usage.firstTs !== null) agentSpans.push({ session: a.session, id: tag?.id ?? null, span: [a.usage.firstTs, a.usage.lastTs] });
    if (tag && a.usage.firstTs !== null) {
      if (!agentWork.has(tag.id)) agentWork.set(tag.id, []);
      agentWork.get(tag.id).push({ name: AGENT_PHASE[tag.phase], span: [a.usage.firstTs, a.usage.lastTs] });
    }
    for (const u of a.usage.turns) {
      if (tag) addTokens(phase(tag.id, AGENT_PHASE[tag.phase]).tokens, 'agents', u.model, u.usage);
      else addTokens(unattributed, 'agents', u.model, u.usage);
    }
  }

  // B5a: joined per intent; an overlap goes to the earlier run's phase. Runs in start order; each books only the
  // part beyond what earlier-started runs already cover, so per-phase work sums to the union of the intent's runs.
  // Equal starts: the shorter run books first.
  for (const [id, runs] of agentWork) {
    let covered = -Infinity;
    for (const { name, span: [from, to] } of runs.sort((x, y) => x.span[0] - y.span[0] || x.span[1] - y.span[1])) {
      const part = to - Math.max(from, covered);
      if (part > 0) phase(id, name).agentWorkMs += part;
      covered = Math.max(covered, to);
    }
  }

  // owner wait
  for (const [id, cs] of byIntent) {
    const spans = getIntent(id).spans;
    const mine = [...agentSpans.filter((s) => s.id === id).map((s) => s.span), ...(coordSpans.get(id) ?? [])];
    for (const raw of gateGaps(cs)) {
      // a guard: a gate gap starts at one of the intent's commits and ends at the next, so it lies inside its life already
      const g = clipToLife(getIntent(id), raw, now);
      if (!g) continue;
      const { wait, idle } = capWait(g.to - g.from, overlapMs(g.from, g.to, mine));
      for (const [name, share] of spread(spans, g.from, g.to)) {
        const p = phase(id, name);
        p.gateWaitMs += wait * share;
        p.idleMs += idle * share;
      }
    }
  }
  for (const raw of gaps) {
    const a = attribution(raw.who);
    if (a.kind !== 'intent') continue;
    const g = clipToLife(getIntent(a.id), raw, now);
    if (!g) continue;
    const running = agentSpans.filter((s) => s.session === g.session).map((s) => s.span);
    const { wait, idle } = capWait(g.to - g.from, overlapMs(g.from, g.to, running));
    for (const [name, share] of spread(getIntent(a.id).spans, g.from, g.to)) {
      const p = phase(a.id, name);
      p.sessionWaitMs += wait * share;
      p.idleMs += idle * share;
    }
  }

  const wanted = only ? new Set(only) : null;
  const out = [];
  for (const [id, it] of [...intents].sort((a, b) => a[0] - b[0])) {
    if (wanted && !wanted.has(id)) continue;
    const list = [...it.phases.values()].sort((a, b) => order(a.name) - order(b.name));
    out.push({ id, partial: it.partial, startedAt: it.startedAt, mergedAt: it.mergedAt, phases: list, totals: totalsOf(list) });
  }
  return { intents: out, shared, unattributed, skipped };
}

const order = (name) => (PHASE_ORDER.includes(name) ? PHASE_ORDER.indexOf(name) : PHASE_ORDER.length);

function sumBucket(into, b) {
  for (const src of ['coordinator', 'agents']) {
    for (const [model, u] of b[src]) {
      if (!into[src].has(model)) into[src].set(model, ZERO());
      addUsage(into[src].get(model), u);
    }
  }
}

/** The time columns of B8, in print order: [field, header]. */
const COLUMNS = [
  ['elapsedMs', 'elapsed'],
  ['coordWorkMs', 'coord work'],
  ['agentWorkMs', 'agent work'],
  ['gateWaitMs', 'gate wait'],
  ['sessionWaitMs', 'in-session'],
  ['idleMs', 'idle'],
];
const TIME_COLUMNS = COLUMNS.map(([k]) => k);
const header = () => COLUMNS.map(([, h]) => h.padStart(11)).join(' ');
const cells = (t) => COLUMNS.map(([k]) => duration(t[k]).padStart(11)).join(' ');

function totalsOf(list) {
  const t = { elapsedMs: 0, coordWorkMs: 0, agentWorkMs: 0, gateWaitMs: 0, sessionWaitMs: 0, idleMs: 0, tokens: bucket() };
  for (const p of list) {
    for (const k of TIME_COLUMNS) t[k] += p[k];
    sumBucket(t.tokens, p.tokens);
  }
  return t;
}

/** Every token the computation counted, to compare against a source total. */
export function grandTotal(stats) {
  const all = bucket();
  for (const it of stats.intents) sumBucket(all, it.totals.tokens);
  for (const b of stats.shared.values()) sumBucket(all, b);
  sumBucket(all, stats.unattributed);
  const sum = ZERO();
  for (const src of ['coordinator', 'agents']) for (const u of all[src].values()) addUsage(sum, u);
  return sum;
}

// ---- output ---------------------------------------------------------------------------

/** "1h05m", "12m", "40s", "0s". */
export function duration(ms) {
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  return `${Math.floor(m / 60)}h${String(m % 60).padStart(2, '0')}m`;
}

const tok = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n));
const usageText = (u) => `in ${tok(u.input)} out ${tok(u.output)} cr ${tok(u.cacheRead)} cw ${tok(u.cacheWrite)}`;

function tokenLines(b, indent) {
  const lines = [];
  for (const src of ['coordinator', 'agents']) {
    for (const [model, u] of [...b[src]].sort((a, c) => a[0].localeCompare(c[0]))) lines.push(`${indent}${src} ${model}: ${usageText(u)}`);
  }
  return lines;
}

/** The B8 text for one intent (also what `stats.md` holds, after its stamp). */
export function formatIntent(it) {
  const flag = it.partial ? ' (partial: merged before stats existed; tokens and session waits may be missing)' : '';
  const lines = [`§${it.id}${flag}`, `  ${'phase'.padEnd(12)} ${header()}`];
  const row = (name, p) => `  ${name.padEnd(12)} ${cells(p)}`;
  for (const p of it.phases) {
    lines.push(row(p.open ? `${p.name} (open)` : p.name, p), ...tokenLines(p.tokens, '      '));
  }
  lines.push(row('total', it.totals), ...tokenLines(it.totals.tokens, '      '));
  return lines.join('\n');
}

function formatSide(stats) {
  const lines = [];
  const work = (b) => (b.workMs ? [`  coord work ${duration(b.workMs)}`] : []);
  for (const [label, b] of stats.shared) lines.push(`${label}`, ...work(b), ...tokenLines(b, '  '));
  const un = [...work(stats.unattributed), ...tokenLines(stats.unattributed, '  ')];
  if (un.length) lines.push('unattributed', ...un);
  return lines;
}

function formatSkipped(stats) {
  if (!stats.skipped.length) return ['skipped lines: 0'];
  const n = stats.skipped.reduce((s, x) => s + x.count, 0);
  return [`skipped lines: ${n}`, ...stats.skipped.map((s) => `  ${s.file}: ${s.count}`)];
}

/** `npm run stats -- <id>` text (B8). */
export function formatStats(stats) {
  const lines = [];
  for (const it of stats.intents) lines.push(formatIntent(it), '');
  lines.push(...formatSide(stats), ...formatSkipped(stats));
  return lines.join('\n');
}

/** `npm run stats -- --all`: one line per intent; `partial` marks every figure. */
export function formatAll(stats) {
  const lines = [`${'intent'.padEnd(8)} ${header()}  tokens (in/out/cache read/cache write)`];
  const total = Object.fromEntries(TIME_COLUMNS.map((k) => [k, 0]));
  for (const it of stats.intents) {
    const t = it.totals;
    const u = ZERO();
    for (const src of ['coordinator', 'agents']) for (const x of t.tokens[src].values()) addUsage(u, x);
    const tag = it.partial ? ' partial' : '';
    lines.push(`${`§${it.id}`.padEnd(8)} ${cells(t)}  ${usageText(u)}${tag}`);
    for (const k of Object.keys(total)) total[k] += t[k];
  }
  const g = grandTotal(stats);
  lines.push(`${'total'.padEnd(8)} ${cells(total)}  ${usageText(g)} (all sources, incl. shared and unattributed)`);
  lines.push(...formatSide(stats), ...formatSkipped(stats));
  return lines.join('\n');
}

const plainBucket = (b) => ({ coordinator: Object.fromEntries(b.coordinator), agents: Object.fromEntries(b.agents), ...(b.workMs === undefined ? {} : { workMs: b.workMs }) });

/** The same data as plain JSON (B8 `--json`). */
export function statsJson(stats) {
  return {
    intents: stats.intents.map((it) => ({
      id: it.id,
      partial: it.partial,
      startedAt: it.startedAt,
      mergedAt: it.mergedAt,
      phases: it.phases.map((p) => ({ ...p, tokens: plainBucket(p.tokens) })),
      totals: { ...it.totals, tokens: plainBucket(it.totals.tokens) },
    })),
    shared: Object.fromEntries([...stats.shared].map(([k, b]) => [k, plainBucket(b)])),
    unattributed: plainBucket(stats.unattributed),
    skipped: stats.skipped,
  };
}

/** The committed `stats.md` of one intent (B9): generated, stamped, numbers and ids only. */
export function statsMarkdown(it, stamp) {
  return `<!-- generated-by: ${stamp} -->\n# §${it.id} stats\n\nDerived totals only (no prompt or response text). Regenerate live with \`npm run stats -- ${it.id}\`.\n\n\`\`\`text\n${formatIntent(it)}\n\`\`\`\n`;
}

// ---- arguments ----

/** `{ids, all, json, transcripts}` from argv, or throws a usage message. */
export function parseStatsArgs(argv, defaultTranscripts) {
  const opts = { ids: [], all: false, json: false, transcripts: defaultTranscripts };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--all') opts.all = true;
    else if (a === '--json') opts.json = true;
    else if (a === '--transcripts') {
      if (!argv[i + 1]) throw new Error('--transcripts needs a directory');
      opts.transcripts = argv[(i += 1)];
    } else if (/^§?\d+$/.test(a)) opts.ids.push(Number(a.replace('§', '')));
    else throw new Error(`unknown argument: ${a}`);
  }
  if (!opts.all && !opts.ids.length) throw new Error('give an intent id or --all');
  return opts;
}
