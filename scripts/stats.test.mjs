// End-to-end tests for `npm run stats` against a throwaway git repository, a
// synthetic session log and synthetic transcripts (scripts/fixtures/stats/).
// Never the real repository, the real session log or ~/.claude.
import { execFileSync, spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { after as afterAll, before as beforeAll, describe, it } from 'node:test';
import { expect } from './expect.mjs';
import { collectStats, projectSlug, renderStatsFile } from './stats-io.mjs';
import { parseStatsArgs } from './stats-lib.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const STATS = join(here, 'stats.mjs');
const FIX = join(here, 'fixtures', 'stats');
const SENTINEL = 'SENTINEL-PROMPT-TEXT-7f3a';

const GIT_ENV = {
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^GIT_/i.test(k))),
  GIT_AUTHOR_NAME: 't',
  GIT_AUTHOR_EMAIL: 't@example.com',
  GIT_COMMITTER_NAME: 't',
  GIT_COMMITTER_EMAIL: 't@example.com',
};

let sandbox;
let repo;
let transcripts;
const git = (cwd, ...args) => execFileSync('git', args, { cwd, env: GIT_ENV, encoding: 'utf8' }).trim();
const commitAt = (iso, subject) => {
  writeFileSync(join(repo, 'f.txt'), `${subject}\n`);
  git(repo, 'add', '.');
  execFileSync('git', ['commit', '-q', '-m', subject], { cwd: repo, env: { ...GIT_ENV, GIT_COMMITTER_DATE: iso, GIT_AUTHOR_DATE: iso } });
};
const run = (args, env = {}) => spawnSync(process.execPath, [STATS, ...args], { cwd: repo, env: { ...GIT_ENV, ...env }, encoding: 'utf8' });

beforeAll(() => {
  sandbox = realpathSync(mkdtempSync(join(tmpdir(), 'sdlc-stats-')));
  repo = join(sandbox, 'repo');
  transcripts = join(sandbox, 'projects');
  mkdirSync(repo);
  git(repo, 'init', '-q', '-b', 'main');
  git(repo, 'config', 'core.autocrlf', 'false');
  commitAt('2026-11-01T07:00:00Z', 'init');
  commitAt('2026-11-01T08:00:00Z', '§7: intent drafted and accepted (owner: "yes")');
  commitAt('2026-11-01T09:00:00Z', '§7: plan approved (auto)');
  commitAt('2026-11-01T10:00:00Z', '§7: in-review, progress entry');
  commitAt('2026-11-01T12:00:00Z', '§7: merged (abc1234); status done');
  commitAt('2026-11-01T13:00:00Z', '§8: intent drafted (owner: x)');

  const log = [
    { ts: '2026-11-01T09:10:00Z', worktree: repo, branch: 'main', id: null, event: 'UserPromptSubmit', session: 'sess1', promptChars: 30, detail: '30 chars', skill: 'build-plan', skillId: 7 },
    { ts: '2026-11-01T09:20:00Z', worktree: repo, branch: 'main', id: null, event: 'Stop', session: 'sess1', detail: '' },
    { ts: '2026-11-01T09:50:00Z', worktree: repo, branch: 'main', id: null, event: 'UserPromptSubmit', session: 'sess1', promptChars: 5, detail: '5 chars', skill: 'auto', skillId: 7 },
  ];
  writeFileSync(join(repo, '.git', 'product-advice-agent-sessions.jsonl'), `${log.map((l) => JSON.stringify(l)).join('\n')}\nhalf a line {\n`);

  const project = join(transcripts, projectSlug(repo));
  mkdirSync(join(project, 'sess1', 'subagents'), { recursive: true });
  copyFileSync(join(FIX, 'coordinator.jsonl'), join(project, 'sess1.jsonl'));
  for (const f of ['agent-tagged.jsonl', 'agent-tagged.meta.json', 'agent-untagged.jsonl', 'agent-untagged.meta.json']) {
    copyFileSync(join(FIX, f), join(project, 'sess1', 'subagents', f));
  }
  // another project's transcripts must never be read
  const other = join(transcripts, 'C--somewhere-else');
  mkdirSync(other, { recursive: true });
  copyFileSync(join(FIX, 'coordinator.jsonl'), join(other, 'other.jsonl'));
});

afterAll(() => {
  rmSync(sandbox, { recursive: true, force: true });
});

