// Pure logic behind `npm run ship`: the merge preconditions of
// REVIEW-POLICY.md → "Merging", the metadata.yml bookkeeping edit,
// the resumable step plan and the merge message. No git, no fs: tested in
// ship-lib.test.mjs. The git half is scripts/ship.mjs.

/** The seven steps of a ship run, in order. */
export const STEPS = [
  { id: 'live-check', label: 'record the live check on the branch' },
  { id: 'preconditions', label: 'check the merge preconditions' },
  { id: 'merge', label: 'merge --no-ff into main' },
  { id: 'verify', label: 'npm run verify on main' },
  { id: 'bookkeeping', label: 'bookkeeping commit (metadata.yml)' },
  { id: 'push', label: 'push main to origin (when there is one)' },
  { id: 'remove', label: 'remove the worktree and delete the branch' },
];

/**
 * The step plan: each step is `done` when its effect is already there,
 * `n/a` for the live check when the owner didn't give their word and for the
 * push when the repository has no `origin` (a local-only repository: nothing
 * to push to, so the step is skipped, not failed), and `todo` otherwise. A
 * re-run therefore resumes where the last one stopped.
 *
 * @param {{liveCheckRequested:boolean, liveCheckRecorded:boolean, merged:boolean,
 *          bookkept:boolean, pushed:boolean, cleanedUp:boolean, hasRemote?:boolean}} s
 */
export function planSteps(s) {
  const doneBy = {
    'live-check': s.liveCheckRecorded || s.merged,
    preconditions: s.merged,
    merge: s.merged,
    verify: s.bookkept,
    bookkeeping: s.bookkept,
    push: s.pushed,
    remove: s.cleanedUp,
  };
  return STEPS.map((step) => {
    if (doneBy[step.id]) return { ...step, status: 'done' };
    if (step.id === 'live-check' && !s.liveCheckRequested) return { ...step, status: 'n/a' };
    if (step.id === 'push' && s.hasRemote === false) return { ...step, status: 'n/a' };
    return { ...step, status: 'todo' };
  });
}

