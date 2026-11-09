import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import {
  age,
  autoSummary,
  branchFor,
  clip,
  eventRecordFrom,
  formatEvent,
  formatStatusTable,
  sessionsData,
  gateSummary,
  latestEventByWorktree,
  metadataColumns,
  notificationState,
  parseEvents,
  parseWorktreeList,
  pathKey,
  portFor,
  sessionBrief,
  sessionState,
  sortRows,
  worktreePathFor,
} from './session-lib.mjs';

describe('naming scheme', () => {
  it('gives each intent a stable port in 5200-5299', () => {
    expect(portFor(27)).toBe(5227);
    expect(portFor('9')).toBe(5209);
    expect(portFor(73)).toBe(5273);
    expect(portFor(199)).toBe(5299);
  });

  it('derives the branch from type, id and slug', () => {
    expect(branchFor({ type: 'feature', id: '28', slug: 'naval-retreat' })).toBe('feat/28-naval-retreat');
    expect(branchFor({ type: 'adjustment', id: 29, slug: 'readme' })).toBe('adjust/29-readme');
    expect(() => branchFor({ type: 'chore', id: 1, slug: 'x' })).toThrow(/no branch prefix/);
  });

  it('puts worktrees next to the repo, not inside it', () => {
    expect(worktreePathFor('C:\\Users\\me\\src\\product-advice-agent', 27, 'parallel-sessions')).toBe(
      'C:/Users/me/src/product-advice-agent-wt/27-parallel-sessions',
    );
    expect(worktreePathFor('/home/e/product-advice-agent/', 3, 'x')).toBe('/home/e/product-advice-agent-wt/3-x');
  });

  it('matches paths across slash style, trailing slash and drive-letter case', () => {
    expect(pathKey('C:\\Users\\me\\src\\product-advice-agent-wt\\27-x\\')).toBe(pathKey('c:/Users/me/src/product-advice-agent-wt/27-x'));
  });
});

describe('parseWorktreeList', () => {
  it('reads branches, detached heads and skips bare entries', () => {
    const text = [
      'worktree C:/r/product-advice-agent',
      'HEAD aaa',
      'branch refs/heads/main',
      '',
      'worktree C:/r/product-advice-agent-wt/27-x',
      'HEAD bbb',
      'branch refs/heads/refactor/27-x',
      '',
      'worktree C:/r/review',
      'HEAD ccc',
      'detached',
      'prunable gitdir file points to non-existent location',
      '',
      'worktree C:/r/bare.git',
      'bare',
      '',
    ].join('\r\n');
    expect(parseWorktreeList(text)).toEqual([
      { path: 'C:/r/product-advice-agent', head: 'aaa', branch: 'main', bare: false },
      { path: 'C:/r/product-advice-agent-wt/27-x', head: 'bbb', branch: 'refactor/27-x', bare: false },
      { path: 'C:/r/review', head: 'ccc', branch: null, bare: false },
    ]);
  });
});

