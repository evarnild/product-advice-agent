// A cheap grep over the kit's instruction texts (§20): the update-before-review
// flow is written down where each reader looks, and the old "rebase" wordings
// are gone. Weak by design: it cannot prove that no new rebase instruction
// exists in other words; the review's full `grep -i rebase` does that.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';
import { expect } from './expect.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => readFileSync(join(root, p), 'utf8');

function walk(dir) {
  const out = [];
  for (const name of readdirSync(join(root, dir))) {
    const rel = `${dir}/${name}`;
    if (statSync(join(root, rel)).isDirectory()) out.push(...walk(rel));
    else if (/\.(md|toml|mjs)$/.test(name)) out.push(rel);
  }
  return out;
}

const AUTO = '.claude/skills/auto/SKILL.md';
const REVIEW = '.claude/skills/review/SKILL.md';
const SESSIONS = '.claude/skills/sessions/SKILL.md';
const IMPLEMENTERS = ['.claude/agents/product-advice-agent-implementer.md', '.codex/agents/product-advice-agent-implementer.toml'];
const REVIEWERS = ['.claude/agents/product-advice-agent-reviewer.md', '.codex/agents/product-advice-agent-reviewer.toml'];

describe('kit texts: the update flow is written down', () => {
  it('names npm run update-branch where it is used', () => {
    for (const f of [AUTO, REVIEW, SESSIONS, 'REVIEW-POLICY.md', 'CLAUDE.md']) expect(read(f), f).toContain('npm run update-branch');
  });
  it('both implementer definitions carry the merge-on-request rule and its abort path', () => {
    for (const f of IMPLEMENTERS) {
      expect(read(f), f).toContain('git merge main');
      expect(read(f), f).toContain('git merge --abort');
    }
  });
  it('the Codex implementer never-merges sentence is narrowed to main', () => {
    const text = read('.codex/agents/product-advice-agent-implementer.toml');
    expect(text).toContain('an implementer never merges into `main`');
    expect(text).not.toContain('an implementer never merges.');
  });
  it('the reviewers and the review skill name the three-dot diff', () => {
    for (const f of [...REVIEWERS, REVIEW]) expect(read(f), f).toContain('main...');
  });
  it('the policy has the main: header line', () => {
    expect(read('REVIEW-POLICY.md')).toContain('main: <hash>');
  });
  it('/auto lists the three stop reasons', () => {
    const auto = read(AUTO);
    for (const reason of ['main merge conflict', 'red verify after merging main', 'branch update refused']) expect(auto).toContain(reason);
  });
});

describe('kit texts: the old rebase instructions are gone', () => {
  const files = [
    ...walk('.claude'),
    ...walk('.codex'),
    'REVIEW-POLICY.md',
    'CLAUDE.md',
    ...readdirSync(join(root, 'scripts')).filter((n) => n.endsWith('.mjs') && !n.endsWith('.test.mjs')).map((n) => `scripts/${n}`),
  ];
  const old = [
    'rebase before review',
    'main moved, rebase',
    'rebase `<branch>`',
    'rebase this branch',
    'a rebase since the review means',
    'others rebase',
    'add rebases',
  ];
  it('covers the files it should', () => {
    expect(files).toContain(AUTO);
    expect(files).toContain('scripts/sessions.mjs');
  });
  it('no file uses an old wording', () => {
    for (const f of files) {
      const text = read(f).toLowerCase();
      for (const phrase of old) expect(text.includes(phrase), `${f}: "${phrase}"`).toBe(false);
    }
  });
});
