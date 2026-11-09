import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { artefactOrigins, gateShares, metadataProblems, qualityByRun, parseReviewFields, qualityByTier, runOf, sampleDue, sampleDueCommand } from './scan-lib.mjs';

const intent = (over = {}) => ({ id: '1', merged: null, gates: {}, ...over });

describe('metadataProblems', () => {
  it('flags a merged: that is not a hash, without asking git', () => {
    let asked = false;
    const p = metadataProblems([intent({ merged: '2026-10-20' }), intent({ id: '2', merged: '--output=x' })], () => ((asked = true), true));
    expect(p.map((x) => [x.id, x.field])).toEqual([['1', 'merged'], ['2', 'merged']]);
    expect(asked).toBe(false);
  });

  it('flags a hash git cannot resolve, and passes one it can', () => {
    expect(metadataProblems([intent({ merged: 'abc1234' })], () => false)).toHaveLength(1);
    expect(metadataProblems([intent({ merged: 'abc1234' })], () => true)).toEqual([]);
  });

  it('flags a malformed gate, naming intent and field, and accepts both recorded forms', () => {
    const gates = { intent_accepted: 'yes', spec_accepted: '2026-10-20', plan_approved: '2026-10-20 by-agent', live_checked: [] };
    const p = metadataProblems([intent({ gates })], () => true);
    expect(p).toHaveLength(1);
    expect(p[0]).toMatchObject({ id: '1', field: 'intent_accepted', value: 'yes' });
  });
});

describe('gateShares', () => {
  it('counts owner and agent per field, ignoring empty and malformed values', () => {
    const f = 'intent_accepted';
    const shares = gateShares([
      intent({ gates: { [f]: '2026-10-20' } }),
      intent({ gates: { [f]: '2026-10-20 by-agent' } }),
      intent({ gates: { [f]: [] } }),
      intent({ gates: { [f]: 'TBD' } }),
    ]);
    expect(shares[f]).toEqual({ owner: 1, agent: 1 });
    expect(shares.live_checked).toEqual({ owner: 0, agent: 0 });
  });
});

describe('artefactOrigins', () => {
  const stamps = (spec, plan) => ({ stamps: { 'intent.md': 'product-advice-agent/intent@0.1.3', ...(spec !== undefined && { 'spec.md': spec }), ...(plan !== undefined && { 'plan.md': plan }) } });

  it('counts a /spec spec and a /build-plan plan as skill-made, any version', () => {
    const o = artefactOrigins([stamps('product-advice-agent/spec@0.1.0', 'product-advice-agent/build-plan@0.1.0'), stamps('product-advice-agent/spec@0.2.0', 'product-advice-agent/build-plan@1.0.0')]);
    expect(o['spec.md']).toEqual({ skill: 2, hand: 0, unstamped: 0 });
    expect(o['plan.md']).toEqual({ skill: 2, hand: 0, unstamped: 0 });
  });

  it('counts an old intent stamp as hand-made and no stamp as unstamped', () => {
    const o = artefactOrigins([stamps('product-advice-agent/intent@0.1.2', 'product-advice-agent/intent@0.1.1'), stamps(null, null)]);
    expect(o['spec.md']).toEqual({ skill: 0, hand: 1, unstamped: 1 });
    expect(o['plan.md']).toEqual({ skill: 0, hand: 1, unstamped: 1 });
  });

  it('does not count a stamp of the other skill as skill-made', () => {
    const o = artefactOrigins([stamps('product-advice-agent/build-plan@0.1.0', 'product-advice-agent/spec@0.1.0')]);
    expect(o['spec.md']).toEqual({ skill: 0, hand: 1, unstamped: 0 });
    expect(o['plan.md']).toEqual({ skill: 0, hand: 1, unstamped: 0 });
  });

  it('does not match a skill name that merely starts with the right one', () => {
    const o = artefactOrigins([stamps('product-advice-agent/spec-x@0.1.0', 'product-advice-agent/build-plan-x@0.1.0')]);
    expect(o['spec.md']).toEqual({ skill: 0, hand: 1, unstamped: 0 });
    expect(o['plan.md']).toEqual({ skill: 0, hand: 1, unstamped: 0 });
  });

  it('counts an intent without the file nowhere', () => {
    const o = artefactOrigins([stamps(undefined, 'product-advice-agent/build-plan@0.1.0')]);
    expect(o['spec.md']).toEqual({ skill: 0, hand: 0, unstamped: 0 });
    expect(o['plan.md']).toEqual({ skill: 1, hand: 0, unstamped: 0 });
  });
});

