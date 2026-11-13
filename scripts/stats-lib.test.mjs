import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import {
  WAIT_CAP_MS,
  agentTag,
  attributeTurn,
  capWait,
  commitsByIntent,
  computeStats,
  duration,
  formatAll,
  formatStats,
  gateGaps,
  grandTotal,
  milestones,
  parseCommitLog,
  phaseAt,
  sessionTurns,
  spread,
  statsJson,
  statsMarkdown,
  usageLines,
} from './stats-lib.mjs';

const SENTINEL = 'SENTINEL-PROMPT-TEXT-7f3a';
const H = 3600 * 1000;
const T0 = Date.parse('2026-11-01T08:00:00Z');
const at = (h) => T0 + h * H;
const iso = (h) => new Date(at(h)).toISOString();
let n = 0;
const commit = (h, subject) => ({ hash: `c${String(n++).padStart(6, '0')}`, ts: at(h), subject });
const log = (...pairs) => pairs.map(([h, s]) => commit(h, s));
const csOf = (id, commits) => commitsByIntent(commits).get(id);

const FULL = (id) =>
  log(
    [0, `§${id}: intent drafted (owner: x)`],
    [1, `§${id}: intent accepted (owner: "yes")`],
    [2, `§${id}: spec drafted (by /spec)`],
    [5, `§${id}: spec accepted (owner: "yes")`],
    [6, `§${id}: plan drafted`],
    [7, `§${id}: plan approved (auto)`],
    [8, `§${id}: pure logic`],
    [10, `§${id}: in-review, progress entry`],
    [11, `§${id}: review round 1 (run: auto): rework`],
    [12, `§${id}: rework round 1 (fix)`],
    [13, `§${id}: review round 2 (run: auto): ready`],
    [14, `§${id}: live check recorded (on the owner's word)`],
    [15, `§${id}: merged (abc1234); status done`],
  );

const span = (m) => Object.fromEntries(m.phases.map((p) => [p.name, (p.end - p.start) / H]));

describe('parseCommitLog', () => {
  it('reads hash, committer time and subject, dropping junk', () => {
    const out = parseCommitLog('abcdef1 1700000000 §3: plan approved (x)\nnot a line\n\n1234567 1700000100 Merge §3: t');
    expect(out).toEqual([
      { hash: 'abcdef1', ts: 1700000000000, subject: '§3: plan approved (x)' },
      { hash: '1234567', ts: 1700000100000, subject: 'Merge §3: t' },
    ]);
    expect(parseCommitLog(undefined)).toEqual([]);
  });
});