describe('npm run stats', () => {
  it('prints the phases, tokens per model split coordinator and agents, and the skipped count', () => {
    const r = run(['7', '--transcripts', transcripts]);
    expect(r.status).toBe(0);
    expect(r.stdout).toContain('§7');
    expect(r.stdout).toMatch(/plan\s+1h00m/);
    expect(r.stdout).toMatch(/build\s+1h00m/);
    expect(r.stdout).toContain('coordinator model-a: in 100 out 10 cr 1.0k cw 5');
    expect(r.stdout).toContain('coordinator model-b: in 7');
    expect(r.stdout).toContain('agents model-a: in 50 out 5 cr 500 cw 2');
    expect(r.stdout).toMatch(/unattributed\s+agents model-b: in 9 out 9 cr 9 cw 9/);
    expect(r.stdout).toContain('skipped lines: 1');
    expect(r.stdout).toContain('sess1.jsonl: 1');
    expect(r.stdout).toMatch(/in-session/);
  });

  it('counts the in-session wait from the log, skipping its half-written line', () => {
    const r = run(['7', '--json', '--transcripts', transcripts]);
    const j = JSON.parse(r.stdout);
    const build = j.intents[0].phases.find((p) => p.name === 'build');
    expect(build.sessionWaitMs).toBe(30 * 60 * 1000); // Stop 09:20 -> prompt 09:50
    expect(build.tokens.coordinator['model-a'].input).toBe(100); // counted once
  });

  it('counts every token once: the total equals the distinct messages of the fixtures', () => {
    const j = JSON.parse(run(['--all', '--json', '--transcripts', transcripts]).stdout);
    const all = [];
    for (const it of j.intents) all.push(it.totals.tokens);
    all.push(j.unattributed, ...Object.values(j.shared));
    let total = 0;
    for (const b of all) for (const src of ['coordinator', 'agents']) for (const u of Object.values(b[src])) total += u.input + u.output + u.cacheRead + u.cacheWrite;
    expect(total).toBe(1115 + 10 + 557 + 36);
  });

  it('prints one line per intent with --all, partial while the change is not on main', () => {
    const r = run(['--all', '--transcripts', transcripts]);
    expect(r.status).toBe(0);
    expect(r.stdout).toMatch(/^§7 .*partial$/m);
    expect(r.stdout).toMatch(/^§8 /m);
    expect(r.stdout).not.toMatch(/^§8 .*partial$/m);
    expect(r.stdout).toMatch(/^total /m);
  });

  it('never prints transcript or prompt text', () => {
    for (const args of [['7'], ['--all'], ['7', '--json'], ['--all', '--json']]) {
      const r = run([...args, '--transcripts', transcripts]);
      expect(`${r.stdout}${r.stderr}`).not.toContain(SENTINEL);
    }
  });

  it('works without any transcripts, and reads the root from the environment', () => {
    const r = run(['7'], { SDLC_STATS_TRANSCRIPTS: join(sandbox, 'does-not-exist') });
    expect(r.status).toBe(0);
    expect(r.stdout).toContain('skipped lines: 0');
    const viaEnv = run(['7'], { SDLC_STATS_TRANSCRIPTS: transcripts });
    expect(viaEnv.stdout).toContain('agents model-a');
  });

  it('refuses bad arguments and says when an id has no commits', () => {
    expect(run([]).status).toBe(1);
    expect(run(['x']).stderr).toContain('unknown argument');
    expect(run(['99', '--transcripts', transcripts]).stderr).toContain('no commits found for §99');
  });

  it('parses its arguments', () => {
    expect(parseStatsArgs(['3', '§4', '--json'], 'd')).toEqual({ ids: [3, 4], all: false, json: true, transcripts: 'd' });
    expect(parseStatsArgs(['--all', '--transcripts', 'x'], 'd')).toMatchObject({ all: true, transcripts: 'x' });
    expect(() => parseStatsArgs(['--transcripts'], 'd')).toThrow();
  });
});

describe('renderStatsFile (B9)', () => {
  it('renders the stamped file, counting the pending merge as the end of the ship phase', () => {
    const md = renderStatsFile(repo, 7, 'abc1234', { now: Date.parse('2026-11-01T12:30:00Z') });
    expect(md).toContain('# §7 stats');
    expect(md).toContain('generated-by: product-advice-agent/ship@');
    expect(md).not.toContain(SENTINEL);
  });

  it('gives an intent without a merged commit a ship phase ending at the pending merge (I5)', () => {
    const md = renderStatsFile(repo, 8, 'abc1234', { now: Date.parse('2026-11-01T15:00:00Z') });
    expect(md).toMatch(/^ {2}ship\s+2h00m/m); // §8 drafted 13:00, the pending merge at 15:00
    expect(collectStats({ cwd: repo, transcripts, only: [8], now: Date.parse('2026-11-01T15:00:00Z') }).intents[0].phases.at(-1).open).toBe(true);
  });

  it('throws when collection throws, so the caller can carry on', () => {
    expect(() => renderStatsFile(repo, 7, 'abc1234', { collect: () => { throw new Error('boom'); } })).toThrow('boom');
  });
});

