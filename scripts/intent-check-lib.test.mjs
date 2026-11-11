import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import {
  ADJUSTMENT_LIMITS,
  checkChange,
  formatResult,
  parseArgs,
  parseAuto,
  parseBranch,
  parseGate,
  parseMetadata,
  parseReviewHeader,
} from './intent-check-lib.mjs';

const meta = (over = {}) => ({
  id: '27',
  type: 'fix',
  status: 'in-progress',
  intent_accepted: '2026-10-07',
  plan_approved: '2026-10-07',
  ...over,
});

const base = (over = {}) => ({
  branch: 'fix/27-drift-log',
  metadata: meta(),
  intentDir: 'intents/27-drift-log',
  intentFiles: ['intent.md', 'plan.md', 'metadata.yml'],
  diff: [
    { path: 'src/advisor/agent.py', added: 4, deleted: 1 },
    { path: 'tests/test_agent.py', added: 20, deleted: 0 },
  ],
  ...over,
});

describe('parseBranch', () => {
  it('reads prefix, type, id and slug', () => {
    expect(parseBranch('feat/27-ticket-intake')).toEqual({ prefix: 'feat', type: 'feature', id: '27', slug: 'ticket-intake' });
    expect(parseBranch('codex/adjust/3-copy')).toMatchObject({ type: 'adjustment', id: '3' });
  });

  it('returns null for branches without an intent id', () => {
    for (const b of ['main', 'stable', 'feat/ticket-intake', 'worktree-agent-a164fba', 'chore/27-x']) {
      expect(parseBranch(b)).toBeNull();
    }
  });
});

describe('parseMetadata', () => {
  it('reads scalars, quoted values, comments and lists', () => {
    const m = parseMetadata(
      ['id: 27', 'type: "fix"   # declared', '# a comment', 'intent_accepted: ', 'links:', '  - plan-history.md#19', "  - 'intents/26-x'", 'status: draft'].join('\r\n'),
    );
    expect(m).toEqual({ id: '27', type: 'fix', intent_accepted: [], links: ['plan-history.md#19', 'intents/26-x'], status: 'draft' });
  });
});