describe('milestones (B3, B5)', () => {
  it('spans the full milestone set in order', () => {
    const m = milestones(csOf(7, FULL(7)), 7);
    expect(m.phases.map((p) => p.name)).toEqual(['intent', 'spec', 'plan', 'build', 'review', 'live check', 'ship']);
    expect(span(m)).toEqual({ intent: 1, spec: 4, plan: 2, build: 3, review: 3, 'live check': 1, ship: 1 });
    expect(m.mergedAt).toBe(at(15));
    expect(m.startedAt).toBe(at(0));
  });

  it('merges a missing milestone into the next phase', () => {
    const cs = csOf(7, FULL(7).filter((c) => !/spec accepted/.test(c.subject)));
    const m = milestones(cs, 7);
    expect(m.phases.map((p) => p.name)).toEqual(['intent', 'plan', 'build', 'review', 'live check', 'ship']);
    expect(span(m).plan).toBe(6); // from intent accepted (1) to plan approved (7)
  });

  it('has no spec phase for a fix and counts "drafted and accepted" as intent', () => {
    const cs = csOf(
      4,
      log([0, '§4: intent drafted and accepted (owner: "yes")'], [1, '§4: plan approved (auto)'], [3, '§4: in review; progress entry'], [4, '§4: merged (abc1234); status done']),
    );
    const m = milestones(cs, 4);
    expect(m.phases.map((p) => p.name)).toEqual(['intent', 'plan', 'build', 'ship']);
    expect(span(m).intent).toBe(0);
  });

  it('keeps time monotonic when commits arrive out of order', () => {
    const m = milestones(csOf(2, log([5, '§2: intent accepted'], [3, '§2: spec accepted'], [9, '§2: merged (abc1234)'])), 2);
    for (const p of m.phases) expect(p.end >= p.start).toBe(true);
  });

  it('ends build at the first auto round when there is no in-review commit', () => {
    const cs = csOf(3, log([0, '§3: intent accepted'], [2, '§3: auto round 1'], [4, '§3: review round 1 (x)'], [5, '§3: merged (abc1234)']));
    expect(span(milestones(cs, 3)).build).toBe(2);
  });

  it('gives an unmerged intent an open phase up to now', () => {
    const m = milestones(csOf(5, FULL(5).slice(0, 6)), 5, at(20));
    expect(m.mergedAt).toBeNull();
    expect(m.phases.at(-1)).toMatchObject({ name: 'build', open: true });
    expect(span(m).build).toBe(13);
  });

  it('is empty without commits', () => {
    expect(milestones([], 9).phases).toEqual([]);
  });

  it('puts a time into the phase that contains it, clamped at both ends', () => {
    const m = milestones(csOf(7, FULL(7)), 7);
    expect(phaseAt(m.phases, at(3))).toBe('spec');
    expect(phaseAt(m.phases, at(1))).toBe('spec'); // a boundary belongs to the next phase
    expect(phaseAt(m.phases, at(-5))).toBe('intent');
    expect(phaseAt(m.phases, at(99))).toBe('ship');
    expect(phaseAt([], 1)).toBeNull();
  });
});

describe('agentTag (B2)', () => {
  it('reads the id and phase from the description', () => {
    expect(agentTag('§13 review round 2')).toEqual({ id: 13, phase: 'review' });
    expect(agentTag('§7 implement the plan')).toEqual({ id: 7, phase: 'implement' });
    expect(agentTag('  §7 rework round 1')).toEqual({ id: 7, phase: 'rework' });
  });
  it('treats anything looser as unattributed', () => {
    for (const d of ['review §13', 'Explore the repo', '§13 explore', '§13review', '§ 13 review', 'x §13 review', '', undefined, 42]) expect(agentTag(d)).toBeNull();
  });
});

const line = (o) => JSON.stringify(o);
const asst = (id, ts, model, u) =>
  line({
    type: 'assistant',
    timestamp: ts,
    message: { id, model, content: [{ type: 'text', text: SENTINEL }], usage: { input_tokens: u[0], output_tokens: u[1], cache_read_input_tokens: u[2], cache_creation_input_tokens: u[3] } },
  });

describe('usageLines (B4, B7)', () => {
  it('sums per assistant message once, whatever the number of lines', () => {
    const text = [asst('m1', iso(1), 'opus', [1, 2, 3, 4]), asst('m1', iso(1), 'opus', [1, 2, 3, 4]), asst('m2', iso(2), 'sonnet', [10, 20, 30, 40])].join('\n');
    const r = usageLines(text);
    expect(r.turns.length).toBe(2);
    expect(r.turns[0]).toEqual({ ts: at(1), model: 'opus', usage: { input: 1, output: 2, cacheRead: 3, cacheWrite: 4 } });
    expect(r.skipped).toBe(0);
    expect(r.firstTs).toBe(at(1));
    expect(r.lastTs).toBe(at(2));
  });

  it('skips and counts garbage and unknown shapes, never throws', () => {
    const text = [
      'not json',
      '{"truncated":',
      '[1,2]',
      'null',
      line({ type: 'assistant', timestamp: iso(1), message: { id: 'a', model: 'opus' } }), // no usage
      line({ type: 'assistant', timestamp: iso(1), message: { id: 'b', model: 'opus', usage: { input_tokens: 'many' } } }),
      line({ type: 'assistant', message: { id: 'c', model: 'opus', usage: { input_tokens: 1 } } }), // no timestamp
      line({ type: 'user', timestamp: iso(1), message: { content: SENTINEL } }), // not usage: neither read nor counted
      asst('ok', iso(3), 'opus', [1, 1, 1, 1]),
      '',
    ].join('\n');
    const r = usageLines(text);
    expect(r.skipped).toBe(7);
    expect(r.turns.length).toBe(1);
    expect(usageLines(undefined)).toEqual({ turns: [], firstTs: null, lastTs: null, skipped: 0 });
  });

  it('keeps no text', () => {
    expect(JSON.stringify(usageLines(asst('m', iso(1), 'opus', [1, 1, 1, 1])))).not.toContain(SENTINEL);
  });
});