describe('author time and the stats cutover (F4, I4)', () => {
  let box;
  let r2;
  const commitDates = (iso, committerIso, subject, file = 'f.txt') => {
    writeFileSync(join(r2, file), `${subject}
`);
    git(r2, 'add', '.');
    execFileSync('git', ['commit', '-q', '-m', subject], { cwd: r2, env: { ...GIT_ENV, GIT_AUTHOR_DATE: iso, GIT_COMMITTER_DATE: committerIso } });
  };
  const REBASED = '2026-11-05T00:00:00Z'; // what a rebase does: every committer time becomes the same
  beforeAll(() => {
    box = realpathSync(mkdtempSync(join(tmpdir(), 'sdlc-stats2-')));
    r2 = join(box, 'repo');
    mkdirSync(join(r2, 'scripts'), { recursive: true });
    git(r2, 'init', '-q', '-b', 'main');
    git(r2, 'config', 'core.autocrlf', 'false');
    commitDates('2026-11-01T07:00:00Z', REBASED, 'init');
    commitDates('2026-11-01T08:00:00Z', REBASED, '§1: intent drafted and accepted (owner: "yes")');
    commitDates('2026-11-01T09:00:00Z', REBASED, '§1: merged (abc1234); status done');
    commitDates('2026-11-01T10:00:00Z', REBASED, 'add stats', 'scripts/stats-lib.mjs'); // author time: the cutover
    commitDates('2026-11-01T11:00:00Z', REBASED, '§2: intent drafted and accepted (owner: "yes")');
    commitDates('2026-11-01T12:00:00Z', REBASED, '§2: plan approved (auto)');
    commitDates('2026-11-01T14:00:00Z', REBASED, '§2: in-review, progress entry');
    commitDates('2026-11-01T15:00:00Z', REBASED, '§2: merged (def5678); status done');
  });
  afterAll(() => {
    rmSync(box, { recursive: true, force: true });
  });
  const stats = (...args) => JSON.parse(spawnSync(process.execPath, [STATS, ...args, '--json', '--transcripts', join(box, 'none')], { cwd: r2, env: GIT_ENV, encoding: 'utf8' }).stdout);

  it('keeps distinct phases for a rebased intent: author times differ while committer times are equal (F4)', () => {
    const it2 = stats('2').intents[0];
    const ms = Object.fromEntries(it2.phases.map((p) => [p.name, p.elapsedMs / 3600000]));
    expect(ms).toMatchObject({ intent: 0, plan: 1, build: 2, ship: 1 });
  });

  it('marks partial only the intent merged before stats-lib.mjs arrived on main, by author time (I4, F4)', () => {
    const j = stats('--all');
    expect(j.intents.find((i) => i.id === 1).partial).toBe(true);
    expect(j.intents.find((i) => i.id === 2).partial).toBe(false);
  });
});

describe('the stats cutover is when stats-lib.mjs reached main (F8)', () => {
  it('uses the merge commit, not the author time of the commit that added the file', () => {
    const box = realpathSync(mkdtempSync(join(tmpdir(), 'sdlc-stats3-')));
    const r3 = join(box, 'repo');
    mkdirSync(join(r3, 'scripts'), { recursive: true });
    const g = (...a) => execFileSync('git', a, { cwd: r3, env: GIT_ENV, encoding: 'utf8' }).trim();
    const c = (iso, subject, file = 'f.txt') => {
      writeFileSync(join(r3, file), `${subject}
`);
      g('add', '.');
      execFileSync('git', ['commit', '-q', '-m', subject], { cwd: r3, env: { ...GIT_ENV, GIT_AUTHOR_DATE: iso, GIT_COMMITTER_DATE: iso } });
    };
    try {
      g('init', '-q', '-b', 'main');
      g('config', 'core.autocrlf', 'false');
      c('2026-11-01T07:00:00Z', 'init');
      g('checkout', '-q', '-b', 'feat/9-stats');
      c('2026-11-02T08:00:00Z', 'add stats', 'scripts/stats-lib.mjs'); // authored early
      g('checkout', '-q', 'main');
      c('2026-11-03T08:00:00Z', '§1: intent drafted and accepted (owner: "yes")');
      c('2026-11-03T09:00:00Z', '§1: merged (abc1234); status done'); // after the author time, before the merge
      execFileSync('git', ['merge', '--no-ff', '-q', '-m', 'Merge §9: stats', 'feat/9-stats'], { cwd: r3, env: { ...GIT_ENV, GIT_AUTHOR_DATE: '2026-11-04T08:00:00Z', GIT_COMMITTER_DATE: '2026-11-04T08:00:00Z' } });
      const r = spawnSync(process.execPath, [STATS, '--all', '--json', '--transcripts', join(box, 'none')], { cwd: r3, env: GIT_ENV, encoding: 'utf8' });
      expect(JSON.parse(r.stdout).intents.find((i) => i.id === 1).partial).toBe(true);
    } finally {
      rmSync(box, { recursive: true, force: true });
    }
  });
});
