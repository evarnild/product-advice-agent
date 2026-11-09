#!/usr/bin/env node
// Claude Code hook handler (.claude/settings.json): appends this session's
// lifecycle event to the shared log that `npm run sessions` reads.
//
// Hooks run on every prompt and every turn of every session, so this script
// must stay invisible: it prints nothing (SessionStart and UserPromptSubmit
// output would land in the model's context), swallows every error, and
// always exits 0. What gets recorded — and what deliberately doesn't, such as
// prompt text — is decided by eventRecordFrom in session-lib.mjs.
import { readFileSync } from 'node:fs';
import { appendEvent } from './session-io.mjs';
import { eventRecordFrom } from './session-lib.mjs';

try {
  const record = eventRecordFrom(JSON.parse(readFileSync(0, 'utf8')), process.env, process.cwd());
  if (record) appendEvent(record.dir, record.fields);
} catch {
  // Not in a git repo, no stdin, log not writable: the session matters more than the log.
}
process.exit(0);