describe('checkChange', () => {
  it('passes a well-formed fix', () => {
    const r = checkChange(base());
    expect(r.errors).toEqual([]);
    expect(r.routes).toEqual([]);
    expect(formatResult(r).verdict).toBe('PASS');
  });

  it('fails a branch with no intent id', () => {
    const r = checkChange(base({ branch: 'feat/ticket-intake' }));
    expect(formatResult(r).verdict).toBe('FAIL');
    expect(r.errors[0]).toMatch(/carries no intent id/);
  });

  it('fails when the intent folder is missing', () => {
    const r = checkChange(base({ metadata: null, intentDir: null }));
    expect(r.errors[0]).toMatch(/No intents\/27-\*/);
  });

  it('fails when branch prefix and declared type disagree', () => {
    const r = checkChange(base({ branch: 'feat/27-drift-log' }));
    expect(r.errors.join()).toMatch(/says feature, but .* declares fix/);
  });

  it('fails when the metadata id differs from the branch id', () => {
    const r = checkChange(base({ metadata: meta({ id: '28' }) }));
    expect(r.errors.join()).toMatch(/does not match branch id/);
  });

  it('fails an unknown type', () => {
    const r = checkChange(base({ metadata: meta({ type: 'chore' }) }));
    expect(r.errors.join()).toMatch(/not one of/);
  });

  it('requires the artefacts the type needs', () => {
    const r = checkChange(base({ branch: 'feat/27-drift-log', metadata: meta({ type: 'feature', spec_accepted: '2026-10-07' }) }));
    expect(r.errors).toContain('feature intents need intents/27-drift-log/spec.md.');
  });

  it('treats a missing gate as an error only once source code changed', () => {
    const noPlan = meta({ plan_approved: [] });
    const withCode = checkChange(base({ metadata: noPlan }));
    expect(withCode.errors.join()).toMatch(/plan_approved.*Code changed before the gate/);

    const artefactsOnly = checkChange(base({ metadata: noPlan, diff: [{ path: 'intents/27-drift-log/plan.md', added: 40, deleted: 0 }] }));
    expect(artefactsOnly.errors).toEqual([]);
    expect(artefactsOnly.notes.join()).toMatch(/plan_approved/);
  });

  it('routes a fix that carries no test', () => {
    const r = checkChange(base({ diff: [{ path: 'web/tooltip.ts', added: 3, deleted: 1 }] }));
    expect(formatResult(r).verdict).toBe('ROUTE');
    expect(r.routes.join()).toMatch(/no test changed/);
  });

  it('routes an adjustment that outgrew its blast radius', () => {
    const adj = { branch: 'adjust/27-copy', metadata: meta({ type: 'adjustment' }), intentFiles: ['intent.md', 'metadata.yml'] };
    const small = checkChange(base({ ...adj, diff: [{ path: 'README.md', added: 5, deleted: 5 }] }));
    expect(small.routes).toEqual([]);

    const big = checkChange(base({ ...adj, diff: [{ path: 'web/session.ts', added: 50, deleted: 20 }] }));
    expect(big.routes.join()).toMatch(/70 lines/);

    const files = Array.from({ length: 6 }, (_, i) => ({ path: `docs/a${i}.md`, added: 1, deleted: 0 }));
    expect(checkChange(base({ ...adj, diff: files })).routes.join()).toMatch(/6 files/);

    const rules = checkChange(base({ ...adj, diff: [{ path: 'src/advisor/catalogue.py', added: 1, deleted: 1 }] }));
    expect(rules.routes.join()).toMatch(/core code/);
  });

  it('does not count intents/ artefacts toward the adjustment limits', () => {
    const r = checkChange(
      base({
        branch: 'adjust/27-copy',
        metadata: meta({ type: 'adjustment' }),
        intentFiles: ['intent.md', 'metadata.yml'],
        diff: [
          { path: 'intents/27-copy/intent.md', added: 200, deleted: 0 },
          { path: 'README.md', added: 2, deleted: 2 },
        ],
      }),
    );
    expect(r.routes).toEqual([]);
  });

  it('routes a refactor that removed test lines', () => {
    const r = checkChange(
      base({
        branch: 'refactor/27-split',
        metadata: meta({ type: 'refactor' }),
        diff: [
          { path: 'web/Board.ts', added: 10, deleted: 200 },
          { path: 'tests/test_guardrails.py', added: 0, deleted: 12 },
        ],
      }),
    );
    expect(r.routes.join()).toMatch(/existing tests lost lines \(tests\/test_guardrails.py\)/);
  });

  it('routes a feature that changed core code without a test', () => {
    const r = checkChange(
      base({
        branch: 'feat/27-x',
        metadata: meta({ type: 'feature', spec_accepted: '2026-10-07' }),
        intentFiles: ['intent.md', 'spec.md', 'plan.md', 'metadata.yml'],
        diff: [{ path: 'src/advisor/guardrails.py', added: 30, deleted: 2 }],
      }),
    );
    expect(r.routes.join()).toMatch(/Core code .* no test change/);
  });
});

describe('parseMetadata edge cases', () => {
  it('keeps a # inside a quoted value and treats [] as an empty list', () => {
    const m = parseMetadata(['title: "Fix #12 overlap"  # trailing comment', "note: 'a # b'", 'links: []', 'tag: a#b'].join('\n'));
    expect(m.title).toBe('Fix #12 overlap');
    expect(m.note).toBe('a # b');
    expect(m.links).toEqual([]);
    expect(m.tag).toBe('a#b');
  });

  it('treats an apostrophe inside an unquoted value as a letter', () => {
    expect(parseMetadata("title: it's fine  # trailing").title).toBe("it's fine");
  });
});