const ev = (h, event, extra = {}) => ({ ts: iso(h), session: 's1', event, id: null, ...extra });

describe('sessionTurns', () => {
  it('builds turns from prompt to Stop and gaps from Stop to the next prompt', () => {
    const { turns, gaps } = sessionTurns([ev(0, 'UserPromptSubmit', { skill: 'spec', skillId: 17 }), ev(1, 'Stop'), ev(3, 'UserPromptSubmit'), ev(4, 'Stop')]);
    expect(turns.map((t) => [t.start, t.end, t.skillId])).toEqual([[at(0), at(1), 17], [at(3), at(4), null]]);
    expect(gaps).toEqual([{ session: 's1', from: at(1), to: at(3), who: turns[0] }]);
  });

  it('closes a turn at the next prompt when no Stop came, and leaves an unfinished one open', () => {
    const { turns } = sessionTurns([ev(0, 'UserPromptSubmit'), ev(1, 'UserPromptSubmit'), ev(2, 'Stop'), ev(3, 'UserPromptSubmit')]);
    expect(turns.map((t) => t.end)).toEqual([at(1), at(2), Infinity]);
  });

  it("starts a gap at a permission prompt, restarted by the turn's Stop; idle prompts do not count", () => {
    const a = sessionTurns([ev(0, 'UserPromptSubmit'), ev(0.5, 'Notification', { kind: 'permission_prompt' }), ev(1, 'Notification', { kind: 'idle_prompt' }), ev(2, 'Stop'), ev(3, 'UserPromptSubmit')]);
    expect(a.gaps.map((g) => [g.from, g.to])).toEqual([[at(2), at(3)]]);
    const b = sessionTurns([ev(0, 'UserPromptSubmit'), ev(0.5, 'Notification', { kind: 'permission_prompt' }), ev(3, 'UserPromptSubmit')]);
    expect(b.gaps.map((g) => [g.from, g.to])).toEqual([[at(0.5), at(3)]]);
  });

  it('drops events it cannot place', () => {
    expect(sessionTurns([null, {}, { ts: 'x', session: 's', event: 'Stop' }, { ts: iso(0), event: 'Stop' }]).turns).toEqual([]);
  });
});

describe('attributeTurn (B4)', () => {
  const turn = (over) => ({ session: 's1', start: at(10), end: at(11), skill: null, skillId: null, worktreeId: null, ...over });
  const times = (...p) => p.map(([id, h]) => ({ id, ts: at(h) }));
  it('prefers the skill id, then the worktree session, then a single committing intent', () => {
    expect(attributeTurn(turn({ skillId: 3, worktreeId: 4 }), times([5, 10.5]))).toEqual({ kind: 'intent', id: 3 });
    expect(attributeTurn(turn({ worktreeId: 4 }), times([5, 10.5]))).toEqual({ kind: 'intent', id: 4 });
    expect(attributeTurn(turn(), times([5, 10.5], [5, 10.7], [6, 12]))).toEqual({ kind: 'intent', id: 5 });
  });
  it('reports several intents as shared and none as unattributed, never splitting', () => {
    expect(attributeTurn(turn(), times([6, 10.2], [5, 10.5]))).toEqual({ kind: 'shared', ids: [5, 6] });
    expect(attributeTurn(turn(), times([5, 9], [6, 12]))).toEqual({ kind: 'none' });
  });
});

