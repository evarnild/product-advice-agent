// Pure logic behind parallel sessions: `npm run spawn`, `npm run sessions`
// and the session-event hook. Kept free of git/fs calls so it can be
// unit-tested; see session-lib.test.mjs.
import { parseAuto, parseGate, PREFIX_TO_TYPE, TYPE_RULES } from './intent-check-lib.mjs';

/** Name of the shared event log, inside the git common dir (never committed). */
export const EVENT_LOG = 'product-advice-agent-sessions.jsonl';

/** Spawned worktrees live next to the repo, never inside it. */
export const WORKTREE_PARENT = 'product-advice-agent-wt';

const TYPE_TO_PREFIX = Object.fromEntries(Object.entries(PREFIX_TO_TYPE).map(([p, t]) => [t, p]));

/**
 * Each intent gets a stable port for a dev server, should the project run
 * one: §27 → 5227. Parallel sessions then never collide. 5200–5299 stays
 * clear of the common defaults (3000, 5000, 5173, 8000, 8080).
 */
export function portFor(id) {
  return 5200 + (Number(id) % 100);
}

/** `feat/27-naval-retreat` from metadata's type, id and slug. */
export function branchFor({ type, id, slug }) {
  const prefix = TYPE_TO_PREFIX[type];
  if (!prefix) throw new Error(`metadata type "${type}" has no branch prefix (${Object.keys(TYPE_TO_PREFIX).join(', ')})`);
  return `${prefix}/${id}-${slug}`;
}

/** `<parent of repo>/product-advice-agent-wt/<id>-<slug>`, with forward slashes. */
export function worktreePathFor(repoRoot, id, slug) {
  const root = toSlashes(repoRoot).replace(/\/+$/, '');
  const parent = root.slice(0, root.lastIndexOf('/'));
  return `${parent}/${WORKTREE_PARENT}/${id}-${slug}`;
}

function toSlashes(p) {
  return p.replace(/\\/g, '/');
}

/**
 * Comparison key for a path. Hooks hand us `C:\Users\…`, git hands us
 * `C:/Users/…`, and Windows paths are case-insensitive.
 */
export function pathKey(p) {
  return toSlashes(p).replace(/\/+$/, '').toLowerCase();
}

/** Parses `git worktree list --porcelain` into `{path, head, branch}` records (branch null when detached). */
export function parseWorktreeList(text) {
  const out = [];
  let cur = null;
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('worktree ')) {
      cur = { path: line.slice('worktree '.length), head: null, branch: null, bare: false };
      out.push(cur);
    } else if (cur && line.startsWith('HEAD ')) {
      cur.head = line.slice('HEAD '.length);
    } else if (cur && line.startsWith('branch ')) {
      cur.branch = line.slice('branch '.length).replace(/^refs\/heads\//, '');
    } else if (cur && line === 'bare') {
      cur.bare = true;
    }
  }
  return out.filter((w) => !w.bare);
}

/** One JSON object per line; lines that don't parse are skipped, not fatal. */
export function parseEvents(text) {
  const out = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const e = JSON.parse(line);
      if (e && typeof e === 'object' && e.event && e.worktree) out.push(e);
    } catch {
      // A half-written line from a killed hook must not hide the rest.
    }
  }
  return out;
}

/** What each event says about the session, in the words the status table shows. */
export const EVENT_STATE = {
  spawned: 'not started',
  SessionStart: 'started',
  UserPromptSubmit: 'working',
  Stop: 'idle',
  Notification: 'needs you',
  SessionEnd: 'closed',
};

/**
 * Latest event per worktree, keyed by `pathKey` — except that an idle
 * reminder never replaces a prompt still waiting on the owner. Claude Code
 * can send its "waiting for your input" reminder while a permission prompt
 * is unanswered; letting it win would hide the block. The owner's next
 * prompt, the turn ending, or the session ending clears "needs you".
 */
export function latestEventByWorktree(events) {
  const out = new Map();
  for (const e of events) {
    const key = pathKey(e.worktree);
    const prev = out.get(key);
    if (prev && isNotification(prev, 'needs you') && isNotification(e, 'idle')) continue;
    out.set(key, e);
  }
  return out;
}

function isNotification(e, state) {
  return e.event === 'Notification' && notificationState(e) === state;
}

/**
 * Claude Code sends a Notification both when it needs the owner (a
 * permission prompt, a question) and when it has merely been idle for a
 * minute. Only the first kind is "needs you". Older versions send no
 * `notification_type`, so the idle prompt is also recognised by its text;
 * anything unrecognised stays "needs you", the safe direction.
 */
