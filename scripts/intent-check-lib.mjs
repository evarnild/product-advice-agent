// Pure logic behind `npm run check:intent` (scripts/check-intent.mjs).
// Kept free of git/fs calls so it can be unit-tested; see
// intent-check-lib.test.mjs. The rules it encodes are written down for
// humans in intents/README.md — change both together.

/** Branch prefix → intent type. */
export const PREFIX_TO_TYPE = {
  feat: 'feature',
  fix: 'fix',
  refactor: 'refactor',
  adjust: 'adjustment',
  exp: 'experiment',
};

/** Which artefacts each intent type requires, and which gates must be recorded. */
export const TYPE_RULES = {
  feature: { files: ['intent.md', 'spec.md', 'plan.md'], gates: ['intent_accepted', 'spec_accepted', 'plan_approved'] },
  fix: { files: ['intent.md', 'plan.md'], gates: ['intent_accepted', 'plan_approved'] },
  refactor: { files: ['intent.md', 'plan.md'], gates: ['intent_accepted', 'plan_approved'] },
  adjustment: { files: ['intent.md'], gates: ['intent_accepted'] },
  experiment: { files: ['intent.md'], gates: ['intent_accepted'] },
};

/** An adjustment is only an adjustment while its blast radius stays small. */
export const ADJUSTMENT_LIMITS = { files: 5, lines: 60 };

const BRANCH_RE = /^(?:codex\/)?(feat|fix|refactor|adjust|exp)\/(\d+)-([a-z0-9][a-z0-9-]*)$/;

/**
 * Parses `feat/27-ticket-intake` (optionally `codex/`-prefixed) into its parts.
 * Returns null for branches that carry no intent id (main, worktree-agent-*).
 */
export function parseBranch(name) {
  const m = BRANCH_RE.exec(name.trim());
  if (!m) return null;
  return { prefix: m[1], type: PREFIX_TO_TYPE[m[1]], id: m[2], slug: m[3] };
}

/**
 * Minimal parser for the flat metadata.yml format in intents/_templates —
 * `key: value` lines, `#` comments, and `- item` list entries under a key
 * with an empty value. Not a general YAML parser, deliberately: the format is
 * ours, and a dependency for six keys is not worth it.
 */
export function parseMetadata(text) {
  const out = {};
  let listKey = null;
  for (const raw of text.split(/\r?\n/)) {
    const line = stripComment(raw);
    if (!line.trim()) continue;
    const item = /^\s+-\s+(.*)$/.exec(line);
    if (item && listKey) {
      out[listKey].push(unquote(item[1]));
      continue;
    }
    const kv = /^([A-Za-z_][\w-]*):\s*(.*)$/.exec(line);
    if (!kv) continue;
    const [, key, value] = kv;
    if (value === '' || value === '[]') {
      out[key] = [];
      listKey = key;
    } else {
      out[key] = unquote(value);
      listKey = null;
    }
  }
  return out;
}

/** Drops a `#` comment, but not a `#` inside a quoted value ("Fix #12"). */
function stripComment(line) {
  let quote = null;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (quote) {
      if (c === quote) quote = null;
    } else if ((c === '"' || c === "'") && /(^|[:-])\s*$/.test(line.slice(0, i))) {
      // A quote opens only at the start of a value (after `key:` or `- `),
      // so the apostrophe in `title: it's fine  # note` is just a letter.
      quote = c;
    } else if (c === '#' && (i === 0 || /\s/.test(line[i - 1]))) {
      return line.slice(0, i).trimEnd();
    }
  }
  return line;
}

/** The four gate fields of metadata.yml (intents/README.md → "Gates"). */
export const GATE_FIELDS = ['intent_accepted', 'spec_accepted', 'plan_approved', 'live_checked'];

const GATE_RE = /^(\d{4}-\d{2}-\d{2})( by-agent)?$/;

/**
 * Reads one gate value. Empty (absent, `[]`) is not recorded; a bare date was
 * written by the owner; `<date> by-agent` was written by an agent on the
 * owner's request (intents/README.md → "Who edits what"); anything else
 * (TBD, yes, ~, a date plus another token) is malformed, never "not recorded".
 *
 * @returns {{state:'empty'}|{state:'recorded',date:string,by:'owner'|'agent'}|{state:'malformed',value:unknown}}
 */
