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
const SPEC_PLAN_AGENTS = ['.claude/agents/product-advice-agent-spec.md', '.claude/agents/product-advice-agent-plan.md', '.codex/agents/product-advice-agent-spec.toml', '.codex/agents/product-advice-agent-plan.toml'];
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

describe('kit texts: the number reservation (§28) is written down where each reader looks', () => {
  it('AC20: npm run reserve-id is in the policy, the guides and the intent skill', () => {
    for (const f of ['REVIEW-POLICY.md', 'CLAUDE.md', 'AGENTS.md', 'intents/README.md', 'sdlc.md', '.claude/skills/intent/SKILL.md']) {
      expect(read(f), f).toContain('npm run reserve-id');
    }
  });
  it('the policy keeps every other push on request and names the script in the Reviewed row', () => {
    const policy = read('REVIEW-POLICY.md');
    expect(policy).toContain('Every other push stays on request');
    expect(policy).toContain('scripts/reserve-id.mjs');
  });
  it('the intent skill is at 0.3.0 with no 0.2.0 stamp left', () => {
    const skill = read('.claude/skills/intent/SKILL.md');
    expect(skill).toContain('intent@0.3.0');
    expect(skill).not.toContain('intent@0.2.0');
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

describe('kit texts: spec and plan agents (§36)', () => {
  const CLAUDE_AGENTS = SPEC_PLAN_AGENTS.filter((f) => f.endsWith('.md'));
  const CODEX_AGENTS = SPEC_PLAN_AGENTS.filter((f) => f.endsWith('.toml'));
  const kindOf = (f) => (f.includes('-spec.') ? 'spec' : 'plan');
  const SKILL_OF = { spec: '.claude/skills/spec/SKILL.md', plan: '.claude/skills/build-plan/SKILL.md' };
  const STAMP = { spec: 'product-advice-agent/spec@0.2.0', plan: 'product-advice-agent/build-plan@0.2.0' };
  const PHRASES = ['Write exactly one file', 'private folder with a unique name', 'Never commit', 'Never edit metadata.yml', 'Never record a gate', 'INCOMPLETE:', '250 words'];

  it('AC1: each Claude file has name, description and tools in its frontmatter', () => {
    for (const f of CLAUDE_AGENTS) {
      const text = read(f);
      expect(text.startsWith('---'), f).toBe(true);
      expect(text, f).toMatch(new RegExp(`^name: product-advice-agent-${kindOf(f)}[ 	]*$`, 'm'));
      expect(/^description: \S/m.test(text), f).toBe(true);
      expect(/^tools: /m.test(text), f).toBe(true);
    }
  });
  it('AC1: each Codex file has name, description and a closed developer_instructions', () => {
    for (const f of CODEX_AGENTS) {
      const text = read(f);
      expect(text, f).toContain(`name = "product_advice_agent_${kindOf(f)}"`);
      expect(text, f).toContain('description = "');
      expect(text, f).toContain('developer_instructions = """');
      expect(text.trimEnd().endsWith('"""'), f).toBe(true);
    }
  });
  it('AC2: the shared hand-off rules are in all four files', () => {
    for (const f of SPEC_PLAN_AGENTS) for (const phrase of PHRASES) expect(read(f), `${f}: ${phrase}`).toContain(phrase);
  });
  it('AC2: each agent carries its own skill stamp, tied to the skill', () => {
    for (const f of SPEC_PLAN_AGENTS) {
      const kind = kindOf(f);
      const other = kind === 'spec' ? 'plan' : 'spec';
      expect(read(f), f).toContain(STAMP[kind]);
      expect(read(f), f).not.toContain(STAMP[other]);
      expect(read(SKILL_OF[kind]), SKILL_OF[kind]).toContain(STAMP[kind]);
      expect(read(f), f).toContain(SKILL_OF[kind]);
    }
  });
  it('AC3: Claude agents have Write and Bash, no Edit, and run on Sonnet', () => {
    for (const f of CLAUDE_AGENTS) {
      const tools = /^tools: (.*)$/m.exec(read(f))[1];
      expect(/Edit/.test(tools), f).toBe(false);
      expect(tools, f).toContain('Write');
      expect(tools, f).toContain('Bash');
      expect(read(f), f).toMatch(/^model: sonnet\s*$/m);
    }
  });
  it('B4: no agent text tells itself to run git commit beyond the prohibition', () => {
    for (const f of SPEC_PLAN_AGENTS) expect(read(f).split('git commit').length - 1, f).toBeLessThanOrEqual(1);
  });
  it('AC4: the skills and guides name the agents and the coordinator check', () => {
    for (const [skill, agent, tag] of [['.claude/skills/spec/SKILL.md', 'product-advice-agent-spec', '§<id> spec'], ['.claude/skills/build-plan/SKILL.md', 'product-advice-agent-plan', '§<id> plan']]) {
      const text = read(skill);
      for (const phrase of [agent, tag, 'git status --short', 'git diff --stat', 'pass a `model`']) expect(text, `${skill}: ${phrase}`).toContain(phrase);
    }
    for (const f of [AUTO, 'CLAUDE.md']) for (const name of ['product-advice-agent-spec', 'product-advice-agent-plan']) expect(read(f), `${f}: ${name}`).toContain(name);
    for (const name of ['product_advice_agent_spec', 'product_advice_agent_plan']) expect(read('AGENTS.md'), name).toContain(name);
  });
  it('B12: CLAUDE.md says the coordinator does not draft by reading the codebase inline', () => {
    expect(read('CLAUDE.md')).toContain('not by reading the codebase inline');
  });
});
