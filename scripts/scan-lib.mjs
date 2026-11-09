// Pure logic behind the metadata checks of `npm run sdlc:scan`. Kept
// free of git/fs calls so it can be unit-tested; see scan-lib.test.mjs. The
// git lookup is injected as `isCommit`.
import { GATE_FIELDS, parseGate, parseReviewHeader } from './intent-check-lib.mjs';

// Anything else never reaches git: a value starting with `-` would be read as an option.
const HASH_RE = /^[0-9a-f]{7,40}$/;

/**
 * Bad values in intents' metadata.yml: a `merged:` that is not a hash or does
 * not resolve to a commit, and any malformed gate value.
 *
 * @param {{id:unknown, merged:string|null, gates:Record<string,unknown>}[]} intents
 * @param {(hash:string) => boolean} isCommit
 * @returns {{id:unknown, field:string, value:unknown, why:string}[]}
 */
export function metadataProblems(intents, isCommit) {
  const problems = [];
  for (const i of intents) {
    if (i.merged) {
      if (!HASH_RE.test(i.merged)) problems.push({ id: i.id, field: 'merged', value: i.merged, why: 'not a commit hash' });
      else if (!isCommit(i.merged)) problems.push({ id: i.id, field: 'merged', value: i.merged, why: 'does not resolve to a commit' });
    }
    for (const field of GATE_FIELDS) {
      if (parseGate(i.gates[field]).state === 'malformed') {
        problems.push({ id: i.id, field, value: i.gates[field], why: 'not empty, a date, or a date plus "by-agent"' });
      }
    }
  }
  return problems;
}

/** Per gate field, how many recorded values the owner typed and how many an agent did. */
export function gateShares(intents) {
  const out = {};
  for (const field of GATE_FIELDS) {
    out[field] = { owner: 0, agent: 0 };
    for (const i of intents) {
      const g = parseGate(i.gates[field]);
      if (g.state === 'recorded') out[field][g.by] += 1;
    }
  }
  return out;
}

// Which skill is allowed to have written each artefact: a stamp names
// the skill, so a spec only counts as skill-made when /spec stamped it.
const ARTEFACT_SKILL = { 'spec.md': 'product-advice-agent/spec', 'plan.md': 'product-advice-agent/build-plan' };

/**
 * Per artefact (spec.md, plan.md): how many files the step's skill made
 * (stamp name matches the file), how many are hand-made under another stamp,
 * and how many are unstamped. An intent without the file is counted nowhere.
 * The stamp is `name@version`, as sdlc-scan.mjs reads it; any version counts.
 *
 * @param {{stamps:Record<string,string|null>}[]} intents
 * @returns {Record<string,{skill:number, hand:number, unstamped:number}>}
 */
export function artefactOrigins(intents) {
  const out = {};
  for (const [file, skill] of Object.entries(ARTEFACT_SKILL)) {
    out[file] = { skill: 0, hand: 0, unstamped: 0 };
    for (const i of intents) {
      if (!(file in i.stamps)) continue;
      const stamp = i.stamps[file];
      if (!stamp) out[file].unstamped += 1;
      else if (stamp.split('@')[0] === skill) out[file].skill += 1;
      else out[file].hand += 1;
    }
  }
  return out;
}

/**
 * Quality per review tier (REVIEW-POLICY.md "Against rubber-stamping").
 * Only merged changes inside the window count. A follow-up is a fix intent
 * whose `follows_up:` names the intent whose change caused the defect; it
 * counts against the tier that change was reviewed at. A revert counts
 * against the tier of the § its subject names.
 *
 * @param {{intents: {id:unknown, type:unknown, followsUp:string|null, review:{tier:string|null}|null}[],
 *          reverts: {subject:string}[], mergedInWindow: (intent:object) => boolean}} input
 * @returns {Record<string, {changes:number, followUps:number, reverts:number}>}
 */