describe('spread', () => {
  const ph = [{ name: 'a', start: 0, end: 10 }, { name: 'b', start: 10, end: 20 }];
  it('divides a gap over the phases it overlaps, by length', () => {
    expect(spread(ph, 5, 15)).toEqual([['a', 0.5], ['b', 0.5]]);
    expect(spread(ph, 2, 6)).toEqual([['a', 1]]);
    expect(spread(ph, 8, 20)).toEqual([['a', 2 / 12], ['b', 10 / 12]]);
  });
  it('gives time outside every phase to the nearest one, and a zero-length gap to the phase it falls in', () => {
    expect(spread(ph, 15, 30)).toEqual([['b', 1]]);
    expect(spread(ph, -10, 5)).toEqual([['a', 1]]);
    expect(spread(ph, 12, 12)).toEqual([['b', 1]]);
    expect(spread([], 1, 5)).toEqual([['unphased', 1]]);
  });
});

describe('owner wait (B6)', () => {
  it('caps a gap at 2 h with the excess as idle, to the boundary', () => {
    expect(capWait(3 * H)).toEqual({ wait: 2 * H, idle: 1 * H });
    expect(capWait(WAIT_CAP_MS)).toEqual({ wait: 2 * H, idle: 0 });
    expect(capWait(WAIT_CAP_MS + 1)).toEqual({ wait: 2 * H, idle: 1 });
    expect(capWait(WAIT_CAP_MS - 1)).toEqual({ wait: 2 * H - 1, idle: 0 });
    expect(capWait(0)).toEqual({ wait: 0, idle: 0 });
  });
  it('takes agent time out of a gap before capping', () => {
    expect(capWait(3 * H, 2 * H)).toEqual({ wait: 1 * H, idle: 0 });
    expect(capWait(1 * H, 5 * H)).toEqual({ wait: 0, idle: 0 });
  });
  it("pairs a stop or drafted commit with the owner's answer", () => {
    const cs = csOf(
      9,
      log(
        [0, '§9: intent drafted (owner: x)'],
        [1, '§9: intent accepted (owner: "yes")'],
        [2, '§9: spec drafted'],
        [2.5, '§9: auto stopped: spec drafted, waiting for spec_accepted'],
        [6, '§9: spec accepted'],
        [6.5, '§9: auto stopped: waiting for 4 to merge'],
        [7, '§9: auto run resumed'],
        [8, '§9: plan drafted'],
        [9, '§9: plan approved'],
      ),
    );
    expect(gateGaps(cs).map((g) => [(g.from - T0) / H, (g.to - T0) / H])).toEqual([[0, 1], [2, 6], [8, 9]]);
  });
  it('counts no gate for "drafted and accepted"', () => {
    expect(gateGaps(csOf(9, log([0, '§9: intent drafted and accepted (owner: "yes")'], [1, '§9: spec drafted'], [2, '§9: spec accepted'])))).toHaveLength(1);
  });
});