describe('events', () => {
  const line = (o) => JSON.stringify(o);

  it('skips half-written and foreign lines without losing the rest', () => {
    const text = [
      line({ ts: '2026-10-07T10:00:00Z', event: 'SessionStart', worktree: 'C:/w/a' }),
      '{"ts":"2026-10-07T10:01:00Z","event":"Sto',
      line({ hello: 'world' }),
      '',
      line({ ts: '2026-10-07T10:02:00Z', event: 'Stop', worktree: 'C:/w/a' }),
    ].join('\n');
    expect(parseEvents(text).map((e) => e.event)).toEqual(['SessionStart', 'Stop']);
  });

  it('keeps the latest event per worktree whatever path style wrote it', () => {
    const latest = latestEventByWorktree([
      { event: 'UserPromptSubmit', worktree: 'C:\\w\\a' },
      { event: 'Notification', worktree: 'c:/w/a', detail: 'needs permission' },
      { event: 'Stop', worktree: 'C:/w/b' },
    ]);
    expect(latest.get(pathKey('C:/w/a')).event).toBe('Notification');
    expect(latest.size).toBe(2);
  });

  it('names the session state each event implies', () => {
    expect(sessionState(undefined).state).toBe('no events');
    expect(sessionState({ event: 'spawned' }).state).toBe('not started');
    expect(sessionState({ event: 'UserPromptSubmit' }).state).toBe('working');
    expect(sessionState({ event: 'Stop' }).state).toBe('idle');
    expect(sessionState({ event: 'Notification', detail: 'x' })).toMatchObject({ state: 'needs you', detail: 'x' });
    expect(sessionState({ event: 'SessionEnd' }).state).toBe('closed');
    expect(sessionState({ event: 'SomethingNew' }).state).toBe('SomethingNew');
  });

  it('formats one event per line', () => {
    expect(formatEvent({ ts: 'T', id: '27', event: 'Stop', worktree: 'w' })).toBe('T  §27    Stop');
    expect(formatEvent({ ts: 'T', branch: 'main', event: 'SessionStart', worktree: 'w', detail: 'startup' })).toBe(
      'T  main   SessionStart      startup',
    );
  });

  it('clips details to one short line', () => {
    expect(clip('a\n  b')).toBe('a b');
    expect(clip('x'.repeat(10), 5)).toBe('xxxx…');
    expect(clip(undefined)).toBe('');
    expect(clip('  padded  ')).toBe('padded');
    expect(clip('x'.repeat(5), 5)).toBe('xxxxx'); // exactly at the limit: not clipped
  });

  it('drops events that name no worktree, so one bad line cannot break the table', () => {
    const text = [
      JSON.stringify({ event: 'Stop' }),
      JSON.stringify({ worktree: 'C:/w/a' }),
      JSON.stringify({ event: 'Stop', worktree: 'C:/w/a' }),
    ].join('\n');
    const events = parseEvents(text);
    expect(events).toHaveLength(1);
    expect(() => latestEventByWorktree(events)).not.toThrow();
  });

  it('tells a permission prompt from the idle reminder', () => {
    expect(notificationState({ kind: 'permission_prompt', detail: 'Claude needs your permission to use Bash' })).toBe('needs you');
    expect(notificationState({ kind: 'elicitation_dialog' })).toBe('needs you');
    expect(notificationState({ kind: 'idle_prompt', detail: 'Claude is waiting for your input' })).toBe('idle');
    expect(notificationState({ kind: 'auth_success' })).toBe('idle');
    // Older Claude Code sends no notification_type: fall back to the text.
    expect(notificationState({ detail: 'Claude is waiting for your input' })).toBe('idle');
    expect(notificationState({ detail: 'Claude needs your permission to use Bash' })).toBe('needs you');
    expect(notificationState({ kind: 'something_new' })).toBe('needs you');
    // A typed notification is trusted over its text; the text match ignores case.
    expect(notificationState({ kind: 'permission_prompt', detail: 'waiting for your input' })).toBe('needs you');
    expect(notificationState({ detail: 'Claude is WAITING FOR YOUR INPUT' })).toBe('idle');
    expect(sessionState({ event: 'Notification', kind: 'idle_prompt', detail: 'x' }).state).toBe('idle');
  });
});

describe('latestEventByWorktree and pending prompts', () => {
  const ev = (event, extra = {}) => ({ event, worktree: 'C:/w/a', ...extra });
  const stateAfter = (...events) => sessionState(latestEventByWorktree(events).get(pathKey('C:/w/a'))).state;

  it('keeps "needs you" when an idle reminder follows an unanswered prompt', () => {
    expect(stateAfter(ev('Notification', { kind: 'permission_prompt' }), ev('Notification', { kind: 'idle_prompt' }))).toBe('needs you');
    expect(stateAfter(ev('Notification', { detail: 'needs your permission' }), ev('Notification', { detail: 'waiting for your input' }))).toBe('needs you');
  });

  it('clears "needs you" on the next prompt, turn end, or session end', () => {
    const ask = ev('Notification', { kind: 'permission_prompt' });
    expect(stateAfter(ask, ev('UserPromptSubmit'))).toBe('working');
    expect(stateAfter(ask, ev('Stop'), ev('Notification', { kind: 'idle_prompt' }))).toBe('idle');
    expect(stateAfter(ask, ev('SessionEnd'))).toBe('closed');
    expect(stateAfter(ask, ev('Notification', { kind: 'elicitation_dialog', detail: 'newer' }))).toBe('needs you');
  });
});