export function qualityByTier({ intents, reverts, mergedInWindow }, runKind = null) {
  const tierOf = new Map(intents.filter((i) => i.review?.tier && mergedInWindow(i)).map((i) => [String(i.id), i.review.tier]));
  // runKind narrows the counts to the changes of one run kind;
  // a follow-up or revert goes to the run kind of the change it names.
  const runOfId = new Map(intents.map((i) => [String(i.id), runOf(i.review)]));
  const keep = (id) => runKind === null || runOfId.get(id) === runKind;
  const perTier = {};
  const bump = (tier, key) => {
    perTier[tier] ??= { changes: 0, followUps: 0, reverts: 0 };
    perTier[tier][key] += 1;
  };
  for (const [id, tier] of tierOf) if (keep(id)) bump(tier, 'changes');
  for (const i of intents.filter((x) => x.type === 'fix' && x.followsUp)) {
    if (tierOf.has(i.followsUp) && keep(i.followsUp)) bump(tierOf.get(i.followsUp), 'followUps');
  }
  for (const c of reverts) {
    const id = /§\s?(\d+)/.exec(c.subject)?.[1];
    if (id && tierOf.has(id) && keep(id)) bump(tierOf.get(id), 'reverts');
  }
  return perTier;
}

/**
 * The run kind a review records in its `run:` header line (REVIEW-POLICY.md →
 * "The report"). A review with no `run:` line predates auto mode, and any
 * value but `auto` is manual, so old reviews stay in the manual bucket.
 */
export function runOf(review) {
  return review?.run === 'auto' ? 'auto' : 'manual';
}

/** Per run kind, the same per-tier counts as qualityByTier. */
export function qualityByRun(input) {
  return { auto: qualityByTier(input, 'auto'), manual: qualityByTier(input, 'manual') };
}

/** Sampling rate per run kind: every Nth attested change gets a full diff read (REVIEW-POLICY.md → "Sampling"). */
export const SAMPLE_EVERY = { auto: 3, manual: 5 };

/**
 * Is the next attested change of this run kind the one to sample? Counts the
 * attested reviews already recorded for that run kind, separately from the
 * other kind; `excludeId` leaves out the intent under review, whose earlier
 * rounds must not count as another change.
 *
 * @param {{reviews: {id?:unknown, verdict:string|null, run?:string|null}[], run:'auto'|'manual', excludeId?:unknown}} input
 * @returns {{nth:number, due:boolean, every:number}}
 */
export function sampleDue({ reviews, run, excludeId = null }) {
  const every = SAMPLE_EVERY[run];
  if (!every) throw new Error(`unknown run kind "${run}"`);
  const prior = reviews.filter(
    (r) => r.verdict === 'attest' && runOf(r) === run && (excludeId === null || String(r.id) !== String(excludeId)),
  ).length;
  const nth = prior + 1;
  return { nth, due: nth % every === 0, every };
}

/**
 * The review fields the scan reads from a review.md. `run` comes only from
 * the header (parseReviewHeader) and only when it is exactly `auto` or
 * `manual`: a review that copied the template line `run: auto | manual`
 * literally is neither, so it reads as null and counts as manual (runOf).
 */
export function parseReviewFields(text) {
  const field = (k) => new RegExp(`^${k}:\\s*(\\S+)`, 'm').exec(text)?.[1] ?? null;
  const run = parseReviewHeader(text).run;
  return {
    verdict: field('verdict'),
    tier: field('tier'),
    round: field('round'),
    sampled: field('sampled'),
    run: run === 'auto' || run === 'manual' ? run : null,
  };
}

const SAMPLE_USAGE = 'usage: sdlc:scan -- --sample-due <auto|manual> [--exclude <id>]';

/**
 * `npm run sdlc:scan -- --sample-due <auto|manual> [--exclude <id>]`: null when
 * the flag is absent (the normal scan runs), else what to print and the exit
 * code. A missing or unknown value is a usage error (exit 2), never the full
 * report with exit 0.
 *
 * @returns {null|{exit:number, stdout?:string, stderr?:string}}
 */
export function sampleDueCommand(args, intents) {
  const at = args.indexOf('--sample-due');
  if (at < 0) return null;
  const run = args[at + 1];
  if (!['auto', 'manual'].includes(run)) return { exit: 2, stderr: SAMPLE_USAGE };
  const ex = args.indexOf('--exclude');
  const excludeId = ex >= 0 ? args[ex + 1] : null;
  if (ex >= 0 && (excludeId === undefined || excludeId.startsWith('--'))) return { exit: 2, stderr: SAMPLE_USAGE };
  const reviews = intents.filter((i) => i.review).map((i) => ({ id: i.id, ...i.review }));
  const s = sampleDue({ reviews, run, excludeId });
  return { exit: 0, stdout: `sample-due ${run}: nth attested ${run} change = ${s.nth}, every ${s.every}, sampled: ${s.due ? 'yes' : 'no'}` };
}