describe('qualityByTier', () => {
  const rv = (tier, extra = {}) => ({ tier, verdict: 'attest', ...extra });
  const intents = [
    { id: 1, type: 'feature', followsUp: null, review: rv('attested') },
    { id: 2, type: 'refactor', followsUp: null, review: rv('reviewed') },
    { id: 3, type: 'fix', followsUp: null, review: rv('attested') }, // merged before the window
    { id: 4, type: 'adjustment', followsUp: null, review: rv('attested') },
    { id: 5, type: 'feature', followsUp: null, review: null }, // never reviewed
    { id: 10, type: 'fix', followsUp: '2', review: rv('attested') },
    { id: 11, type: 'fix', followsUp: '1', review: rv('attested') },
    { id: 12, type: 'fix', followsUp: '3', review: null },
    { id: 13, type: 'fix', followsUp: '99', review: null },
    { id: 14, type: 'feature', followsUp: '1', review: null },
  ];
  const outsideWindow = new Set([3]);
  const mergedInWindow = (i) => !outsideWindow.has(i.id);
  const reverts = [
    { subject: 'Revert "§4: tweak"' },
    { subject: 'Revert §2 merge' },
    { subject: 'Revert something' },
    { subject: 'Revert §3' },
    { subject: 'Revert § 1' },
  ];

  it('T7: counts changes, follow-ups and reverts per tier (numbers pinned against the pre-move inline code in sdlc-scan.mjs)', () => {
    expect(qualityByTier({ intents, reverts, mergedInWindow })).toEqual({
      attested: { changes: 4, followUps: 1, reverts: 2 },
      reviewed: { changes: 1, followUps: 1, reverts: 1 },
    });
  });
});

describe('qualityByRun', () => {
  // The T7 fixture again, with run kinds: 1 and 10 are auto, 4 says manual,
  // and 2 and 11 predate auto mode (no run: line at all).
  const rv = (tier, run) => ({ tier, verdict: 'attest', ...(run ? { run } : {}) });
  const intents = [
    { id: 1, type: 'feature', followsUp: null, review: rv('attested', 'auto') },
    { id: 2, type: 'refactor', followsUp: null, review: rv('reviewed') },
    { id: 4, type: 'adjustment', followsUp: null, review: rv('attested', 'manual') },
    { id: 10, type: 'fix', followsUp: '2', review: rv('attested', 'auto') },
    { id: 11, type: 'fix', followsUp: '1', review: rv('attested') },
  ];
  const reverts = [{ subject: 'Revert "§4: tweak"' }, { subject: 'Revert §2 merge' }, { subject: 'Revert § 1' }];
  const input = { intents, reverts, mergedInWindow: () => true };

  it('T8: splits changes, follow-ups and reverts by the run kind of the change they name; a missing run: is manual', () => {
    expect(qualityByRun(input)).toEqual({
      auto: { attested: { changes: 2, followUps: 1, reverts: 1 } },
      manual: {
        attested: { changes: 2, followUps: 0, reverts: 1 },
        reviewed: { changes: 1, followUps: 1, reverts: 1 },
      },
    });
  });

  it('T8: the split adds up to the unsplit per-tier numbers', () => {
    const all = qualityByTier(input);
    const { auto, manual } = qualityByRun(input);
    for (const tier of Object.keys(all)) {
      for (const key of ['changes', 'followUps', 'reverts']) {
        expect((auto[tier]?.[key] ?? 0) + (manual[tier]?.[key] ?? 0)).toBe(all[tier][key]);
      }
    }
  });

  it('T8: runOf reads auto, and everything else (missing, manual, junk, no review) as manual', () => {
    expect(runOf({ run: 'auto' })).toBe('auto');
    expect(runOf({ run: 'manual' })).toBe('manual');
    expect(runOf({})).toBe('manual');
    expect(runOf({ run: 'Auto' })).toBe('manual');
    expect(runOf(null)).toBe('manual');
  });
});