describe('computeStats', () => {
  const base = () => ({ commits: [...FULL(7), ...FULL(8).map((c) => ({ ...c, ts: c.ts + 100 * H }))], events: [], coordinators: [], agents: [], now: at(500) });
  const find = (stats, id) => stats.intents.find((i) => i.id === id);
  const phaseOf = (it, name) => it.phases.find((p) => p.name === name);
  const input = (b, src, model) => b[src].get(model)?.input ?? 0;

  it('reports elapsed per phase, each intent on its own wall-clock (B5)', () => {
    const s = computeStats(base());
    expect(find(s, 7).totals.elapsedMs).toBe(15 * H);
    expect(find(s, 8).totals.elapsedMs).toBe(15 * H);
    expect(phaseOf(find(s, 7), 'spec').elapsedMs).toBe(4 * H);
    expect(computeStats({ ...base(), only: [8] }).intents.map((i) => i.id)).toEqual([8]);
  });

  it('attributes tokens by tag, skill id, commits, shared and none, and counts every token once', () => {
    const coordinatorText = [
      asst('a1', iso(2.2), 'opus', [100, 10, 1, 1]), // the /spec 7 turn (2 .. 2.5)
      asst('a1', iso(2.2), 'opus', [100, 10, 1, 1]), // same message, second line
      asst('a2', iso(8.5), 'opus', [200, 20, 2, 2]), // a turn with only a §7 commit inside (8)
      asst('a3', iso(8.6), 'sonnet', [5, 5, 5, 5]),
      asst('a4', iso(20.5), 'opus', [30, 0, 0, 0]), // a turn with no commit inside
      asst('a5', iso(50), 'opus', [1000, 0, 0, 0]), // no turn at all
      asst('a6', iso(15.2), 'opus', [60, 0, 0, 0]), // outside every turn
    ].join('\n');
    const agentText = [asst('g1', iso(9), 'opus', [300, 30, 3, 3]), asst('g2', iso(9.5), 'opus', [400, 40, 4, 4])].join('\n');
    const strayAgent = asst('g3', iso(9), 'sonnet', [7, 7, 7, 7]);
    const reworkAgent = asst('g4', iso(12), 'opus', [11, 0, 0, 0]);
    // intent 8's commits are 100 h later; add a 8-commit inside the "shared" turn
    const commits = [...base().commits, ...log([115.1, '§8: extra'], [115.2, '§7: extra'])];
    const events = [
      ev(2, 'UserPromptSubmit', { skill: 'spec', skillId: 7 }),
      ev(2.5, 'Stop'),
      ev(7.9, 'UserPromptSubmit'),
      ev(8.9, 'Stop'),
      ev(20, 'UserPromptSubmit'),
      ev(21, 'Stop'),
      ev(115, 'UserPromptSubmit'),
      ev(116, 'Stop'),
    ];
    const coordinatorWithShared = `${coordinatorText}\n${asst('a7', iso(115.5), 'opus', [70, 0, 0, 0])}`;
    const s = computeStats({
      ...base(),
      commits,
      events,
      coordinators: [{ file: 'main.jsonl', session: 's1', usage: usageLines(coordinatorWithShared) }],
      agents: [
        { file: 'agent-1.jsonl', session: 's1', description: '§7 implement the plan', usage: usageLines(agentText) },
        { file: 'agent-2.jsonl', session: 's1', description: 'Explore', usage: usageLines(strayAgent) },
        { file: 'agent-3.jsonl', session: 's1', description: '§7 rework round 1', usage: usageLines(reworkAgent) },
      ],
    });
    const i7 = find(s, 7);
    expect(input(phaseOf(i7, 'spec').tokens, 'coordinator', 'opus')).toBe(100); // by skillId, the duplicate line counted once
    expect(input(phaseOf(i7, 'build').tokens, 'coordinator', 'opus')).toBe(200); // by the single intent whose commit fell inside
    expect(input(phaseOf(i7, 'build').tokens, 'coordinator', 'sonnet')).toBe(5);
    expect(input(phaseOf(i7, 'build').tokens, 'agents', 'opus')).toBe(700); // by tag, implement -> build
    expect(input(phaseOf(i7, 'review').tokens, 'agents', 'opus')).toBe(11); // rework -> review
    expect(s.shared.get('shared: §7, §8') && input(s.shared.get('shared: §7, §8'), 'coordinator', 'opus')).toBe(70);
    // unattributed: the turn without commits, the message outside any turn, the untagged agent
    expect(input(s.unattributed, 'coordinator', 'opus')).toBe(30 + 1000 + 60);
    expect(input(s.unattributed, 'agents', 'sonnet')).toBe(7);
    // nothing counted twice or lost: the grand total is the sum of the distinct messages
    const expected = [100, 10, 1, 1, 200, 20, 2, 2, 5, 5, 5, 5, 30, 1000, 60, 70, 300, 30, 3, 3, 400, 40, 4, 4, 7, 7, 7, 7, 11].reduce((a, b) => a + b, 0);
    const g = grandTotal(s);
    expect(g.input + g.output + g.cacheRead + g.cacheWrite).toBe(expected);
  });

  it('counts gate wait and in-session wait separately, caps both, and leaves agent time out', () => {
    const commits = log(
      [0, '§7: intent drafted (owner: x)'],
      [0.5, '§7: intent accepted'],
      [1, '§7: spec drafted'],
      [4.5, '§7: spec accepted'], // gate wait of 3.5 h: 2 h counted, 1.5 h idle
      [30, '§7: merged (abc1234)'],
    );
    const events = [
      ev(1, 'UserPromptSubmit', { skill: 'spec', skillId: 7 }),
      ev(1.5, 'Stop'),
      ev(2.5, 'UserPromptSubmit', { skillId: 7 }), // 1 h in-session wait
      ev(3, 'Stop'),
      ev(4.5, 'UserPromptSubmit', { skillId: 7 }), // 1.5 h gap, 1 h of it an agent running: 0.5 h
      ev(5, 'Stop'),
      ev(10, 'UserPromptSubmit', { skillId: 7 }), // 5 h gap, no agent: 2 h counted, 3 h idle
    ];
    const agentSpan = [asst('x1', iso(3.1), 'opus', [1, 1, 1, 1]), asst('x2', iso(4.1), 'opus', [1, 1, 1, 1])].join('\n');
    const s = computeStats({
      commits,
      events,
      coordinators: [],
      agents: [{ file: 'a.jsonl', session: 's1', description: 'Explore', usage: usageLines(agentSpan) }],
      now: at(40),
    });
    const i7 = find(s, 7);
    const spec = phaseOf(i7, 'spec');
    // gate waits: intent drafted(0) -> accepted(0.5) is in the intent phase; spec drafted(1) -> accepted(4.5) is 3.5 h in spec
    expect(phaseOf(i7, 'intent').gateWaitMs).toBe(0.5 * H);
    expect(spec.gateWaitMs).toBe(2 * H);
    expect(spec.idleMs).toBe(1.5 * H);
    // in-session: 1 h (1.5 -> 2.5) and 1.5 h - 1 h agent = 0.5 h (3 -> 4.5), both in spec
    expect(spec.sessionWaitMs).toBe(1.5 * H);
    // 5 h (5 -> 10) in the ship phase: 2 h counted, 3 h idle; agent time is not wait
    const ship = phaseOf(i7, 'ship');
    expect(ship.sessionWaitMs).toBe(2 * H);
    expect(ship.idleMs).toBe(3 * H);
  });

  it('splits a wait that straddles a milestone over the phases it touches', () => {
    const commits = log([0, '§7: intent accepted'], [1, '§7: spec drafted'], [3, '§7: spec accepted'], [4, '§7: plan drafted'], [6, '§7: plan approved'], [9, '§7: merged (abc1234)']);
    // the owner answers the plan after 2 h; a stop at 2.5 h inside the spec/plan boundary is not a gate here
    const events = [ev(2, 'UserPromptSubmit', { skillId: 7 }), ev(2.1, 'Stop'), ev(3.5, 'UserPromptSubmit', { skillId: 7 })];
    const i7 = find(computeStats({ commits, events, coordinators: [], agents: [], now: at(20) }), 7);
    // 2.1 -> 3.5 is 1.4 h: 0.9 h in spec (to 3), 0.5 h in plan (from 3)
    expect(Math.round(phaseOf(i7, 'spec').sessionWaitMs / 1000)).toBe(Math.round(0.9 * H / 1000));
    expect(Math.round(phaseOf(i7, 'plan').sessionWaitMs / 1000)).toBe(Math.round(0.5 * H / 1000));
    expect(Math.round(i7.totals.sessionWaitMs / 1000)).toBe(Math.round(1.4 * H / 1000));
  });

  it('marks partial the intents merged before the cutover', () => {
    const s = computeStats({ ...base(), cutover: at(50) });
    expect(find(s, 7).partial).toBe(true);
    expect(find(s, 8).partial).toBe(false);
    expect(computeStats({ ...base(), cutover: null }).intents.every((i) => i.partial)).toBe(true); // the change is not merged yet
  });

  it('counts skipped lines per file', () => {
    const s = computeStats({
      ...base(),
      coordinators: [{ file: 'main.jsonl', session: 's1', usage: usageLines('junk\nmore junk') }],
      agents: [{ file: 'agent-1.jsonl', session: 's1', description: 'x', usage: usageLines('{') }, { file: 'agent-2.jsonl', session: 's1', description: 'x', usage: usageLines('') }],
    });
    expect(s.skipped).toEqual([{ file: 'main.jsonl', count: 2 }, { file: 'agent-1.jsonl', count: 1 }]);
  });
});