export function parseGate(value) {
  if (value === undefined || (Array.isArray(value) && value.length === 0)) return { state: 'empty' };
  const m = typeof value === 'string' ? GATE_RE.exec(value) : null;
  if (!m) return { state: 'malformed', value };
  return { state: 'recorded', date: m[1], by: m[2] ? 'agent' : 'owner' };
}

/**
 * Auto-mode fields (intents/README.md → "Who edits what").
 * `auto_authorized` reuses the gate grammar (a date, or a date plus
 * "by-agent") and is NOT a gate: nothing waits on it. `auto_round` is the
 * review round a stopped run is in (1 to 3, the cap); `auto_stopped` is the
 * reason, written without " #" because stripComment would cut it there.
 */
export const AUTO_FIELDS = ['auto_authorized', 'auto_round', 'auto_stopped'];

/** Highest review round an auto run may record (at most three). */
export const AUTO_MAX_ROUND = 3;

const ROUND_RE = /^[1-9]\d*$/;

/**
 * @returns {{authorized: ReturnType<typeof parseGate>, round: number|null, stopped: string|null}}
 */
export function parseAuto(metadata) {
  const m = metadata ?? {};
  const rawRound = m.auto_round;
  const hasRound = typeof rawRound === 'string' && rawRound !== '';
  const roundOk = hasRound && ROUND_RE.test(rawRound);
  const stopped = typeof m.auto_stopped === 'string' && m.auto_stopped !== '' ? m.auto_stopped : null;
  return {
    authorized: parseGate(m.auto_authorized),
    round: roundOk ? Number(rawRound) : null,
    stopped,
  };
}

function unquote(v) {
  const s = v.trim();
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) return s.slice(1, -1);
  return s;
}

// Path rules. TEST_RE is language-neutral. CORE_CODE (set by §1, stack
// Python) is the modules whose mistakes cost most: the agent loop, the
// catalogue search, the guardrails and the model interface. cli, config and
// tracing are wiring and I/O, and the live check covers them.
const TEST_RE = [
  /\.(test|spec)\.[cm]?[jt]sx?$/, // JS/TS
  /(^|\/)test_[^/]+\.py$/, // pytest
  /_test\.(py|go)$/,
  /(^|\/)(tests?|__tests__)\//, // anything under a test directory
];
export const CORE_CODE = [
  /^src\/advisor\/(agent|catalogue|guardrails)\.py$/,
  /^src\/advisor\/models\//,
  // The eval scorers decide pass or fail; the runner (run.py) is I/O.
  /^src\/advisor\/evals\/(cases|score)\.py$/,
];

const isTest = (p) => TEST_RE.some((re) => re.test(p));
const isCoreCode = (p) => CORE_CODE.some((re) => re.test(p)) && !isTest(p);
const isIntentArtefact = (p) => p.startsWith('intents/');
// Code, as far as the gates care: anything that is not an intent artefact,
// documentation or a test. A test written before the plan is approved is
// harmless; a config or source file is not.
const isSource = (p) => !isIntentArtefact(p) && !p.startsWith('docs/') && !p.endsWith('.md') && !isTest(p);

/**
 * Checks one change against its intent.
 *
 * @param {object} input
 * @param {string} input.branch          branch name
 * @param {object|null} input.metadata   parsed metadata.yml, or null if the folder is missing
 * @param {string|null} input.intentDir  e.g. "intents/27-ticket-intake", or null
 * @param {string[]} input.intentFiles   file names present in that folder
 * @param {{path:string, added:number, deleted:number}[]} input.diff  numstat vs. the merge base
 * @returns {{errors:string[], routes:string[], notes:string[], type:string|null, id:string|null}}
 *   errors block the change; routes say the declared type does not fit what
 *   arrived (the change should take the fuller path); notes are informational.
 */
