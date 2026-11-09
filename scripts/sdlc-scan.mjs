#!/usr/bin/env node
// `npm run sdlc:scan [-- --since 2025-10-01] [--json]`
// `npm run sdlc:scan -- --sample-due <auto|manual> [--exclude <id>]` prints whether the next
// attested change of that run kind is the one REVIEW-POLICY.md says to sample.
//
// Reads what each SDLC level leaves behind — context file, one-command
// verification, intents/ contents, skill stamps, review verdicts — plus the
// outcome measures from git history (throughput, intent-id reference rate,
// revert rate). /grid uses this to pre-fill docs/sdlc-grid.md; nobody should
// gather these numbers by hand.
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { GATE_FIELDS, parseMetadata } from './intent-check-lib.mjs';
import { artefactOrigins, gateShares, metadataProblems, qualityByRun, parseReviewFields, qualityByTier, sampleDueCommand } from './scan-lib.mjs';

const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const since = flag('--since') ?? isoDaysAgo(365);
const asJson = args.includes('--json');
const git = (...a) => execFileSync('git', a, { encoding: 'utf8' }).trim();

function isoDaysAgo(n) {
  return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
}

// --- Agent-readiness (org rule 1) -----------------------------------------
const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
const readiness = {
  contextFile: existsSync('CLAUDE.md'),
  verifyCommand: Boolean(pkg.scripts?.verify),
  lint: Boolean(pkg.scripts?.lint),
  reviewPolicy: existsSync('REVIEW-POLICY.md'),
  typeCheck: Boolean(pkg.scripts?.['check:intent']),
};

// --- Intents and their artefacts ------------------------------------------
const STAMP_RE = /<!--\s*generated-by:\s*([^\s]+)\s*-->/;
const intents = [];
if (existsSync('intents')) {
  for (const dir of readdirSync('intents')) {
    const path = join('intents', dir);
    if (dir.startsWith('_') || !existsSync(join(path, 'metadata.yml'))) continue;
    const meta = parseMetadata(readFileSync(join(path, 'metadata.yml'), 'utf8'));
    const files = readdirSync(path);
    const stamps = {};
    for (const f of files.filter((x) => x.endsWith('.md'))) {
      const m = STAMP_RE.exec(readFileSync(join(path, f), 'utf8'));
      stamps[f] = m ? m[1] : null;
    }
    let review = null;
    if (files.includes('review.md')) {
      const text = readFileSync(join(path, 'review.md'), 'utf8');
      review = parseReviewFields(text);
    }
    const followsUp = typeof meta.follows_up === 'string' ? meta.follows_up : null;
    const merged = typeof meta.merged === 'string' ? meta.merged : null;
    const gates = Object.fromEntries(GATE_FIELDS.map((k) => [k, meta[k]]));
    intents.push({ dir, id: meta.id, type: meta.type, status: meta.status, files, stamps, review, followsUp, merged, gates });
  }
}
// --- `--sample-due`: the sampling rule, nothing else -----------------------
const sampleDueOut = sampleDueCommand(args, intents);
if (sampleDueOut) {
  if (sampleDueOut.stderr) console.error(sampleDueOut.stderr);
  if (sampleDueOut.stdout) console.log(sampleDueOut.stdout);
  process.exit(sampleDueOut.exit);
}
const countBy = (xs, key) => xs.reduce((acc, x) => ((acc[x[key] ?? 'unset'] = (acc[x[key] ?? 'unset'] ?? 0) + 1), acc), {});
const stamped = intents.filter((i) => Object.values(i.stamps).some(Boolean)).length;

// --- Outcome measures from main's first-parent history ---------------------
const log = git('log', '--first-parent', 'main', `--since=${since}`, '--format=%h%x09%ad%x09%s', '--date=short')
  .split('\n')
  .filter(Boolean)
  .map((l) => {
    const [hash, date, ...rest] = l.split('\t');
    return { hash, date, subject: rest.join('\t') };
  });
const isPlanOnly = (s) => /^Plan[:\s]/i.test(s);
const changes = log.filter((c) => !isPlanOnly(c.subject));
const referencesIntent = (s) => /§\s?\d+/.test(s) || /\b(feat|fix|refactor|adjust|exp)\/\d+-/.test(s);
const reverts = changes.filter((c) => /^Revert\b/.test(c.subject));
// Measure from the later of --since and the first change, so a young repo's
// throughput isn't diluted by weeks before it existed.
const firstChange = changes.length ? changes[changes.length - 1].date : since;
const windowStart = Math.max(new Date(since).getTime(), new Date(firstChange).getTime());
const weeks = Math.max(1, (Date.now() - windowStart) / (7 * 86400000));