describe('eventRecordFrom', () => {
  const base = { session_id: 's1', cwd: 'C:/elsewhere' };

  it('logs a prompt by its length only, never its text', () => {
    const r = eventRecordFrom({ ...base, hook_event_name: 'UserPromptSubmit', prompt: 'my key is sk-SECRET-123' });
    expect(r.fields).toEqual({ event: 'UserPromptSubmit', session: 's1', promptChars: 23, detail: '23 chars' });
    expect(JSON.stringify(r)).not.toContain('SECRET');
    expect(eventRecordFrom({ ...base, hook_event_name: 'UserPromptSubmit' }).fields.promptChars).toBe(0);
    expect(eventRecordFrom({ ...base, hook_event_name: 'UserPromptSubmit', prompt: ['not', 'text'] }).fields.promptChars).toBe(0);
  });

  it('keeps the notification type and message', () => {
    const r = eventRecordFrom({ ...base, hook_event_name: 'Notification', notification_type: 'idle_prompt', message: 'Claude is\nwaiting' });
    expect(r.fields).toMatchObject({ event: 'Notification', kind: 'idle_prompt', detail: 'Claude is waiting' });
    expect(eventRecordFrom({ ...base, hook_event_name: 'Notification', message: 'm' }).fields).not.toHaveProperty('kind');
  });

  it('records start source and end reason, nothing for other events', () => {
    expect(eventRecordFrom({ ...base, hook_event_name: 'SessionStart', source: 'startup' }).fields.detail).toBe('startup');
    expect(eventRecordFrom({ ...base, hook_event_name: 'SessionEnd', reason: 'logout' }).fields.detail).toBe('logout');
    expect(eventRecordFrom({ ...base, hook_event_name: 'Stop', prompt: 'leak?' }).fields.detail).toBe('');
  });

  it('files the event under the project directory, not the current one', () => {
    const input = { ...base, hook_event_name: 'Stop' };
    expect(eventRecordFrom(input, { CLAUDE_PROJECT_DIR: 'C:/proj' }, 'C:/fallback').dir).toBe('C:/proj');
    expect(eventRecordFrom(input, {}, 'C:/fallback').dir).toBe('C:/elsewhere');
    expect(eventRecordFrom({ hook_event_name: 'Stop' }, {}, 'C:/fallback').dir).toBe('C:/fallback');
    expect(eventRecordFrom({ hook_event_name: 'Stop', cwd: 42 }, {}, 'C:/fallback').dir).toBe('C:/fallback');
  });

  it('ignores anything that is not a hook payload', () => {
    for (const bad of [null, [], 'x', 42, {}, { hook_event_name: { nested: true } }]) {
      expect(eventRecordFrom(bad)).toBeNull();
    }
  });
});