describe('gates must hold a date', () => {
  it('treats an empty gate as not recorded, an error once code changed', () => {
    const r = checkChange(base({ metadata: meta({ plan_approved: [] }) }));
    expect(r.errors.join()).toMatch(/plan_approved.*Code changed before the gate/);
  });

  for (const value of ['~', 'null', 'TBD', 'no', '2026-10', 'x2026-10-07', '2026-10-07x', 'approved 2026-10-07']) {
    it(`rejects plan_approved: ${JSON.stringify(value)} as malformed, code or no code`, () => {
      for (const diff of [base().diff, [{ path: 'README.md', added: 1, deleted: 0 }]]) {
        const r = checkChange(base({ metadata: meta({ plan_approved: value }), diff }));
        expect(r.errors.join()).toMatch(/plan_approved must be empty/);
        expect(r.errors).toHaveLength(1);
      }
    });
  }

  it('passes gates recorded with the by-agent marker, with code changed', () => {
    const r = checkChange(base({ metadata: meta({ intent_accepted: '2026-10-20 by-agent', plan_approved: '2026-10-20 by-agent' }) }));
    expect(r.errors).toEqual([]);
  });

  it('fails a malformed gate that the type does not need, naming the field', () => {
    const r = checkChange(base({ metadata: meta({ spec_accepted: '2026-10-20 by-claude' }) }));
    expect(r.errors.join()).toMatch(/spec_accepted must be empty/);
  });
});

describe('parseGate', () => {
  it('reads a bare date as the owner', () => {
    expect(parseGate('2026-10-20')).toEqual({ state: 'recorded', date: '2026-10-20', by: 'owner' });
  });
  it('reads the by-agent token as an agent', () => {
    expect(parseGate('2026-10-20 by-agent')).toEqual({ state: 'recorded', date: '2026-10-20', by: 'agent' });
  });
  it('reads absent and empty as empty, not malformed', () => {
    expect(parseGate([])).toEqual({ state: 'empty' });
    expect(parseGate(undefined)).toEqual({ state: 'empty' });
  });
  for (const value of ['yes', 'TBD', '2026-1-2', '2026-10-20 by-claude', '2026-10-20by-agent', 'by-agent', '2026-10-20 by-agent ', ['x']]) {
    it(`reads ${JSON.stringify(value)} as malformed`, () => {
      expect(parseGate(value).state).toBe('malformed');
    });
  }
});

describe('type shape boundaries', () => {
  const adj = { branch: 'adjust/27-copy', metadata: meta({ type: 'adjustment' }), intentFiles: ['intent.md', 'metadata.yml'] };
  const files = (n) => Array.from({ length: n }, (_, i) => ({ path: `docs/a${i}.md`, added: 1, deleted: 0 }));

  it('allows an adjustment exactly at the limits, routes one past them', () => {
    expect(checkChange(base({ ...adj, diff: files(ADJUSTMENT_LIMITS.files) })).routes).toEqual([]);
    expect(checkChange(base({ ...adj, diff: files(ADJUSTMENT_LIMITS.files + 1) })).routes).toHaveLength(1);
    const lines = (n) => [{ path: 'README.md', added: n, deleted: 0 }];
    expect(checkChange(base({ ...adj, diff: lines(ADJUSTMENT_LIMITS.lines) })).routes).toEqual([]);
    expect(checkChange(base({ ...adj, diff: lines(ADJUSTMENT_LIMITS.lines + 1) })).routes).toHaveLength(1);
  });

  it('routes a refactor that removed even one test line', () => {
    const r = checkChange(
      base({ branch: 'refactor/27-split', metadata: meta({ type: 'refactor' }), diff: [{ path: 'tests/test_guardrails.py', added: 1, deleted: 1 }] }),
    );
    expect(r.routes).toHaveLength(1);
  });

  it('does not ask a fix for a test while only its artefacts have changed', () => {
    const r = checkChange(base({ diff: [{ path: 'intents/27-drift-log/plan.md', added: 30, deleted: 0 }] }));
    expect(r.routes).toEqual([]);
  });
});