// --- Quality per review tier (REVIEW-POLICY.md "Against rubber-stamping") --
// Only merged changes inside the window count. A follow-up is a fix intent
// whose `follows_up:` names the intent whose change caused the defect; it
// counts against the tier that change was reviewed at. A revert counts
// against the tier of the § its subject names.
const isCommit = (hash) => {
  try {
    git('rev-parse', '--verify', `${hash}^{commit}`);
    return true;
  } catch {
    return false; // hash not in this clone
  }
};
const problems = metadataProblems(intents, isCommit);
const mergedInWindow = (i) => {
  if (!i.merged || !isCommit(i.merged)) return false;
  return git('show', '-s', '--format=%as', i.merged) >= since;
};
const perTier = qualityByTier({ intents, reverts, mergedInWindow });
const perRun = qualityByRun({ intents, reverts, mergedInWindow });

const byMonth = {};
for (const c of changes) {
  const m = c.date.slice(0, 7);
  byMonth[m] = (byMonth[m] ?? 0) + 1;
}

const until = new Date().toISOString().slice(0, 10);
const report = {
  since,
  // The window the per-week figure divides by; record it with the number,
  // because the same history gives a different rate on a later day.
  window: { from: new Date(windowStart).toISOString().slice(0, 10), to: until },
  readiness,
  intents: {
    total: intents.length,
    byType: countBy(intents, 'type'),
    byStatus: countBy(intents, 'status'),
    withSkillStamp: stamped,
    artefactOrigins: artefactOrigins(intents),
    reviews: intents.filter((i) => i.review).map((i) => ({ id: i.id, ...i.review })),
  },
  outcome: {
    changesOnMain: changes.length,
    perWeek: Number((changes.length / weeks).toFixed(2)),
    intentReferenceRate: changes.length ? Number((changes.filter((c) => referencesIntent(c.subject)).length / changes.length).toFixed(2)) : 0,
    reverts: reverts.length,
    revertRate: changes.length ? Number((reverts.length / changes.length).toFixed(3)) : 0,
    byMonth,
  },
  perTier,
  perRun,
  problems,
  gateShares: gateShares(intents),
};

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  const yes = (b) => (b ? 'yes' : 'no');
  const r = report;
  console.log(`# SDLC scan (main, window ${r.window.from} → ${r.window.to})\n`);
  console.log('## Metadata problems');
  if (!r.problems.length) console.log('none');
  for (const p of r.problems) console.log(`§${p.id} ${p.field}: ${JSON.stringify(p.value)} — ${p.why}`);
  console.log('\n## Agent-readiness');
  console.log(`context file: ${yes(r.readiness.contextFile)} · verify: ${yes(r.readiness.verifyCommand)} · lint: ${yes(r.readiness.lint)} · review policy: ${yes(r.readiness.reviewPolicy)} · type check: ${yes(r.readiness.typeCheck)}\n`);
  console.log('## Intents');
  console.log(`total: ${r.intents.total} · by type: ${JSON.stringify(r.intents.byType)} · by status: ${JSON.stringify(r.intents.byStatus)} · skill-stamped: ${r.intents.withSkillStamp}`);
  for (const [file, o] of Object.entries(r.intents.artefactOrigins)) {
    console.log(`${file}: ${o.skill} by /${file === 'spec.md' ? 'spec' : 'build-plan'} · ${o.hand} hand (old stamp) · ${o.unstamped} unstamped`);
  }
  for (const rv of r.intents.reviews) console.log(`  review §${rv.id}: verdict ${rv.verdict}, tier ${rv.tier}, round ${rv.round}, sampled ${rv.sampled}, run ${rv.run ?? 'manual'}`);
  console.log('\n## Gates recorded (owner / agent)');
  for (const [field, n] of Object.entries(r.gateShares)) console.log(`${field}: ${n.owner} owner · ${n.agent} agent`);
  console.log('\n## Outcome (first-parent commits on main, plan-only commits excluded)');
  console.log(`changes: ${r.outcome.changesOnMain} · per week: ${r.outcome.perWeek} · reference an intent/§: ${Math.round(r.outcome.intentReferenceRate * 100)}% · reverts: ${r.outcome.reverts} (${(r.outcome.revertRate * 100).toFixed(1)}%)`);
  console.log(`by month: ${Object.entries(r.outcome.byMonth).sort().map(([m, n]) => `${m}=${n}`).join(' ')}`);
  console.log('\n## Quality per review tier (merged, reviewed intents in the window)');
  const tiers = Object.entries(r.perTier);
  if (!tiers.length) console.log('no merged, reviewed intents yet');
  for (const [tier, q] of tiers) console.log(`${tier}: ${q.changes} change(s) · ${q.followUps} follow-up fix(es) · ${q.reverts} revert(s)`);
  console.log('\n## Quality per review tier and run kind (a review with no run: line counts as manual)');
  for (const [run, perTierOfRun] of Object.entries(r.perRun)) {
    const rows = Object.entries(perTierOfRun);
    if (!rows.length) console.log(`${run}: none`);
    for (const [tier, q] of rows) console.log(`${run} · ${tier}: ${q.changes} change(s) · ${q.followUps} follow-up fix(es) · ${q.reverts} revert(s)`);
  }
}
