import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { formatQueue, groupIntents, nextId, pickSource, queueData, queueLine } from './queue-lib.mjs';

const entry = (id, status, extra = {}, mergeRank = null, source = 'main') => ({
  id: String(id),
  source,
  mergeRank,
  metadata: { id: String(id), slug: `s${id}`, type: 'fix', title: `Title ${id}`, status, ...extra },
});

describe('groupIntents', () => {
  const all = [
    entry(1, 'accepted'),
    entry(2, 'in-progress'),
    entry(3, 'in-review'),
    entry(4, 'draft'),
    entry(5, 'done'),
    entry(6, 'abandoned'),
    entry(7, 'deferred'),
    entry(8, 'weird'),
  ];
  const ids = (list) => list.map((e) => e.id);

  it('puts one intent of every status in its group', () => {
    const g = groupIntents(all);
    expect(ids(g.inFlight)).toEqual(['1', '2', '3']);
    expect(ids(g.queued)).toEqual(['4']);
    expect(ids(g.shipped)).toEqual(['5']);
    expect(ids(g.stopped)).toEqual(['6', '7']);
    expect(ids(g.other)).toEqual(['8']);
  });

  it('sorts shipped by merge order, newest first, not by id', () => {
    const g = groupIntents([entry(10, 'done', {}, 5), entry(20, 'done', {}, 1), entry(30, 'done', {}, 3)]);
    expect(ids(g.shipped)).toEqual(['20', '30', '10']);
  });

  it('puts shipped of unknown merge order after the known ones, higher id first', () => {
    const g = groupIntents([entry(1, 'done'), entry(2, 'done'), entry(3, 'done', {}, 0)]);
    expect(ids(g.shipped)).toEqual(['3', '2', '1']);
  });
});

describe('pickSource', () => {
  const main = { status: 'accepted' };
  const branch = { status: 'in-review' };
  it('reads an unmerged branch over main', () => {
    expect(pickSource(main, branch, false)).toEqual({ metadata: branch, source: 'branch' });
  });
  it('reads main when the branch is already merged', () => {
    expect(pickSource({ status: 'done' }, branch, true)).toEqual({ metadata: { status: 'done' }, source: 'main' });
  });
  for (const status of ['done', 'abandoned', 'deferred']) it(`reads main when main says ${status}, whatever the unmerged branch says`, () => {
    const m = { status };
    expect(pickSource(m, branch, false)).toEqual({ metadata: m, source: 'main' });
  });
  it('still reads an unmerged branch over a non-terminal main status', () => {
    for (const status of ['draft', 'accepted', 'in-progress', 'in-review']) {
      expect(pickSource({ status }, branch, false).source).toBe('branch');
    }
  });
  it('reads main when there is no branch', () => {
    expect(pickSource(main, null, false)).toEqual({ metadata: main, source: 'main' });
  });
  it('is null when neither side has metadata', () => {
    expect(pickSource(null, null, false)).toBeNull();
  });
});

describe('nextId', () => {
  it('counts an id that exists only on a branch', () => {
    expect(nextId({ overviewText: '§6', ids: ['3', '48'] })).toBe(49);
  });
  it('counts a section only in the overview text', () => {
    expect(nextId({ overviewText: 'see §30 and x §25 y', ids: ['3'] })).toBe(31);
  });
  it('reads §6.13 as 6', () => {
    expect(nextId({ overviewText: '§6.13', ids: [] })).toBe(7);
  });
  it('starts at 1 when there is nothing', () => {
    expect(nextId({})).toBe(1);
    expect(nextId()).toBe(1);
  });
});

describe('queueLine and formatQueue', () => {
  it('shows the hash for shipped only, and the source', () => {
    const done = entry(5, 'done', { merged: 'abc1234', type: 'feature', plan_approved: '2026-10-22' }, 0);
    expect(queueLine(done)).toContain('abc1234');
    expect(queueLine(done)).toContain('main');
    const open = entry(6, 'in-review', { merged: 'abc1234', type: 'feature' }, null, 'branch');
    expect(queueLine(open)).not.toContain('abc1234');
    expect(queueLine(open)).toContain('branch');
    expect(queueLine(open)).toContain('-·-·-');
    expect(queueLine(done)).toContain('-·-·P');
  });

  it('T6: shows the auto summary only for an auto-run intent', () => {
    const auto = entry(6, 'in-progress', { auto_authorized: '2026-10-24 by-agent', auto_round: '1', auto_stopped: 'spec' });
    expect(queueLine(auto)).toContain('auto · r1 · spec');
    expect(queueLine(entry(7, 'in-progress'))).not.toContain('auto');
    expect(queueLine(entry(7, 'in-progress'))).not.toMatch(/ {3,}/); // no empty column left behind
    expect(queueLine(entry(8, 'in-progress', { auto_round: '1', auto_stopped: 'spec' }))).not.toContain('auto');
  });

  it('prints the Stopped group and every heading', () => {
    const text = formatQueue([entry(6, 'abandoned'), entry(1, 'accepted')]);
    expect(text).toMatch(/In flight \(1\)[\s\S]*Queued \(0\)[\s\S]*Shipped \(0\)[\s\S]*Stopped \(1\)\n {2}§6/);
    expect(text).not.toContain('Unrecognised');
  });

  it('gives the same entries as data', () => {
    const data = queueData([entry(3, 'done', { merged: 'abc1234' }, 0), entry(4, 'deferred')]);
    expect(data.shipped[0]).toMatchObject({ id: 3, status: 'done', merged: 'abc1234', source: 'main' });
    expect(data.stopped[0]).toMatchObject({ id: 4, merged: null });
  });

  it('T6: carries auto in the data, empty for a manual intent', () => {
    const data = queueData([entry(6, 'in-progress', { auto_authorized: '2026-10-24', auto_round: '2' }), entry(7, 'in-progress')]);
    expect(data.inFlight.map((e) => e.auto)).toEqual(['auto · r2', '']);
  });
});

