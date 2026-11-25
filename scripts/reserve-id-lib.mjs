// The decisions of `npm run reserve-id -- <id>` that need no repository: the
// arguments, what origin already holds, what the reservation commit may carry.
// The git half is reserve-id.mjs.

export const EXIT = { OK: 0, REFUSED: 1, NO_REMOTE: 2, REMOTE_FAILED: 3 };

/** The only two files a reservation carries, in a folder `intents/<id>-<slug>/`. */
export const RESERVE_FILES = ['intent.md', 'metadata.yml'];

/** `{ id }` for exactly one argument that is a positive integer with no leading zero, else `{ error }`. */
export function parseReserveArgs(argv) {
  if (argv.length !== 1 || !/^[1-9]\d*$/.test(argv[0])) {
    return { error: 'usage: npm run reserve-id -- <id>   (one intent number, no leading zeros)' };
  }
  return { id: argv[0] };
}

/** The branch a reservation lives on. */
export function reservationRef(id) {
  return `refs/heads/intent/${id}`;
}

/** The reservation commit's subject; `dir` is `intents/<id>-<slug>`. */
export function reservationSubject(id, dir) {
  return `§${id}: number reserved (${dir})`;
}

/** The one push: this commit to the new branch, no force, no `main`, no deletion. */
export function pushArgs(commit, id) {
  return ['push', 'origin', `${commit}:${reservationRef(id)}`];
}

const folderOf = (names, id) => (names ?? []).filter((n) => n.startsWith(`${id}-`));

/**
 * What to do, from what origin holds (B3.4 to B3.6). `dir` is the draft's
 * folder name (`23-a`), `originMainDirs` the folder names in origin/main's
 * intents/, `reservationDirs` those in origin/intent/<id>'s intents/ (null
 * when that branch does not exist).
 */
export function decide({ id, dir, originMainDirs = [], reservationDirs = null }) {
  const onMain = folderOf(originMainDirs, id);
  if (onMain.includes(dir)) return { action: 'already-on-main', exit: EXIT.OK, message: `§${id} is already on origin/main (intents/${dir}); nothing to reserve` };
  const taken = (other, where) => ({
    action: 'taken',
    exit: EXIT.REFUSED,
    message: `§${id} is taken on origin by intents/${other} (${where}); take \`npm run queue -- --next-id\` and renumber the draft`,
  });
  if (onMain.length > 0) return taken(onMain[0], 'origin/main');
  if (reservationDirs !== null) {
    const held = folderOf(reservationDirs, id);
    if (held.includes(dir)) return { action: 'already-reserved', exit: EXIT.OK, message: `§${id} is already reserved on origin as intent/${id} (intents/${dir})` };
    return taken(held[0] ?? `${id}-?`, `origin/intent/${id}`);
  }
  return { action: 'reserve', exit: null, message: '' };
}

/**
 * Is the commit safe to push (B3.7)? `parents` the commit's parent hashes,
 * `paths` every file path in its tree, `dir` the full `intents/<id>-<slug>`.
 * Null when it is, else the reason.
 */
export function checkCarried({ parents = [], paths = [], dir }) {
  if (parents.length > 0) return 'the reservation commit has a parent';
  const allowed = RESERVE_FILES.map((f) => `${dir}/${f}`);
  for (const p of paths) if (!allowed.includes(p)) return `the reservation commit would carry ${p}`;
  if (!paths.includes(`${dir}/metadata.yml`)) return 'the reservation commit does not hold metadata.yml';
  return null;
}
