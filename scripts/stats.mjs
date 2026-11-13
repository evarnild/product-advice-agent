#!/usr/bin/env node
// `npm run stats -- <id>... | --all [--json] [--transcripts <dir>]` (§19)
//
// Elapsed time, owner wait and tokens per phase of an intent, from git
// milestones, the session log and the Claude Code transcripts, all read in
// place. Prints derived totals only: no prompt or response text. The
// computation is stats-lib.mjs, the reading is stats-io.mjs.
import { collectStats, defaultTranscriptRoot } from './stats-io.mjs';
import { formatAll, formatStats, parseStatsArgs, statsJson } from './stats-lib.mjs';

function main() {
  let opts;
  try {
    opts = parseStatsArgs(process.argv.slice(2), defaultTranscriptRoot());
  } catch (e) {
    console.error(`stats: ${e.message}\nusage: npm run stats -- <id>... | --all [--json] [--transcripts <dir>]`);
    process.exit(1);
  }
  let stats;
  try {
    stats = collectStats({ transcripts: opts.transcripts, only: opts.all ? null : opts.ids });
  } catch (e) {
    console.error(`stats: ${e.message}`);
    process.exit(1);
  }
  if (!opts.all) {
    const missing = opts.ids.filter((id) => !stats.intents.some((i) => i.id === id));
    if (missing.length) console.error(`stats: no commits found for ${missing.map((i) => `§${i}`).join(', ')}`);
  }
  console.log(opts.json ? JSON.stringify(statsJson(stats), null, 2) : opts.all ? formatAll(stats) : formatStats(stats));
}

main();