export function checkChange({ branch, metadata, intentDir, intentFiles, diff, review = null }) {
  const errors = [];
  const routes = [];
  const notes = [];
  const parsed = parseBranch(branch);
  if (!parsed) {
    errors.push(
      `Branch "${branch}" carries no intent id. Name it <prefix>/<id>-<slug>, prefix one of ${Object.keys(PREFIX_TO_TYPE).join(', ')} (e.g. feat/2-first-feature).`,
    );
    return { errors, routes, notes, type: null, id: null };
  }
  const { id } = parsed;
  if (!metadata || !intentDir) {
    errors.push(`No intents/${id}-*/metadata.yml found for intent ${id}. Run /intent to draft it.`);
    return { errors, routes, notes, type: parsed.type, id };
  }

  const declared = metadata.type;
  if (!TYPE_RULES[declared]) {
    errors.push(`${intentDir}/metadata.yml: type "${declared}" is not one of ${Object.keys(TYPE_RULES).join(', ')}.`);
    return { errors, routes, notes, type: declared ?? null, id };
  }
  if (String(metadata.id) !== id) errors.push(`${intentDir}/metadata.yml: id "${metadata.id}" does not match branch id "${id}".`);
  if (declared !== parsed.type) {
    errors.push(`Branch prefix "${parsed.prefix}/" says ${parsed.type}, but ${intentDir}/metadata.yml declares ${declared}. Make them agree.`);
  }

  const rules = TYPE_RULES[declared];
  for (const f of rules.files) {
    if (!intentFiles.includes(f)) errors.push(`${declared} intents need ${intentDir}/${f}.`);
  }
  const touchesSource = diff.some((d) => isSource(d.path));
  for (const gate of rules.gates) {
    if (parseGate(metadata[gate]).state === 'recorded') continue;
    // A gate not passed yet is fine while only artefacts change; it is a gate
    // violation once code arrives. A malformed one is reported below either way.
    if (parseGate(metadata[gate]).state === 'malformed') continue;
    const msg = `Gate "${gate}" is not recorded (as YYYY-MM-DD) in ${intentDir}/metadata.yml.`;
    if (touchesSource) errors.push(`${msg} Code changed before the gate was passed.`);
    else notes.push(msg);
  }
  for (const gate of GATE_FIELDS) {
    if (parseGate(metadata[gate]).state === 'malformed') {
      errors.push(
        `${intentDir}/metadata.yml: ${gate} must be empty, a YYYY-MM-DD date (you recorded it), or a date plus "by-agent" (an agent recorded it on your request); got ${JSON.stringify(metadata[gate])}.`,
      );
    }
  }

  checkAuto(metadata, intentDir, errors);
  checkLiveCheck({ review, metadata, intentDir }, errors);
  checkShape(declared, diff, routes, notes);
  return { errors, routes, notes, type: declared, id };
}

/** A malformed auto field is an error; a gate's own grammar is untouched. */
function checkAuto(metadata, intentDir, errors) {
  const auto = parseAuto(metadata);
  if (auto.authorized.state === 'malformed') {
    errors.push(
      `${intentDir}/metadata.yml: auto_authorized must be empty, a YYYY-MM-DD date, or a date plus "by-agent"; got ${JSON.stringify(metadata.auto_authorized)}.`,
    );
  }
  const raw = metadata.auto_round;
  const present = raw !== undefined && !(Array.isArray(raw) && raw.length === 0);
  if (present && (auto.round === null || auto.round > AUTO_MAX_ROUND)) {
    errors.push(`${intentDir}/metadata.yml: auto_round must be a whole number from 1 to ${AUTO_MAX_ROUND}; got ${JSON.stringify(raw)}.`);
  }
}

const LIVE_CHECK_VALUES = ['owed', 'not-needed'];

/**
 * REVIEW-POLICY.md → "Live checks": a review that says `live-check: owed`
 * blocks the merge until the owner records `live_checked: <date>` (or an agent on their request). Unlike
 * the plan gates this does not wait for source code to change: it is a
 * condition on the merge, and a docs-only change can owe one too.
 */
function checkLiveCheck({ review, metadata, intentDir }, errors) {
  // A malformed value is reported with the other gates, so it is not also "owed".
  const recorded = parseGate(metadata.live_checked).state !== 'empty';
  const state = review?.['live-check'];
  if (state === undefined) return;
  if (!LIVE_CHECK_VALUES.includes(state)) {
    errors.push(`${intentDir}/review.md: live-check: "${state}" is not a value; use live-check: "owed" or "not-needed".`);
  } else if (state === 'owed' && !recorded) {
    errors.push(
      `A live check is owed and not recorded. Do the steps in ${intentDir}/review.md → ## Live check, then set live_checked: <date> in ${intentDir}/metadata.yml.`,
    );
  }
}

