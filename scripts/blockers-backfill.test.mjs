// B10: the repo's own §14, §15 and §17 metadata record the dependencies the
// spec lists, and the queue would show them as the spec says (AC6). Reads the
// working tree's intents/ only; §13 is stood in for by an open synthetic entry.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import { parseBlockers } from './blockers-lib.mjs';
import { parseGate, parseMetadata } from './intent-check-lib.mjs';
import { formatQueue } from './queue-lib.mjs';
import { expect } from './expect.mjs';

const intents = join(dirname(fileURLToPath(import.meta.url)), '..', 'intents');
const load = (dir) => parseMetadata(readFileSync(join(intents, dir, 'metadata.yml'), 'utf8'));
const dirs = { 14: '14-catalogue-500', 15: '15-fifty-cases', 17: '17-evals-every-change' };

describe('the backfilled blocked_by records', () => {
  it('hold exactly the spec B10 items', () => {
    const ids = (n) => parseBlockers(load(dirs[n]), String(n)).items.map((i) => i.id);
    expect(ids(14)).toEqual(['13']);
    expect(ids(15)).toEqual(['13', '14']);
    expect(ids(17)).toEqual(['13']);
    for (const n of [14, 15, 17]) expect(parseBlockers(load(dirs[n]), String(n)).problems).toEqual([]);
  });

  it('leave the gates parseable', () => {
    for (const n of [14, 15, 17]) expect(parseGate(load(dirs[n]).intent_accepted).state).toBe('recorded');
  });

  it('make the queue show §14, §15 and §17 as blocked while §13 is open', () => {
    const entry = (id, metadata) => ({ id: String(id), source: 'main', mergeRank: null, mainMerged: false, metadata });
    const text = formatQueue([
      entry(13, { slug: 's13', type: 'feature', title: 'Thirteen', status: 'accepted' }),
      ...[14, 15, 17].map((n) => entry(n, load(dirs[n]))),
    ]);
    const line = (n) => text.split(String.fromCharCode(10)).find((l) => l.trim().startsWith(`§${n}  `));
    expect(line(14)).toContain('  blocked by §13  ');
    expect(line(15)).toContain('  blocked by §13, §14  ');
    expect(line(17)).toContain('  blocked by §13  ');
    expect(text).not.toContain('Problems');
  });
});