describe('output (B8, B10)', () => {
  const stats = () => {
    const events = [ev(1, 'UserPromptSubmit', { skill: 'spec', skillId: 7 }), ev(2, 'Stop')];
    return computeStats({
      commits: FULL(7),
      events,
      coordinators: [{ file: 'main.jsonl', session: 's1', usage: usageLines([asst('m', iso(1.5), 'claude-opus-x', [1500, 200, 3_000_000, 4]), 'garbage'].join('\n')) }],
      agents: [{ file: 'a.jsonl', session: 's1', description: '§7 review round 1', usage: usageLines(asst('g', iso(11.5), 'claude-sonnet-x', [9, 8, 7, 6])) }],
      now: at(40),
      cutover: at(100),
    });
  };

  it('prints a table per phase with totals, token lines per model and source, and the skipped count', () => {
    const text = formatStats(stats());
    for (const word of ['phase', 'elapsed', 'gate wait', 'in-session', 'idle', 'intent', 'spec', 'live check', 'ship', 'total']) expect(text).toContain(word);
    expect(text).toContain('coordinator claude-opus-x: in 1.5k out 200 cr 3.0M cw 4');
    expect(text).toContain('agents claude-sonnet-x: in 9 out 8 cr 7 cw 6');
    expect(text).toContain('skipped lines: 1');
    expect(text).toContain('main.jsonl: 1');
    expect(text).toContain('partial');
  });

  it('prints one line per intent with --all and marks partial', () => {
    const text = formatAll(stats());
    expect(text).toMatch(/^§7 .*partial$/m);
    expect(text).toMatch(/^total /m);
  });

  it('gives the same data as JSON', () => {
    const j = statsJson(stats());
    expect(j.intents[0].id).toBe(7);
    expect(j.intents[0].partial).toBe(true);
    expect(j.intents[0].phases.find((p) => p.name === 'spec').tokens.coordinator['claude-opus-x'].input).toBe(1500);
    expect(j.skipped).toEqual([{ file: 'main.jsonl', count: 1 }]);
    expect(JSON.parse(JSON.stringify(j))).toEqual(j);
  });

  it('writes a stamped stats.md of numbers and ids only', () => {
    const md = statsMarkdown(stats().intents[0], 'product-advice-agent/ship@0.2.0');
    expect(md.startsWith('<!-- generated-by: product-advice-agent/ship@0.2.0 -->')).toBe(true);
    expect(md).toContain('# §7 stats');
  });

  it('never carries transcript or prompt text', () => {
    const s = stats();
    for (const out of [formatStats(s), formatAll(s), JSON.stringify(statsJson(s)), statsMarkdown(s.intents[0], 'x')]) expect(out).not.toContain(SENTINEL);
  });

  it('formats durations', () => {
    expect(duration(0)).toBe('0s');
    expect(duration(59_000)).toBe('59s');
    expect(duration(60_000)).toBe('1m');
    expect(duration(65 * 60_000)).toBe('1h05m');
  });
});