describe('sampleDue', () => {
  const att = (run, id) => ({ id, verdict: 'attest', ...(run ? { run } : {}) });
  const autos = (n) => Array.from({ length: n }, (_, k) => att('auto', 100 + k));
  const manuals = (n) => Array.from({ length: n }, (_, k) => att('manual', 200 + k));

  it('T9: every third attested auto change is due, the others are not', () => {
    const due = [0, 1, 2, 3, 4, 5].map((prior) => sampleDue({ reviews: autos(prior), run: 'auto' }));
    expect(due.map((d) => d.nth)).toEqual([1, 2, 3, 4, 5, 6]);
    expect(due.map((d) => d.due)).toEqual([false, false, true, false, false, true]);
  });

  it('T9: every fifth attested manual change is due, the third is not', () => {
    expect(sampleDue({ reviews: manuals(4), run: 'manual' })).toMatchObject({ nth: 5, due: true, every: 5 });
    expect(sampleDue({ reviews: manuals(2), run: 'manual' })).toMatchObject({ nth: 3, due: false });
    expect(sampleDue({ reviews: manuals(9), run: 'manual' })).toMatchObject({ nth: 10, due: true });
  });

  it('T9: the two kinds count separately, and a review with no run: line is manual', () => {
    const reviews = [...autos(2), ...manuals(4), att(null, 300)];
    expect(sampleDue({ reviews, run: 'auto' })).toMatchObject({ nth: 3, due: true });
    expect(sampleDue({ reviews, run: 'manual' })).toMatchObject({ nth: 6, due: false });
  });

  it('T9: escalate, rework and unreadable verdicts do not count', () => {
    const reviews = [
      ...autos(2),
      { id: 1, verdict: 'escalate', run: 'auto' },
      { id: 2, verdict: 'rework', run: 'auto' },
      { id: 3, verdict: null, run: 'auto' },
    ];
    expect(sampleDue({ reviews, run: 'auto' })).toMatchObject({ nth: 3, due: true });
  });

  it('T9: the intent under review is left out, so its earlier rounds are not another change', () => {
    const reviews = [...autos(2), att('auto', 50)];
    expect(sampleDue({ reviews, run: 'auto' }).nth).toBe(4);
    expect(sampleDue({ reviews, run: 'auto', excludeId: '50' }).nth).toBe(3);
    expect(sampleDue({ reviews, run: 'auto', excludeId: 50 }).nth).toBe(3);
  });

  it('refuses a run kind it does not know', () => {
    expect(() => sampleDue({ reviews: [], run: 'bot' })).toThrow(/unknown run kind/);
  });
});

describe('parseReviewFields', () => {
  const review = (...head) => ['<!-- generated-by: product-advice-agent/review@0.1.5 -->', '# §1 review', '', ...head, '', '## Passes', ''].join('\n');
  it('MS1: reads the header fields, run included', () => {
    const f = parseReviewFields(review('verdict: attest', 'tier: attested', 'round: 2', 'sampled: yes', 'run: auto', 'live-check: owed'));
    expect(f).toEqual({ verdict: 'attest', tier: 'attested', round: '2', sampled: 'yes', run: 'auto' });
    expect(parseReviewFields(review('verdict: attest', 'run: manual')).run).toBe('manual');
  });
  it('reads CRLF text', () => {
    expect(parseReviewFields(review('verdict: attest', 'run: auto').replace(/\n/g, '\r\n')).run).toBe('auto');
  });
  it('a review with no run: line has run null, which counts as manual', () => {
    const f = parseReviewFields(review('verdict: attest', 'tier: attested'));
    expect(f.run).toBeNull();
    expect(runOf(f)).toBe('manual');
  });
  it('the template line "run: auto | manual" and other junk are not auto', () => {
    for (const v of ['auto | manual', 'automatic', 'Auto', 'auto manual', '']) {
      const f = parseReviewFields(review('verdict: attest', `run: ${v}`));
      expect(f.run).toBeNull();
      expect(runOf(f)).toBe('manual');
    }
  });
  it('does not take a run: line from the report body', () => {
    expect(parseReviewFields(review('verdict: attest') + 'run: auto\n').run).toBeNull();
  });
});

describe('sampleDueCommand', () => {
  const att = (id, run) => ({ id, review: { verdict: 'attest', tier: 'attested', ...(run ? { run } : {}) } });
  const intents = [att('1', 'auto'), att('2', 'auto'), att('3', 'auto')];
  it('is null without the flag, so the normal scan runs', () => {
    expect(sampleDueCommand(['--json'], intents)).toBeNull();
  });
  it('prints the decision for the next attested change of that kind', () => {
    expect(sampleDueCommand(['--sample-due', 'auto'], intents)).toEqual({
      exit: 0,
      stdout: 'sample-due auto: nth attested auto change = 4, every 3, sampled: no',
    });
    expect(sampleDueCommand(['--sample-due', 'auto'], intents.slice(0, 2)).stdout).toContain('= 3, every 3, sampled: yes');
  });
  it('MS3: --exclude leaves the named intent out', () => {
    expect(sampleDueCommand(['--sample-due', 'auto', '--exclude', '3'], intents).stdout).toContain('= 3, every 3, sampled: yes');
    expect(sampleDueCommand(['--exclude', '3', '--sample-due', 'auto'], intents).stdout).toContain('= 3,');
  });
  it('exits 2 with a usage line when the value is missing or unknown', () => {
    for (const args of [['--sample-due'], ['--sample-due', '--json'], ['--sample-due', 'bot'], ['--sample-due', 'auto', '--exclude'], ['--sample-due', 'auto', '--exclude', '--json']]) {
      const r = sampleDueCommand(args, intents);
      expect(r.exit).toBe(2);
      expect(r.stderr).toMatch(/usage: sdlc:scan -- --sample-due <auto\|manual>/);
      expect(r.stdout).toBeUndefined();
    }
  });
});