describe('status table', () => {
  const now = Date.parse('2026-10-07T12:00:00Z');
  const row = (over) => ({
    id: '27',
    branch: 'refactor/27-x',
    status: 'in-progress',
    gates: 'I·P',
    ahead: 2,
    behind: 0,
    dirty: 0,
    port: 5227,
    session: { state: 'working', since: '2026-10-07T11:56:00Z', detail: '' },
    ...over,
  });

  it('formats ages coarsely', () => {
    expect(age('2026-10-07T11:59:30Z', now)).toBe('30s');
    expect(age('2026-10-07T11:56:00Z', now)).toBe('4m');
    expect(age('2026-10-07T09:00:00Z', now)).toBe('3h');
    expect(age('2026-10-04T12:00:00Z', now)).toBe('3d');
    expect(age(null, now)).toBe('');
  });

  it('puts the unit boundaries exactly at 60 s, 1 h and 1 d, and never goes negative', () => {
    const at = (s) => new Date(now - s * 1000).toISOString();
    expect(age(at(59), now)).toBe('59s');
    expect(age(at(60), now)).toBe('1m');
    expect(age(at(3599), now)).toBe('59m');
    expect(age(at(3600), now)).toBe('1h');
    expect(age(at(86399), now)).toBe('23h');
    expect(age(at(86400), now)).toBe('1d');
    expect(age(at(-120), now)).toBe('0s'); // clock skew: an event "from the future"
  });

  it('summarises the gates each type needs', () => {
    expect(gateSummary({ type: 'fix', intent_accepted: '2026-10-07', plan_approved: [] })).toBe('I·-');
    const d = '2026-10-07';
    expect(gateSummary({ type: 'feature', intent_accepted: d, spec_accepted: d, plan_approved: d })).toBe('I·S·P');
    expect(gateSummary({ type: 'feature', intent_accepted: '~', spec_accepted: 'null', plan_approved: 'TBD' })).toBe('-·-·-');
    expect(gateSummary({ type: 'feature', intent_accepted: `${d} by-agent`, spec_accepted: d, plan_approved: `${d} by-agent` })).toBe('I·S·P');
    expect(gateSummary({ type: 'experiment', intent_accepted: d })).toBe('I');
    expect(gateSummary({ type: 'chore' })).toBe('');
    expect(gateSummary(null)).toBe('');
  });

  it('puts sessions that need the owner first', () => {
    const rows = [
      row({ id: '28', session: { state: 'working' } }),
      row({ id: '29', session: { state: 'needs you' } }),
      row({ id: null, branch: 'main', session: { state: 'no events' } }),
      row({ id: '27', session: { state: 'idle' } }),
    ];
    expect(sortRows(rows).map((r) => r.id ?? r.branch)).toEqual(['29', '27', '28', 'main']);
  });

  it('ranks unknown states after every known one and breaks ties by id', () => {
    const rows = [
      row({ id: '31', session: { state: 'SomethingNew' } }),
      row({ id: '30', session: { state: 'closed' } }),
      row({ id: '29', session: { state: 'idle' } }),
      row({ id: '28', session: { state: 'idle' } }),
    ];
    expect(sortRows(rows).map((r) => r.id)).toEqual(['28', '29', '30', '31']);
  });

  it('labels a detached worktree and lists only "needs you" rows under Waiting on you', () => {
    const text = formatStatusTable(
      [
        row({ id: null, branch: null, session: { state: 'idle', since: null, detail: 'Claude is waiting for your input' } }),
        row({ id: '28', session: { state: 'needs you', since: null, detail: 'permission for Bash' } }),
      ],
      now,
    );
    expect(text).toMatch(/^—\s+\(detached\)/m);
    expect(text).toContain('Waiting on you:\n  §28: permission for Bash');
    expect(text).not.toContain('waiting for your input');
  });

  it('renders aligned columns and lists what is waiting on the owner', () => {
    const text = formatStatusTable(
      [
        row({}),
        row({ id: '28', branch: 'feat/28-y', dirty: 3, session: { state: 'needs you', since: '2026-10-07T11:58:00Z', detail: 'Claude needs your permission to use Bash' } }),
        row({ id: null, branch: 'main', status: null, gates: null, ahead: null, port: null, session: { state: 'no events', since: null } }),
      ],
      now,
    );
    const lines = text.split('\n');
    expect(lines[0]).toMatch(/^§\s+branch\s+status\s+gates\s+auto\s+±main\s+dirty\s+session\s+port$/);
    expect(lines[2]).toMatch(/^§28\s+feat\/28-y\s+in-progress\s+I·P\s+\+2\/-0\s+3\s+needs you \(2m\)\s+5227$/);
    expect(lines[3]).toMatch(/^§27\s+refactor\/27-x .* working \(4m\)\s+5227$/);
    expect(lines[4]).toMatch(/^—\s+main\s+no events$/);
    expect(text).toContain('Waiting on you:\n  §28: Claude needs your permission to use Bash');
  });
});

describe('autoSummary', () => {
  const d = '2026-10-24';
  it('T5: shows the round and the reason once stopped', () => {
    expect(autoSummary({ auto_authorized: d, auto_round: '2', auto_stopped: 'live check' })).toBe('auto · r2 · live check');
  });
  it('T5: shows only the round while running', () => {
    expect(autoSummary({ auto_authorized: d, auto_round: '2', auto_stopped: [] })).toBe('auto · r2');
    expect(autoSummary({ auto_authorized: d + ' by-agent' })).toBe('auto');
  });
  it('T5: shows nothing without auto_authorized, even with a round and a reason', () => {
    expect(autoSummary({ auto_round: '2', auto_stopped: 'live check' })).toBe('');
    expect(autoSummary({ auto_authorized: [], auto_round: '1' })).toBe('');
    expect(autoSummary({ auto_authorized: 'yes', auto_round: '1' })).toBe('');
    expect(autoSummary(null)).toBe('');
  });
  it('T5: the sessions table has an auto column after gates with that text', () => {
    const row = {
      id: '50', branch: 'feat/50-x', status: 'in-review', gates: 'I·S·P', auto: 'auto · r2 · live check', ahead: 1, behind: 0, dirty: 0, port: 5250,
      session: { state: 'working', since: null, detail: '' },
    };
    const lines = formatStatusTable([row], Date.now()).split('\n');
    expect(lines[0]).toMatch(/gates\s+auto\s+±main/);
    expect(lines[2]).toMatch(/I·S·P\s+auto · r2 · live check\s+\+1\/-0/);
  });
});

