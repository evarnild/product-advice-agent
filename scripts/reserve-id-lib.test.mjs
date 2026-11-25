import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { EXIT, checkCarried, decide, parseReserveArgs, pushArgs, reservationRef, reservationSubject } from './reserve-id-lib.mjs';

describe('parseReserveArgs', () => {
  it('takes one positive integer without a leading zero', () => {
    expect(parseReserveArgs(['28'])).toEqual({ id: '28' });
    for (const bad of [[], ['028'], ['x'], ['1', '2'], ['0'], ['-3'], ['1.5']]) expect(parseReserveArgs(bad).error).toMatch(/usage/);
  });
});

describe('decide', () => {
  const base = { id: '23', dir: '23-a' };
  it('reserves when origin holds nothing for the number', () => {
    expect(decide({ ...base, originMainDirs: ['1-x', '230-y'], reservationDirs: null }).action).toBe('reserve');
  });
  it('is already on main (exit 0) when origin/main holds the same folder, before any other check', () => {
    const d = decide({ ...base, originMainDirs: ['23-a'], reservationDirs: ['23-zzz'] });
    expect(d.action).toBe('already-on-main');
    expect(d.exit).toBe(EXIT.OK);
    expect(d.message).toContain('already on origin/main');
  });
  it('is taken (exit 1) by another folder on origin/main', () => {
    const d = decide({ ...base, originMainDirs: ['23-b'] });
    expect(d.exit).toBe(EXIT.REFUSED);
    expect(d.message).toBe('§23 is taken on origin by intents/23-b (origin/main); take `npm run queue -- --next-id` and renumber the draft');
  });
  it('is taken by another folder in the reservation', () => {
    const d = decide({ ...base, originMainDirs: [], reservationDirs: ['23-b'] });
    expect(d.exit).toBe(EXIT.REFUSED);
    expect(d.message).toContain('intents/23-b (origin/intent/23)');
  });
  it('is already reserved (exit 0) when the reservation holds the same folder', () => {
    const d = decide({ ...base, originMainDirs: [], reservationDirs: ['23-a'] });
    expect(d.action).toBe('already-reserved');
    expect(d.exit).toBe(EXIT.OK);
    expect(d.message).toContain('already reserved');
  });
  it('treats a reservation branch with no intent folder as taken', () => {
    expect(decide({ ...base, reservationDirs: [] }).exit).toBe(EXIT.REFUSED);
  });
});

describe('checkCarried', () => {
  const dir = 'intents/23-a';
  const two = [`${dir}/intent.md`, `${dir}/metadata.yml`];
  it('accepts the two files, or metadata.yml alone, with no parent', () => {
    expect(checkCarried({ parents: [], paths: two, dir })).toBe(null);
    expect(checkCarried({ parents: [], paths: [`${dir}/metadata.yml`], dir })).toBe(null);
  });
  it('refuses a parent, a path outside the folder, another file, or no metadata.yml', () => {
    expect(checkCarried({ parents: ['abc'], paths: two, dir })).toMatch(/parent/);
    expect(checkCarried({ parents: [], paths: [...two, 'src/x.py'], dir })).toMatch(/src\/x\.py/);
    expect(checkCarried({ parents: [], paths: [...two, `${dir}/spec.md`], dir })).toMatch(/spec\.md/);
    expect(checkCarried({ parents: [], paths: [`intents/230-b/metadata.yml`], dir })).toMatch(/230-b/);
    expect(checkCarried({ parents: [], paths: [`${dir}/intent.md`], dir })).toMatch(/metadata\.yml/);
  });
});

describe('the push', () => {
  it('has exactly one plain refspec: no plus, no flag', () => {
    expect(pushArgs('abc', 7)).toEqual(['push', 'origin', 'abc:refs/heads/intent/7']);
    expect(reservationRef(7)).toBe('refs/heads/intent/7');
  });
  it('subject names the folder', () => {
    expect(reservationSubject(7, 'intents/7-x')).toBe('§7: number reserved (intents/7-x)');
  });
});
