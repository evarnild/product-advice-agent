import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import { expect } from './expect.mjs';
import {
  classifyAbort,
  classifyMerge,
  EXIT,
  findTarget,
  formatReport,
  outputTail,
  parseUpdateArgs,
  planUpdate,
  preflight,
} from './update-branch-lib.mjs';

const wtree = (path, branch) => ({ path, head: 'abc', branch, bare: false });

describe('parseUpdateArgs', () => {
  it('takes exactly one all-digits id', () => {
    expect(parseUpdateArgs(['20'])).toEqual({ ok: true, id: '20' });
  });
  it('rejects no id, two ids, a flag and a non-numeric id', () => {
    for (const argv of [[], ['1', '2'], ['--x'], ['20a'], ['']]) {
      const r = parseUpdateArgs(argv);
      expect(r.ok).toBe(false);
      expect(r.error).toContain('usage');
    }
  });
});

describe('findTarget', () => {
  const list = [
    wtree('/r/repo', 'main'),
    wtree('/r/product-advice-agent-wt/200-z', 'feat/200-z'),
    wtree('/r/product-advice-agent-wt/2-x', 'feat/2-x'),
    wtree('/r/product-advice-agent-wt/20-x', 'feat/20-x'),
  ];
  it('finds by the branch id, with or without codex/, not by prefix', () => {
    expect(findTarget(list, '20')).toEqual({ ok: true, worktree: list[3] });
    const codex = [wtree('/r/c', 'codex/fix/20-y')];
    expect(findTarget(codex, '20').worktree.branch).toBe('codex/fix/20-y');
    expect(findTarget(list.slice(0, 3), '20').ok).toBe(false);
    expect(findTarget(list, '2').worktree.branch).toBe('feat/2-x');
  });
  it('refuses two worktrees for one id, naming both', () => {
    const two = [wtree('/r/a', 'feat/20-x'), wtree('/r/b', 'fix/20-y')];
    const r = findTarget(two, '20');
    expect(r.ok).toBe(false);
    expect(r.reason).toContain('more than one worktree');
    expect(r.reason).toContain('/r/a');
    expect(r.reason).toContain('/r/b');
  });
  it('reports a detached worktree whose folder is <id>-..., else no worktree', () => {
    const r = findTarget([wtree('/r/repo', 'main'), wtree('/r/product-advice-agent-wt/20-x', null)], '20');
    expect(r).toEqual({ ok: false, reason: 'HEAD is detached in /r/product-advice-agent-wt/20-x', detachedPath: '/r/product-advice-agent-wt/20-x' });
    const other = findTarget([wtree('/r/product-advice-agent-wt/200-x', null)], '20');
    expect(other.reason).toContain('no worktree');
    expect(findTarget([], '20').reason).toContain('no worktree has §20');
  });
});

describe('preflight', () => {
  const base = { path: '/r/wt/20-x', branch: 'feat/20-x', mainPath: '/r/repo', inProgress: [], dirty: [] };
  it('accepts a clean branch worktree', () => {
    expect(preflight(base)).toEqual({ ok: true });
  });
  it('names each reason', () => {
    for (const op of ['merge', 'rebase', 'cherry-pick']) {
      const r = preflight({ ...base, inProgress: [op] });
      expect(r.ok).toBe(false);
      expect(r.reason).toContain(`${op} is in progress`);
    }
    expect(preflight({ ...base, path: 'C:\\R\\Repo\\', mainPath: 'c:/r/repo' }).reason).toContain('main checkout');
    expect(preflight({ ...base, branch: 'main' }).reason).toContain('is main');
    expect(preflight({ ...base, branch: null }).reason).toContain('HEAD is detached');
    const d = preflight({ ...base, dirty: [' M a.txt', 'A  b.txt'] });
    expect(d.reason).toContain('a.txt');
    expect(d.reason).toContain('b.txt');
  });
  it('lets the in-progress reason win over every other fault', () => {
    const r = preflight({ ...base, inProgress: ['merge'], branch: null, dirty: [' M a'], path: '/r/repo' });
    expect(r.reason).toContain('merge is in progress');
  });
});

describe('planUpdate', () => {
  it('merges only when behind', () => {
    expect(planUpdate(0)).toBe('up-to-date');
    expect(planUpdate(1)).toBe('merge');
  });
});