describe('metadataColumns (a sessions row)', () => {
  it('MS2: carries status, gates and the auto summary from the metadata', () => {
    const m = { type: 'fix', status: 'in-review', intent_accepted: '2026-10-24', plan_approved: '2026-10-24', auto_authorized: '2026-10-24', auto_round: '2', auto_stopped: 'live check owed' };
    expect(metadataColumns(m)).toEqual({ status: 'in-review', gates: 'I·P', auto: 'auto · r2 · live check owed' });
  });
  it('is empty for a worktree without an intent', () => {
    expect(metadataColumns(null)).toEqual({ status: null, gates: '', auto: '' });
  });
});

describe('sessionBrief', () => {
  it('tells the session its intent, branch, port and limits', () => {
    const brief = sessionBrief({
      id: '28',
      slug: 'ticket-intake',
      type: 'feature',
      branch: 'feat/28-ticket-intake',
      intentDir: 'intents/28-ticket-intake',
      port: 5228,
      coordinatorPath: 'C:/Users/me/src/product-advice-agent',
    });
    expect(brief).toContain('# You are the session for §28 — ticket-intake');
    expect(brief).toContain('`feat/28-ticket-intake`');
    expect(brief).toContain('if the project runs a dev server, use port 5228');
    expect(brief).not.toMatch(/vite|phaser|npm run dev|--strictPort/i);
    expect(brief).toContain('Nobody edits the queue');
    expect(brief).not.toContain('Do not edit `plan.md`');
    expect(brief).toContain('Do not merge into `main`');
    expect(brief).toContain('never switch branch');
    expect(brief).toContain('main checkout at `C:/Users/me/src/product-advice-agent`');
    expect(brief).toContain('set `status: in-review` in');
    expect(brief).toContain('`intents/28-ticket-intake/` (type: feature)');
  });
});

describe('sessionsData (sessions --json)', () => {
  const now = Date.parse('2026-10-07T12:00:00Z');
  it('gives the table rows as data, in table order, with the age in seconds', () => {
    const rows = [
      {
        id: '27', branch: 'refactor/27-x', path: 'C:/wt/27-x', status: 'in-progress', gates: 'I·P', auto: '',
        ahead: 2, behind: 0, dirty: 3, port: 5227,
        session: { state: 'working', since: '2026-10-07T11:56:00Z', detail: '' },
      },
      {
        id: '30', branch: 'feat/30-y', path: 'C:/wt/30-y', status: 'accepted', gates: 'I·-·-', auto: 'auto · r1',
        ahead: 0, behind: 1, dirty: 0, port: 5230,
        session: { state: 'needs you', since: '2026-10-07T11:59:30Z', detail: 'Claude needs permission' },
      },
      { id: null, branch: 'main', path: 'C:/repo', session: { state: 'no events', since: null, detail: '' } },
    ];
    expect(sessionsData(rows, now)).toEqual([
      {
        id: '30', branch: 'feat/30-y', path: 'C:/wt/30-y', status: 'accepted', gates: 'I·-·-', auto: 'auto · r1',
        ahead: 0, behind: 1, dirty: 0, port: 5230,
        session: { state: 'needs you', since: '2026-10-07T11:59:30Z', ageSeconds: 30, detail: 'Claude needs permission' },
      },
      {
        id: '27', branch: 'refactor/27-x', path: 'C:/wt/27-x', status: 'in-progress', gates: 'I·P', auto: '',
        ahead: 2, behind: 0, dirty: 3, port: 5227,
        session: { state: 'working', since: '2026-10-07T11:56:00Z', ageSeconds: 240, detail: '' },
      },
      {
        id: null, branch: 'main', path: 'C:/repo', status: null, gates: '', auto: '',
        ahead: null, behind: null, dirty: null, port: null,
        session: { state: 'no events', since: null, ageSeconds: null, detail: '' },
      },
    ]);
  });
});