const IDLE_NOTIFICATIONS = new Set(['idle_prompt', 'auth_success']);

export function notificationState(e) {
  if (IDLE_NOTIFICATIONS.has(e.kind)) return 'idle';
  if (!e.kind && /waiting for your input/i.test(e.detail ?? '')) return 'idle';
  return 'needs you';
}

/** `{state, since, detail}` for one worktree's latest event, or a placeholder when it has none. */
export function sessionState(event) {
  if (!event) return { state: 'no events', since: null, detail: '' };
  const state = event.event === 'Notification' ? notificationState(event) : (EVENT_STATE[event.event] ?? event.event);
  return { state, since: event.ts ?? null, detail: event.detail ?? '' };
}

/**
 * Turns one hook's stdin payload into the record to log, or null when it
 * isn't a hook event. Events are filed under the session's project
 * directory (`CLAUDE_PROJECT_DIR`), not wherever the session happens to have
 * `cd`'d — a coordinator running `npm run verify` inside another worktree
 * must not show up as that worktree's session. Prompts are logged by length
 * only: the log should show that a session is working, never what was typed.
 */
export function eventRecordFrom(input, env = {}, fallbackCwd = '.') {
  if (!input || typeof input !== 'object' || typeof input.hook_event_name !== 'string') return null;
  const event = input.hook_event_name;
  const fields = { event, session: input.session_id };
  if (event === 'UserPromptSubmit') {
    fields.promptChars = typeof input.prompt === 'string' ? input.prompt.length : 0;
    fields.detail = `${fields.promptChars} chars`;
  } else if (event === 'Notification') {
    if (input.notification_type) fields.kind = String(input.notification_type);
    fields.detail = clip(input.message);
  } else if (event === 'SessionStart') {
    fields.detail = clip(input.source);
  } else if (event === 'SessionEnd') {
    fields.detail = clip(input.reason);
  } else {
    fields.detail = '';
  }
  const dir = env.CLAUDE_PROJECT_DIR || (typeof input.cwd === 'string' && input.cwd) || fallbackCwd;
  return { dir, fields };
}

/** "4m", "2h", "3d" — enough to tell a stuck session from a busy one. */
export function age(ts, now) {
  if (!ts) return '';
  const s = Math.max(0, Math.round((now - Date.parse(ts)) / 1000));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  if (s < 86400) return `${Math.floor(s / 3600)}h`;
  return `${Math.floor(s / 86400)}d`;
}

const GATE_LETTERS = { intent_accepted: 'I', spec_accepted: 'S', plan_approved: 'P' };

/** "I·S·P" with a "-" for each gate the type needs that is not recorded yet. */
export function gateSummary(metadata) {
  const gates = metadata && TYPE_RULES[metadata.type]?.gates;
  if (!gates) return '';
  return gates.map((key) => (isRecorded(metadata[key]) ? GATE_LETTERS[key] : '-')).join('·');
}

/**
 * What `npm run sessions` and `npm run queue` show for an auto run:
 * `auto · r2 · live check` once stopped, `auto · r2` while running, and
 * nothing for an intent without `auto_authorized`.
 */
export function autoSummary(metadata) {
  const auto = parseAuto(metadata);
  if (auto.authorized.state !== 'recorded') return '';
  const parts = ['auto'];
  if (auto.round !== null) parts.push(`r${auto.round}`);
  if (auto.stopped !== null) parts.push(auto.stopped);
  return parts.join(' · ');
}

/** The metadata-derived columns of a sessions row (status, gates, auto); empty for no metadata. */
export function metadataColumns(metadata) {
  return { status: metadata?.status ?? null, gates: gateSummary(metadata), auto: autoSummary(metadata) };
}

/** Same rule as check-intent: both forms of a dated gate count (parseGate). */
function isRecorded(v) {
  return parseGate(v).state === 'recorded';
}

/** Rows that need the owner sort first, then work in flight, then the rest. */
const STATE_ORDER = ['needs you', 'idle', 'working', 'started', 'not started', 'no events', 'closed'];

export function sortRows(rows) {
  const rank = (r) => {
    const i = STATE_ORDER.indexOf(r.session.state);
    return i < 0 ? STATE_ORDER.length : i;
  };
  return [...rows].sort((a, b) => rank(a) - rank(b) || String(a.id ?? '').localeCompare(String(b.id ?? '')));
}