describe('parseArgs', () => {
  it('reads a branch with or without --base', () => {
    expect(parseArgs([])).toEqual({ branch: null, base: 'main' });
    expect(parseArgs(['main'])).toEqual({ branch: 'main', base: 'main' });
    expect(parseArgs(['fix/27-x', '--base', 'stable'])).toEqual({ branch: 'fix/27-x', base: 'stable' });
    expect(parseArgs(['--base', 'stable', 'fix/27-x'])).toEqual({ branch: 'fix/27-x', base: 'stable' });
    expect(parseArgs(['--base=stable'])).toEqual({ branch: null, base: 'stable' });
  });

  it('rejects a missing --base value, unknown flags and extra arguments', () => {
    expect(() => parseArgs(['--base'])).toThrow(/needs a value/);
    expect(() => parseArgs(['--base', '--x'])).toThrow(/needs a value/);
    expect(() => parseArgs(['--base='])).toThrow(/needs a value/);
    expect(() => parseArgs(['--bsae', 'main'])).toThrow(/Unknown option/);
    expect(() => parseArgs(['a', 'b'])).toThrow(/at most one branch/);
  });
});

describe('parseReviewHeader', () => {
  const report = [
    '<!-- generated-by: product-advice-agent/review@0.1.0 -->',
    '# §27 review — thing',
    '',
    'verdict: attest',
    'tier: attested',
    'live-check: not-needed',
    '',
    '## Findings',
    '- live-check: owed',
    'live-check: owed',
    'type-check: FAIL',
    '',
    '# Round 1 (history)',
    'live-check: owed',
    '- verdict: rework',
  ].join('\n');

  it("reads the current round's header fields", () => {
    expect(parseReviewHeader(report)).toEqual({ verdict: 'attest', tier: 'attested', 'live-check': 'not-needed' });
  });

  it('ignores everything from the first ## section or # Round heading on', () => {
    const h = parseReviewHeader(report.replace('live-check: not-needed\n', ''));
    expect(h['live-check']).toBeUndefined();
  });

  it('stops at # Round even in a report with no ## sections', () => {
    expect(parseReviewHeader('verdict: attest\n# Round 1 (history)\nlive-check: owed\n')).toEqual({ verdict: 'attest' });
  });

  it('reads CRLF reports and strips trailing whitespace', () => {
    expect(parseReviewHeader('verdict: escalate  \r\nlive-check: owed\r\n')).toEqual({ verdict: 'escalate', 'live-check': 'owed' });
  });
});

