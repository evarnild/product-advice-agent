#!/usr/bin/env node
// Claude Code hook handler (.claude/settings.json): appends this session's
// lifecycle event to the shared log that `npm run sessions` reads.
//
// Hooks run on every prompt and every turn of every session, so this script
// must stay invisible: it prints nothing (SessionStart and UserPromptSubmit
// output would land in the model's context), swallows every error, and
// always exits 0. What gets recorded — and what deliberately doesn't, such as
// prompt text beyond a skill name and id — is decided by eventRecordFrom in session-lib.mjs.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { appendEvent } from './session-io.mjs';
import { eventRecordFrom } from './session-lib.mjs';

/** Names under `.claude/skills/` (a directory listing, no file reads); [] when there are none. */
function skillNames(dir) {
  try {
    return readdirSync(join(dir, '.claude', 'skills'), { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name);
  } catch {
    return [];
  }
}

try {
  const input = JSON.parse(readFileSync(0, 'utf8'));
  const dir = process.env.CLAUDE_PROJECT_DIR || (typeof input?.cwd === 'string' && input.cwd) || process.cwd();
  const record = eventRecordFrom(input, process.env, process.cwd(), input?.hook_event_name === 'UserPromptSubmit' ? skillNames(dir) : []);
  if (record) appendEvent(record.dir, record.fields);
} catch {
  // Not in a git repo, no stdin, log not writable: the session matters more than the log.
}
process.exit(0);
