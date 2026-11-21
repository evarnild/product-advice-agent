// The git/fs half of `npm run stats` (§19), shared by stats.mjs and ship.mjs.
// Reads git history, the session log and the Claude Code transcripts in
// place; writes nothing. The computation is stats-lib.mjs.
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { eventLogPath, git, mainCheckout } from './session-io.mjs';
import { parseEvents, parseWorktreeList } from './session-lib.mjs';
import { computeStats, parseCommitLog, statsMarkdown, usageLines } from './stats-lib.mjs';

/** Claude Code names a project folder after the path, every non-alphanumeric character becoming `-`. */
export const projectSlug = (path) => String(path).replace(/[^A-Za-z0-9]/g, '-');

/** The default transcript root: `~/.claude/projects`. */
export const defaultTranscriptRoot = () => process.env.SDLC_STATS_TRANSCRIPTS || join(homedir(), '.claude', 'projects');

function readText(file) {
  try {
    return readFileSync(file, 'utf8');
  } catch {
    return '';
  }
}

function listDir(dir) {
  try {
    return readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
}

/** Checkout paths whose transcripts count: the main checkout, its worktrees, and every worktree the session log has seen. */
export function checkoutPaths(root, events) {
  const paths = new Set([root]);
  try {
    for (const wt of parseWorktreeList(git(root, 'worktree', 'list', '--porcelain'))) paths.add(wt.path);
  } catch {
    // no worktree list: the main checkout and the log's paths are what there is
  }
  for (const e of events) if (typeof e.worktree === 'string') paths.add(e.worktree);
  return [...paths];
}

/**
 * Coordinator sessions (`<project>/<session>.jsonl`) and their agents
 * (`<project>/<session>/subagents/agent-*.jsonl` with `agent-*.meta.json`)
 * for the given checkout paths. Only counts, ids and times come out of a file.
 */
export function readTranscripts(transcriptRoot, paths) {
  const coordinators = [];
  const agents = [];
  for (const slug of new Set(paths.map(projectSlug))) {
    const dir = join(transcriptRoot, slug);
    for (const f of listDir(dir)) {
      if (f.isFile() && f.name.endsWith('.jsonl')) {
        const session = f.name.slice(0, -'.jsonl'.length);
        coordinators.push({ file: `${slug}/${f.name}`, session, usage: usageLines(readText(join(dir, f.name))) });
      } else if (f.isDirectory()) {
        const sub = join(dir, f.name, 'subagents');
        for (const a of listDir(sub)) {
          if (!a.isFile() || !/^agent-.*\.jsonl$/.test(a.name)) continue;
          let description = '';
          try {
            const meta = JSON.parse(readText(join(sub, a.name.replace(/\.jsonl$/, '.meta.json'))));
            if (typeof meta?.description === 'string') description = meta.description;
          } catch {
            // no readable tag: the agent is unattributed
          }
          agents.push({ file: `${slug}/${f.name}/${a.name}`, session: f.name, description, usage: usageLines(readText(join(sub, a.name))) });
        }
      }
    }
  }
  return { coordinators, agents };
}

/** When stats-lib.mjs first reached main (ms), or null while it has not: intents merged before it are `partial`. */
export function statsCutover(root) {
  try {
    const out = git(root, 'log', 'main', '--first-parent', '-m', '--diff-filter=A', '--format=%at', '--', 'scripts/stats-lib.mjs');
    const last = out.split(/\r?\n/).filter(Boolean).at(-1);
    return last ? Number(last) * 1000 : null;
  } catch {
    return null;
  }
}

/**
 * Everything `npm run stats` and `/ship` report, for `only` (intent ids, or
 * all when null). Throws on a git failure; unreadable transcripts and log
 * lines are skipped and counted, never thrown.
 */
export function collectStats({ cwd = process.cwd(), transcripts = defaultTranscriptRoot(), only = null, now = Date.now(), extraCommits = [] } = {}) {
  const root = mainCheckout(cwd);
  // oldest first, parents before children: commits in the same second keep the order they were made
  const commits = [...parseCommitLog(git(root, 'log', '--branches', '--topo-order', '--reverse', '--format=%H %at %s')), ...extraCommits];
  const logFile = eventLogPath(root);
  const events = existsSync(logFile) ? parseEvents(readText(logFile)) : [];
  const { coordinators, agents } = existsSync(transcripts) ? readTranscripts(transcripts, checkoutPaths(root, events)) : { coordinators: [], agents: [] };
  return computeStats({ commits, events, coordinators, agents, now, cutover: statsCutover(root), only });
}

/** The `generated-by` stamp of a committed stats.md. */
export const STATS_STAMP = 'product-advice-agent/ship@0.2.0';

/**
 * The `stats.md` text for intent `id` as `/ship` commits it (B9): collected
 * at `now`, with the merge commit that is about to be made counted as the
 * end of the ship phase. Throws when collection fails; the caller decides
 * that a failure never blocks a ship.
 */
export function renderStatsFile(root, id, mergedHash, { collect = collectStats, now = Date.now() } = {}) {
  const stats = collect({ cwd: root, only: [Number(id)], now, extraCommits: [{ hash: `pending-${id}`, ts: now, subject: `§${id}: merged (${mergedHash}); status done` }] });
  const it = stats.intents.find((i) => i.id === Number(id));
  if (!it) throw new Error(`no commits found for §${id}`);
  return statsMarkdown(it, STATS_STAMP);
}
