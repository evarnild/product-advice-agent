import { describe, it } from 'node:test';
import { parseGate, parseMetadata } from './intent-check-lib.mjs';
import { blockerState, findCycles, isMerged, openChain, parseBlockers } from './blockers-lib.mjs';
import { expect } from './expect.mjs';

describe('parseBlockers', () => {
  it('reads id and reason', () => {
    const md = parseMetadata('id: 15\nblocked_by:\n  - 13    its check is extended (spec B4)\n  - 14    the cases need it\n');
    expect(parseBlockers(md, '15')).toEqual({
      items: [
        { id: '13', reason: 'its check is extended (spec B4)' },
        { id: '14', reason: 'the cases need it' },
      ],
      problems: [],
      notes: [],
    });
  });
  it('accepts an item without a reason, with a note', () => {
    expect(parseBlockers(parseMetadata('blocked_by:\n  - 13\n'), '15')).toEqual({ items: [{ id: '13', reason: '' }], problems: [], notes: ['blocked_by item "13": no reason given.'] });
  });
  it('normalises 013 to 13', () => {
    expect(parseBlockers(parseMetadata('blocked_by:\n  - 013    r\n'), '15').items).toEqual([{ id: '13', reason: 'r' }]);
  });
  it('no field or empty means no blockers', () => {
    expect(parseBlockers(parseMetadata('id: 1\n'), '1')).toEqual({ items: [], problems: [], notes: [] });
    expect(parseBlockers(parseMetadata('blocked_by:\n'), '1')).toEqual({ items: [], problems: [], notes: [] });
  });
  it('names a non-digit id and a self id as problems', () => {
    const r = parseBlockers(parseMetadata('blocked_by:\n  - x    why\n  - 18    me\n  - 13    ok\n'), '18');
    expect(r.items).toEqual([{ id: '13', reason: 'ok' }]);
    expect(r.problems).toEqual([
      'blocked_by item "x    why": "x" is not an intent id (digits).',
      'blocked_by item "18    me": an intent cannot block itself.',
    ]);
  });
  it('is not a gate: gates of a blocked intent still parse', () => {
    const md = parseMetadata('plan_approved: 2026-11-13 by-agent\nblocked_by:\n  - 13    r\n');
    expect(parseGate(md.plan_approved)).toEqual({ state: 'recorded', date: '2026-11-13', by: 'agent' });
  });
});

describe('blockerState', () => {
  const metas = { 13: { merged: 'abc1234' }, 14: { merged: '' } };
  const of = (id) => metas[id] ?? null;
  it('an empty merged: line parsed from text is open', () => {
    expect(isMerged(parseMetadata('id: 14\nmerged:\n'))).toBe(false);
    expect(blockerState('14', () => parseMetadata('id: 14\nmerged:\n'))).toBe('open');
    expect(blockerState('14', () => parseMetadata('merged: abc1234\n'))).toBe('cleared');
  });
  it('main merged is cleared; main empty is open', () => {
    expect(blockerState('13', of)).toBe('cleared');
    expect(blockerState('14', of)).toBe('open');
  });
  it('an id only on a branch is open; an id nowhere is unknown', () => {
    expect(blockerState('20', of, (id) => id === '20')).toBe('open');
    expect(blockerState('21', of)).toBe('unknown');
  });
});

describe('openChain', () => {
  const graph = { 17: ['15'], 15: ['13', '14'], 14: ['13'], 13: [] };
  it('follows chains, each id once', () => {
    expect(openChain('17', graph, () => true)).toEqual({ direct: ['15'], further: ['13', '14'] });
    expect(openChain('15', graph, () => true)).toEqual({ direct: ['13', '14'], further: [] });
  });
  it('drops cleared links', () => {
    expect(openChain('17', graph, (id) => id !== '14')).toEqual({ direct: ['15'], further: ['13'] });
    expect(openChain('17', graph, (id) => id !== '15')).toEqual({ direct: [], further: [] });
  });
  it('lists each id once and in ascending order whatever the item order', () => {
    const g = { 20: ['9', '3', '9'], 9: ['5', '4'], 3: ['5', '4'], 5: [], 4: [] };
    expect(openChain('20', g, () => true)).toEqual({ direct: ['3', '9'], further: ['4', '5'] });
  });
  it('orders ids numerically, not lexically', () => {
    const g = { 20: ['13', '9'], 13: ['100', '12'], 9: [], 100: [], 12: [] };
    expect(openChain('20', g, () => true)).toEqual({ direct: ['9', '13'], further: ['12', '100'] });
  });
  it('terminates on a cycle', () => {
    expect(openChain('17', { 17: ['15'], 15: ['17'] }, () => true)).toEqual({ direct: ['15'], further: [] });
  });
});

describe('findCycles', () => {
  it('reports a cycle once', () => {
    expect(findCycles({ 17: ['15'], 15: ['17'] })).toEqual([['15', '17']]);
  });
  it('none in a chain', () => {
    expect(findCycles({ 17: ['15'], 15: ['13'] })).toEqual([]);
  });
});