/**
 * The current round's header of a review.md: the `key: value` lines before its
 * first `## ` section. Stopping there keeps report text (a pasted
 * `type-check: PASS`) and earlier rounds, below `# Round N (history)`, from
 * ever being read as the current header.
 */
export function parseReviewHeader(text) {
  const out = {};
  for (const raw of text.split(/\r?\n/)) {
    if (/^## |^# Round\b/.test(raw)) break;
    const kv = /^([a-z][\w-]*):\s*(.*?)\s*$/.exec(raw);
    if (kv) out[kv[1]] = kv[2];
  }
  return out;
}

/** Compares what arrived against what the declared type should look like. */
function checkShape(type, diff, routes, notes) {
  const code = diff.filter((d) => !isIntentArtefact(d.path));
  const lines = code.reduce((n, d) => n + d.added + d.deleted, 0);
  const testsTouched = code.some((d) => isTest(d.path));
  const coreCodeTouched = code.some((d) => isCoreCode(d.path));
  notes.push(`${code.length} file(s), ${lines} line(s) changed outside intents/.`);

  if (type === 'adjustment') {
    if (code.length > ADJUSTMENT_LIMITS.files || lines > ADJUSTMENT_LIMITS.lines) {
      routes.push(
        `Declared adjustment, but ${code.length} files / ${lines} lines changed (limit ${ADJUSTMENT_LIMITS.files} / ${ADJUSTMENT_LIMITS.lines}). Route to fix or feature.`,
      );
    }
    if (coreCodeTouched) routes.push('Declared adjustment, but core code (CORE_CODE in scripts/intent-check-lib.mjs) changed. Route to fix or feature.');
  }
  if (type === 'fix' && !testsTouched && code.length > 0) {
    routes.push('Declared fix, but no test changed. A fix carries a test so the defect cannot come back.');
  }
  if (type === 'refactor') {
    const testDeletions = code.filter((d) => isTest(d.path) && d.deleted > 0).map((d) => d.path);
    if (testDeletions.length) {
      routes.push(`Declared refactor, but existing tests lost lines (${testDeletions.join(', ')}). Behaviour may have changed — check, or route to feature.`);
    }
  }
  if ((type === 'feature' || type === 'fix') && coreCodeTouched && !testsTouched) {
    routes.push('Core code (CORE_CODE in scripts/intent-check-lib.mjs) changed with no test change.');
  }
}

/**
 * Parses check-intent's CLI: `[<branch>] [--base <ref> | --base=<ref>]`.
 * Throws on an unknown flag or a `--base` without a value, so a typo can't
 * silently check the wrong thing.
 */
export function parseArgs(argv) {
  let base = 'main';
  let branch = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--base') {
      const v = argv[i + 1];
      if (!v || v.startsWith('--')) throw new Error('--base needs a value, e.g. --base main');
      base = v;
      i++;
    } else if (a.startsWith('--base=')) {
      base = a.slice('--base='.length);
      if (!base) throw new Error('--base needs a value, e.g. --base=main');
    } else if (a.startsWith('--')) {
      throw new Error(`Unknown option ${a}`);
    } else if (branch === null) {
      branch = a;
    } else {
      throw new Error(`Unexpected argument ${a} — pass at most one branch`);
    }
  }
  return { branch, base };
}

/** Formats a result as the "Type check" block the review report embeds. */
export function formatResult(r) {
  const verdict = r.errors.length ? 'FAIL' : r.routes.length ? 'ROUTE' : 'PASS';
  const out = [`type-check: ${verdict}${r.id ? ` (intent ${r.id}, ${r.type})` : ''}`];
  for (const e of r.errors) out.push(`  error: ${e}`);
  for (const x of r.routes) out.push(`  route: ${x}`);
  for (const n of r.notes) out.push(`  note:  ${n}`);
  return { verdict, text: out.join('\n') };
}