describe('blocked_by in the queue', () => {
  const chain = () => [
    entry(13, 'in-progress'),
    entry(14, 'accepted', { blocked_by: ['13    needs the growth'] }),
    entry(15, 'accepted', { blocked_by: ['14    cases on 500 products'] }),
    entry(17, 'accepted', { blocked_by: ['15    reads its reports'] }),
  ];
  const lineOf = (text, id) => text.split(String.fromCharCode(10)).find((l) => l.trim().startsWith(`§${id}  `));

  it('B5: prints direct open blockers, then the chain in parentheses, each once', () => {
    const text = formatQueue(chain());
    expect(lineOf(text, 17)).toContain('  blocked by §15 (§14, §13)  ');
    expect(lineOf(text, 14)).toContain('  blocked by §13  ');
    expect(lineOf(text, 13)).not.toContain('blocked by');
  });

  it('B5: drops cleared links from the chain', () => {
    const entries = chain();
    entries[1] = entry(14, 'accepted', { blocked_by: ['13    x'] });
    entries[0] = { ...entry(13, 'done', { merged: 'abc1234' }, 0), mainMerged: true };
    const text = formatQueue(entries);
    expect(lineOf(text, 17)).toContain('  blocked by §15 (§14)  ');
    expect(lineOf(text, 14)).not.toContain('blocked by');
  });

  it('B3: a merged: on a branch copy does not clear a blocker, main does', () => {
    const branchCopy = { ...entry(13, 'done', { merged: 'abc1234' }, null, 'branch'), mainMerged: false };
    expect(lineOf(formatQueue([branchCopy, entry(14, 'accepted', { blocked_by: ['13    x'] })]), 14)).toContain('blocked by §13');
    const onMain = { ...entry(13, 'done', { merged: 'abc1234' }, 0), mainMerged: true };
    expect(lineOf(formatQueue([onMain, entry(14, 'accepted', { blocked_by: ['13    x'] })]), 14)).not.toContain('blocked by');
  });

  it('B5: a cycle is one problem line and the queue still prints', () => {
    const text = formatQueue([
      entry(15, 'accepted', { blocked_by: ['17    x'] }),
      entry(17, 'accepted', { blocked_by: ['15    y'] }),
    ]);
    expect(text).toContain(['Problems', '  blocked_by cycle: §15 -> §17 -> §15.', ''].join(String.fromCharCode(10)));
    expect(text.match(/blocked_by cycle/g)).toHaveLength(1);
    expect(lineOf(text, 17)).toContain('blocked by §15');
  });

  it('B4: broken records are problems naming the intent', () => {
    const text = formatQueue([entry(18, 'accepted', { blocked_by: ['x    a', '18    b', '99    c'] })]);
    expect(text).toContain('§18: blocked_by item "x    a": "x" is not an intent id (digits).');
    expect(text).toContain('§18: blocked_by item "18    b": an intent cannot block itself.');
    expect(text).toContain('§18: blocked_by names §99, which is on no branch.');
    expect(formatQueue([entry(18, 'accepted', { blocked_by: ['99    c'] })], { knownIds: ['99'] })).not.toContain('Problems');
  });

  it('JSON carries blocked_by and blocked_by_open', () => {
    const data = queueData(chain());
    const e17 = data.inFlight.find((e) => e.id === 17);
    expect(e17.blocked_by).toEqual([{ id: 15, reason: 'reads its reports' }]);
    expect(e17.blocked_by_open).toEqual([15, 14, 13]);
    expect(data.inFlight.find((e) => e.id === 13)).toMatchObject({ blocked_by: [], blocked_by_open: [] });
    expect(data.problems).toEqual([]);
  });

  it('metadata without the field prints as before', () => {
    expect(formatQueue([entry(1, 'accepted')])).not.toContain('blocked');
  });
});