describe('live checks', () => {
  const featureMeta = (over = {}) =>
    meta({ type: 'feature', spec_accepted: '2026-10-07', ...over });
  const feature = (over = {}) =>
    base({
      branch: 'feat/27-drift-log',
      metadata: featureMeta(),
      intentFiles: ['intent.md', 'spec.md', 'plan.md', 'metadata.yml', 'review.md'],
      ...over,
    });

  it('fails a change whose review owes a live check that is not recorded', () => {
    const r = checkChange(feature({ review: { 'live-check': 'owed' } }));
    expect(r.errors.join()).toMatch(/live check is owed.*intents\/27-drift-log\/review\.md → ## Live check/);
  });

  it('fails an owed live check even when no source code changed', () => {
    const r = checkChange(feature({ review: { 'live-check': 'owed' }, diff: [{ path: 'README.md', added: 1, deleted: 0 }] }));
    expect(r.errors.join()).toMatch(/live check is owed/);
  });

  it('reads an empty live_checked: field as not recorded, not as invalid', () => {
    const empty = featureMeta({ live_checked: [] });
    expect(checkChange(feature({ review: { 'live-check': 'not-needed' }, metadata: empty })).errors).toEqual([]);
    expect(checkChange(feature({ review: { 'live-check': 'owed' }, metadata: empty })).errors.join()).toMatch(/live check is owed/);
  });

  it('passes an owed live check recorded with by-agent', () => {
    const r = checkChange(feature({ review: { 'live-check': 'owed' }, metadata: featureMeta({ live_checked: '2026-10-20 by-agent' }) }));
    expect(r.errors).toEqual([]);
  });

  it('passes once live_checked holds a date', () => {
    const r = checkChange(feature({ review: { 'live-check': 'owed' }, metadata: featureMeta({ live_checked: '2026-10-09' }) }));
    expect(r.errors).toEqual([]);
  });

  for (const value of ['yes', 'done', '2026-10', ['2026-10-09'], '~']) {
    it(`fails live_checked: ${JSON.stringify(value)} whatever the review says`, () => {
      for (const review of [null, { 'live-check': 'not-needed' }, { 'live-check': 'owed' }]) {
        const r = checkChange(feature({ review, metadata: featureMeta({ live_checked: value }) }));
        expect(r.errors.join()).toMatch(/live_checked.*YYYY-MM-DD/);
        expect(r.errors).toHaveLength(1); // the date error alone, not also "owed"
      }
    });
  }

  it('adds nothing when no live check is needed or there is no review yet', () => {
    expect(checkChange(feature({ review: { 'live-check': 'not-needed' } })).errors).toEqual([]);
    expect(checkChange(feature({ review: null })).errors).toEqual([]);
    expect(checkChange(feature({ review: { verdict: 'attest' } })).errors).toEqual([]);
    expect(checkChange(feature()).errors).toEqual([]);
  });

  it('fails an unknown live-check value instead of reading it as not needed', () => {
    const r = checkChange(feature({ review: { 'live-check': 'owned' } }));
    expect(r.errors.join()).toMatch(/live-check: "owed" or "not-needed"/);
  });

  it('reports a bad date and a bad live-check value together, not just the first', () => {
    const r = checkChange(feature({ review: { 'live-check': 'owned' }, metadata: featureMeta({ live_checked: 'yes' }) }));
    expect(r.errors).toHaveLength(2);
  });

  it('fails a bare live-check: line, a half-written report, instead of reading it as nothing owed', () => {
    const r = checkChange(feature({ review: { 'live-check': '' } }));
    expect(r.errors.join()).toMatch(/live-check: "owed" or "not-needed"/);
  });
});

describe('language-neutral path rules', () => {
  it('counts pytest, Go and test-directory files as tests', () => {
    for (const path of ['src/advisor/test_agent.py', 'src/advisor/agent_test.py', 'pkg/router_test.go', 'tests/e2e/smoke.py', 'web/router.spec.tsx']) {
      expect(checkChange(base({ diff: [{ path: 'src/advisor/agent.py', added: 4, deleted: 1 }, { path, added: 9, deleted: 0 }] })).routes, path).toEqual([]);
    }
  });

  it('narrowed CORE_CODE: wiring and I/O modules are not core, the model interface is', () => {
    const feature = (path) =>
      base({
        branch: 'feat/27-x',
        metadata: meta({ type: 'feature', spec_accepted: '2026-10-07' }),
        intentFiles: ['intent.md', 'spec.md', 'plan.md', 'metadata.yml'],
        diff: [{ path, added: 4, deleted: 1 }],
      });
    for (const path of ['src/advisor/cli.py', 'src/advisor/config.py', 'src/advisor/tracing.py', 'src/advisor/prompts/system.md', 'src/advisor/evals/run.py']) {
      expect(checkChange(feature(path)).routes, path).toEqual([]);
    }
    for (const path of ['src/advisor/agent.py', 'src/advisor/catalogue.py', 'src/advisor/guardrails.py', 'src/advisor/models/anthropic_model.py', 'src/advisor/evals/cases.py', 'src/advisor/evals/score.py']) {
      expect(checkChange(feature(path)).routes.join(), path).toMatch(/Core code .* no test change/);
    }
  });

  it('treats a config file outside src/ as code arriving before its gate', () => {
    const r = checkChange(base({ metadata: meta({ plan_approved: [] }), diff: [{ path: 'pyproject.toml', added: 12, deleted: 0 }] }));
    expect(r.errors.join()).toMatch(/plan_approved.*Code changed before the gate/);
  });

  it('does not treat docs, markdown or tests written before the plan as code', () => {
    const diff = [
      { path: 'docs/architecture.md', added: 30, deleted: 0 },
      { path: 'README.md', added: 3, deleted: 0 },
      { path: 'tests/test_intake.py', added: 20, deleted: 0 },
    ];
    expect(checkChange(base({ metadata: meta({ plan_approved: [] }), diff })).errors).toEqual([]);
  });
});

describe('auto fields', () => {
  const withAuto = (over) => checkChange(base({ metadata: meta(over) }));

  it('T1: parseAuto reads a date, a date plus by-agent, and empty', () => {
    expect(parseAuto({ auto_authorized: '2026-10-24' }).authorized).toEqual({ state: 'recorded', date: '2026-10-24', by: 'owner' });
    expect(parseAuto({ auto_authorized: '2026-10-24 by-agent' }).authorized).toEqual({ state: 'recorded', date: '2026-10-24', by: 'agent' });
    expect(parseAuto({}).authorized).toEqual({ state: 'empty' });
    expect(parseAuto({ auto_authorized: [] }).authorized).toEqual({ state: 'empty' });
  });

  for (const value of ['yes', '2026-10-24 by-auto', '2026-1-2']) it(`T1: parseAuto reads ${JSON.stringify(value)} as malformed`, () => {
    expect(parseAuto({ auto_authorized: value }).authorized.state).toBe('malformed');
  });

  it('T1: parseAuto reads the round and the reason', () => {
    expect(parseAuto({ auto_round: '2', auto_stopped: 'live check owed' })).toMatchObject({ round: 2, stopped: 'live check owed' });
    expect(parseAuto({ auto_round: [], auto_stopped: [] })).toMatchObject({ round: null, stopped: null });
  });

  it('T2: a malformed auto_authorized is an error naming the field', () => {
    const r = withAuto({ auto_authorized: 'yes' });
    expect(r.errors.join('\n')).toMatch(/auto_authorized must be empty, a YYYY-MM-DD date/);
    expect(withAuto({ auto_authorized: '2026-10-24 by-agent' }).errors).toEqual([]);
  });

  for (const value of ['4', '0', 'two', '1.5', '-1']) it(`T2: auto_round ${JSON.stringify(value)} is an error`, () => {
    expect(withAuto({ auto_round: value }).errors.join('\n')).toMatch(/auto_round must be a whole number from 1 to 3/);
  });

  for (const value of ['1', '2', '3']) it(`T2: auto_round ${value} passes`, () => {
    expect(withAuto({ auto_round: value }).errors).toEqual([]);
  });

  it('T2: an intent with no auto fields is unaffected', () => {
    expect(checkChange(base()).errors).toEqual([]);
    expect(withAuto({ auto_authorized: [], auto_round: [], auto_stopped: [] }).errors).toEqual([]);
  });

  it('T3: the gate grammar did not widen', () => {
    expect(parseGate('2026-10-24 by-auto').state).toBe('malformed');
    expect(parseGate('2026-10-24 by-agent').state).toBe('recorded');
    // and auto_authorized is not a gate: an empty one never blocks code
    expect(withAuto({}).errors).toEqual([]);
  });

  it('T4: a comment is stripped from auto_stopped, so the skill writes reasons without " #"', () => {
    expect(parseMetadata('auto_stopped: live check owed  # note\n').auto_stopped).toBe('live check owed');
    expect(parseMetadata('auto_stopped: live check owed\n').auto_stopped).toBe('live check owed');
    expect(parseMetadata('auto_stopped: cut # here\n').auto_stopped).toBe('cut');
  });
});