/** Ways a line that mentions a reason says there is none (one alternative each; ship-lib.test.mjs has a phrase per entry). */
const NO_REASON = [
  /\b(?:no|not|without|missing)\s+(?:\w+\s+)?reason\b/i, // "no reason found"
  /\breason\s+(?:not|unknown|missing|unclear)\b/i, // "reason unclear"
  /\breason\s*:\s*(?:none|unknown|n\/a|tbd)\b/i, // "reason: none"
  /\bnot\s+(?:stated|given|explained)\b/i, // "the reason was not given"
  /\b(?:is|was)n['’]t\s+(?:stated|given|explained)\b/i, // "the reason isn't stated"
  /\bto be (?:decided|determined)\b|\bleft to the owner\b/i, // "reason to be decided by the owner"
];

/**
 * Whether review.md states why a ROUTE is fine (REVIEW-POLICY.md says only
 * "ROUTE with the reason already stated in review.md"). Interpretation: in
 * the current round only (everything before a `# Round N (history)` heading;
 * earlier rounds never count), outside the `## Type check` section (which
 * only pastes the tool's output), a line has both the word ROUTE in capitals
 * and the word "reason" ("ROUTE, reason stated", "ROUTE, reason above",
 * "... Reason:"), without saying there is none ("no
 * reason found", "not stated"). A pasted "check:intent -> ROUTE (exit 2)", a
 * Passes row "| 2 | Type check | ROUTE |" or a lowercase "route" in prose say
 * nothing about why, so the run stops and the owner decides.
 */
export function routeReasonStated(reviewText) {
  const negated = (line) => NO_REASON.some((re) => re.test(line));
  let inTypeCheck = false;
  for (const line of reviewText.split(/\r?\n/)) {
    if (/^# Round\b/.test(line)) break;
    if (/^## /.test(line)) inTypeCheck = /^## Type check\b/.test(line);
    if (inTypeCheck) continue;
    if (/\bROUTE\b/.test(line) && /\breason\b/i.test(line) && !negated(line)) return true;
  }
  return false;
}

/**
 * REVIEW-POLICY.md → "Merging", preconditions 1 to 3, from values the caller
 * read out of git. `checkIntent` is left out to evaluate precondition 1 alone.
 *
 * @param {{reviewHeader:Record<string,string>|null, isAncestor:boolean, changedFiles:string[],
 *          intentDir:string, checkIntent?:{verdict:'PASS'|'ROUTE'|'FAIL', reasonStated:boolean}}} input
 * @returns {{ok:true}|{ok:false, failed:string, message:string}}
 */
export function checkPreconditions({ reviewHeader, isAncestor, changedFiles, intentDir, checkIntent }) {
  const fail = (failed, message) => ({ ok: false, failed, message });
  if (!reviewHeader) return fail('verdict', `${intentDir}/review.md is not committed on the branch.`);
  const verdict = reviewHeader.verdict;
  if (verdict !== 'attest' && verdict !== 'escalate') {
    return fail('verdict', `the committed review.md verdict is "${verdict ?? 'missing'}", not attest or escalate.`);
  }
  if (!reviewHeader['reviewed-commit']) return fail('reviewed-commit', 'review.md has no reviewed-commit.');
  if (!isAncestor) {
    return fail(
      'reviewed-commit',
      `reviewed-commit ${reviewHeader['reviewed-commit']} is not an ancestor of the branch (rebased since the review: a new round is needed).`,
    );
  }
  const allowed = new Set([`${intentDir}/review.md`, `${intentDir}/metadata.yml`]);
  const stray = changedFiles.filter((f) => !allowed.has(f));
  if (stray.length) {
    return fail('unreviewed-changes', `changed since the reviewed commit besides review.md and metadata.yml: ${stray.join(', ')}.`);
  }
  if (!checkIntent) return { ok: true };
  if (checkIntent.verdict === 'FAIL') return fail('check-intent', 'npm run check:intent reports FAIL for the branch.');
  if (checkIntent.verdict === 'ROUTE' && !checkIntent.reasonStated) {
    return fail('check-intent', 'npm run check:intent reports ROUTE and review.md does not state the reason.');
  }
  return { ok: true };
}

/** Splits text into lines keeping each line's own ending, so an edit can put it back unchanged. */
function splitLines(text) {
  return text.match(/[^\n]*\n|[^\n]+$/g) ?? [];
}

function endingOf(line) {
  if (line.endsWith('\r\n')) return '\r\n';
  return line.endsWith('\n') ? '\n' : '';
}

/**
 * Sets top-level `key: value` lines of a metadata.yml, replacing the whole
 * line (its old comment included) and keeping every other line and each line's
 * ending exactly. Throws when a key is absent: the template always has them.
 */
export function setKeys(text, values) {
  const pending = new Map(Object.entries(values));
  const out = splitLines(text).map((line) => {
    const m = /^([A-Za-z_][\w-]*):/.exec(line);
    if (!m || !pending.has(m[1])) return line;
    const value = pending.get(m[1]);
    pending.delete(m[1]);
    return `${m[1]}: ${value}${endingOf(line)}`;
  });
  if (pending.size) throw new Error(`metadata.yml has no ${[...pending.keys()].join(', ')} line`);
  return out.join('');
}

/** `merged:` and `status: done`. */
export function markMerged(text, hash, date) {
  return setKeys(text, {
    merged: `${hash}    # ${date}, merged by Claude on the owner's explicit request in chat`,
    status: 'done',
  });
}

/** `live_checked:` on the owner's word; `words` is quoted, so any " in it becomes '. */
export function markLiveChecked(text, date, words) {
  return setKeys(text, { live_checked: `${date} by-agent    # owner: "${words.replace(/"/g, "'")}"` });
}

/** Whether metadata (parsed) already carries the bookkeeping: `status: done` and a merge hash. */
export function isBookkept(metadata) {
  const merged = typeof metadata.merged === 'string' && metadata.merged !== ''; // an empty `merged:` parses as []
  return metadata.status === 'done' && merged;
}

/** Commit message: subject, then the caller's attribution lines after a blank line. */
export function commitMessage(subject, trailers = []) {
  const lines = trailers.map((t) => t.trim()).filter(Boolean);
  return lines.length ? `${subject}\n\n${lines.join('\n')}\n` : `${subject}\n`;
}

/** The merge commit message. */
export function mergeMessage(id, title, trailers = []) {
  return commitMessage(`Merge §${id}: ${title}`, trailers);
}