/**
 * Renders the coordinator's table. Each row:
 * `{id, branch, path, status, gates, auto, ahead, behind, dirty, session:{state,since,detail}, port}`.
 */
export function formatStatusTable(rows, now) {
  const header = ['§', 'branch', 'status', 'gates', 'auto', '±main', 'dirty', 'session', 'port'];
  const body = sortRows(rows).map((r) => [
    r.id ? `§${r.id}` : '—',
    r.branch ?? '(detached)',
    r.status ?? '',
    r.gates ?? '',
    r.auto ?? '',
    r.ahead == null ? '' : `+${r.ahead}/-${r.behind}`,
    r.dirty ? String(r.dirty) : '',
    describeSession(r.session, now),
    r.port ? String(r.port) : '',
  ]);
  const widths = header.map((h, i) => Math.max(h.length, ...body.map((row) => row[i].length)));
  const fmt = (row) => row.map((c, i) => c.padEnd(widths[i])).join('  ').trimEnd();
  const lines = [fmt(header), fmt(widths.map((w) => '-'.repeat(w))), ...body.map(fmt)];
  const details = sortRows(rows)
    .filter((r) => r.session.state === 'needs you' && r.session.detail)
    .map((r) => `  ${r.id ? `§${r.id}` : r.branch}: ${r.session.detail}`);
  if (details.length) lines.push('', 'Waiting on you:', ...details);
  return lines.join('\n');
}

/**
 * The rows `formatStatusTable` prints, as plain data for `sessions --json`:
 * same order, every field spelled out, the session's age in whole seconds
 * (null without a timestamp) instead of the "4m" text.
 */
export function sessionsData(rows, now) {
  return sortRows(rows).map((r) => ({
    id: r.id ?? null,
    branch: r.branch ?? null,
    path: r.path ?? null,
    status: r.status ?? null,
    gates: r.gates ?? '',
    auto: r.auto ?? '',
    ahead: r.ahead ?? null,
    behind: r.behind ?? null,
    dirty: r.dirty ?? null,
    port: r.port ?? null,
    session: {
      state: r.session.state,
      since: r.session.since ?? null,
      ageSeconds: r.session.since ? Math.max(0, Math.round((now - Date.parse(r.session.since)) / 1000)) : null,
      detail: r.session.detail ?? '',
    },
  }));
}

function describeSession(session, now) {
  const a = age(session.since, now);
  return a ? `${session.state} (${a})` : session.state;
}

/** One log line for the event tail: `2026-10-07T21:40:12Z  §27  Notification  Claude needs your permission…`. */
export function formatEvent(e) {
  const id = e.id ? `§${e.id}` : e.branch ?? '—';
  return [e.ts, id.padEnd(5), e.event.padEnd(16), e.detail ?? ''].join('  ').trimEnd();
}

/** Single-line, length-capped detail so one event stays one log line. */
export function clip(text, max = 120) {
  const s = String(text ?? '').replace(/\s+/g, ' ').trim();
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

/**
 * The `CLAUDE.local.md` dropped into a spawned worktree. Claude Code loads it
 * on every session start there, so the session knows which intent it serves
 * and what it may touch without being told.
 */
export function sessionBrief({ id, slug, type, branch, intentDir, port, coordinatorPath }) {
  return `<!-- written by npm run spawn (scripts/spawn-intent.mjs); not committed -->
# You are the session for §${id} — ${slug}

- **Intent:** \`${intentDir}/\` (type: ${type}). Read \`intent.md\`, then
  \`spec.md\`/\`plan.md\` if present, and \`metadata.yml\` for which gates are recorded.
- **Branch:** \`${branch}\` — this worktree only. Commit here; never switch branch.
- **Port:** if the project runs a dev server, use port ${port}. It is reserved
  for §${id}, so parallel sessions never collide.
- **Coordinator:** the main checkout at \`${coordinatorPath}\`.

## What this session may and may not do

- Write code, tests and docs for §${id}, and inside \`${intentDir}/\` only what
  \`intents/README.md\` → "Who edits what" allows. No code before the gates
  your type needs are recorded. If they are missing, draft the missing
  artefact and stop for the owner.
- **Nobody edits the queue**: \`npm run queue\` generates it from \`metadata.yml\`.
- **Do not merge into \`main\`** and do not rebase other branches.
- When \`npm run verify\` is green and the work is done, set \`status: in-review\` in
  \`metadata.yml\`, commit, and say so. The coordinator runs \`/review\` and the owner merges.
- If you are told \`main\` moved, rebase this branch on it and re-run \`npm run verify\`.
`;
}