describe('classifyMerge', () => {
  it('reads the facts, not the message', () => {
    const h = { headBefore: 'a', headAfter: 'a', mergeHead: false, unmerged: [] };
    expect(classifyMerge({ ...h, status: 0, headAfter: 'b' })).toBe('merged');
    expect(classifyMerge({ ...h, status: 1, mergeHead: true, unmerged: ['f'] })).toBe('conflict');
    expect(classifyMerge({ ...h, status: 1 })).toBe('refused');
    expect(classifyMerge({ ...h, status: 1, headAfter: 'b' })).toBe('unexpected');
    expect(classifyMerge({ ...h, status: 1, mergeHead: true })).toBe('unexpected');
  });
});

describe('classifyAbort', () => {
  const ok = { headBefore: 'abcdef1234', headAfter: 'abcdef1234', mergeHead: false, dirty: [] };
  it('is clean only when nothing is left', () => {
    expect(classifyAbort(ok)).toEqual({ clean: true, left: [] });
  });
  it('lists each fault alone', () => {
    expect(classifyAbort({ ...ok, headAfter: 'fedcba9876' }).left).toEqual(['HEAD moved from abcdef1 to fedcba9']);
    expect(classifyAbort({ ...ok, mergeHead: true }).left).toEqual(['MERGE_HEAD is still present']);
    const d = classifyAbort({ ...ok, dirty: [' M a'] });
    expect(d.clean).toBe(false);
    expect(d.left[0]).toContain('M a');
  });
});

describe('outputTail', () => {
  it('keeps the last 25 lines of 30', () => {
    const text = Array.from({ length: 30 }, (_, i) => `l${i + 1}`).join('\n');
    const lines = outputTail(text).split('\n');
    expect(lines).toHaveLength(25);
    expect(lines[0]).toBe('l6');
    expect(lines.at(-1)).toBe('l30');
  });
});

describe('formatReport', () => {
  const text = (r) => r.lines.join('\n');
  it('up to date: exit 0, names main', () => {
    const r = formatReport({ kind: 'up-to-date', mainShort: 'abc1234' });
    expect(r.exit).toBe(EXIT.OK);
    expect(text(r)).toContain('contains main at abc1234');
  });
  it('merged and green: exit 0 with both hashes', () => {
    const r = formatReport({ kind: 'merged', behind: 2, headShort: 'h123456', mainShort: 'm123456', verify: { ok: true } });
    expect(r.exit).toBe(0);
    expect(text(r)).toContain('behind main by 2');
    expect(text(r)).toContain('h123456');
    expect(text(r)).toContain('m123456');
    expect(text(r)).toContain('verify green');
  });
  it('merged and red: exit 3 with the tail', () => {
    const r = formatReport({ kind: 'merged', behind: 1, headShort: 'h', mainShort: 'm', verify: { ok: false, tail: 'boom' } });
    expect(r.exit).toBe(EXIT.RED);
    expect(text(r)).toContain('verify red after merging main');
    expect(text(r)).toContain('boom');
    expect(text(r)).not.toContain('verify green');
  });
  it('conflict: exit 2 with the files', () => {
    const r = formatReport({ kind: 'conflict', behind: 3, files: ['a/b.md', 'c.txt'] });
    expect(r.exit).toBe(EXIT.CONFLICT);
    expect(text(r)).toContain('a/b.md');
    expect(text(r)).toContain('c.txt');
    expect(text(r)).toContain('behind main by 3');
  });
  it('abort left something: exit 1 listing it', () => {
    const r = formatReport({ kind: 'abort-left', left: ['MERGE_HEAD is still present'] });
    expect(r.exit).toBe(EXIT.REFUSED);
    expect(text(r)).toContain('MERGE_HEAD is still present');
  });
  it('refused: exit 1 with the reason and git message when there is one', () => {
    const a = formatReport({ kind: 'refused', reason: 'no worktree' });
    expect(a.exit).toBe(1);
    expect(text(a)).toContain('no worktree');
    const b = formatReport({ kind: 'refused', reason: 'git refused to merge', gitMessage: 'error: untracked file' });
    expect(text(b)).toContain('error: untracked file');
  });
});

describe('boundary', () => {
  it('the lib imports no node:child_process or node:fs', () => {
    const src = readFileSync(join(dirname(fileURLToPath(import.meta.url)), 'update-branch-lib.mjs'), 'utf8');
    expect(src).not.toMatch(/from\s+['"]node:(child_process|fs)/);
    expect(src).not.toMatch(/require\(/);
  });
});
