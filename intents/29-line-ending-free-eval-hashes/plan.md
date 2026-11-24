<!-- generated-by: product-advice-agent/build-plan@0.2.0 -->
# §29 plan — An eval run's content hashes depend on the checkout's line endings

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

A run report's `cases_sha256`, `catalogue_sha256` and `prompt_sha256` name
the content, not the checkout: each is the sha256 of the file's bytes with
every `\r\n` read as `\n`, computed by one pure helper that `run.py` and the
review's content check share. New reports say so with `"hash_form": "lf"`.
`compare` warns as today when two hashes of the same form differ, and says
plainly when it is comparing a raw-byte hash (before §29) with an `lf` one.
`evals/baseline.json` is rewritten from the same source run
(`20261124T210400Z-ollama.json`) by a command that first proves the run saw
the same content, so `compare` on `main` stops warning about identical
cases. The review's content check becomes one command,
`uv run advisor-analysis hashes <report>`, and the two skills that today say
"the sha256 of" the files name it instead.

## Risks

- **Tests that pass whatever the code does.** On a checkout with LF files
  (Linux, or `core.autocrlf=false`), raw-byte and `lf` hashes are equal, so a
  test that compares the report with "the hash of the file on disk" proves
  nothing. Every new test writes its inputs with `write_bytes` and explicit
  `\r\n` / `\n`, never `write_text` (which writes `\r\n` on Windows and `\n`
  elsewhere: `tests/test_evals_run.py:58` does exactly that today).
- **Over-normalising.** Stripping, `splitlines()` or text-mode reading would
  also hide trailing-whitespace or final-newline edits, which §13 B6 wants
  to show ("Bytes, so a whitespace-only edit changes it", `run.py:311-312`).
  Only the two-byte sequence `\r\n` is folded; a test pins that other
  whitespace and a lone `\r` still change the hash.
- **The baseline must not be hand-edited** (intent, Constraints). The new
  hashes come from `advisor-analysis baseline --rehash`, which refuses unless
  each old hash equals the raw, LF or CRLF form of the file now on disk.
- **Main's baseline may move before this merges.** If `/deliver` of another
  intent rewrites `evals/baseline.json` first, this branch conflicts on it.
  Resolution: take main's file, then re-run subtask 4 against the source run
  main's file names (its `source` field), and re-check with `hashes`.
- **Stale line citations.** §24 and §28 are open and touch `CLAUDE.md`,
  `README.md` and `REVIEW-POLICY.md` (prose only, not the lines cited
  below). Re-check the citations before launch.
- **In-flight reviews.** A branch not yet updated from `main` after this
  merges still has the old `run.py` (raw hashes) and the old skill text.
  `hashes` handles a raw-form report by checking raw bytes and saying so.
- **Pass 9** (`REVIEW-POLICY.md:237-239`) lists no repository-specific
  footgun yet; nothing to carry over. No lint cap exists.

## Verified against the codebase

Re-read on `main` at `62fc0e5`.

- `src/advisor/evals/run.py:14` — `import hashlib`.
- `src/advisor/evals/run.py:24-25` — imports `SYSTEM_PROMPT_PATH` from
  `advisor.agent` and `DEFAULT_CATALOGUE_PATH` from `advisor.catalogue`.
- `src/advisor/evals/run.py:39` — `DEFAULT_CASES = Path("evals") / "cases.jsonl"` (relative to the cwd).
- `src/advisor/evals/run.py:211` — `catalogue = load_catalogue()` (default path; no option).
- `src/advisor/evals/run.py:216-217` — `raw = args.cases.read_bytes()`; `parse_cases(raw.decode("utf-8"), catalogue)`.
- `src/advisor/evals/run.py:307-314` — the report dict:
  `"cases_sha256": hashlib.sha256(raw).hexdigest()` (:310), the comment
  "Bytes, so a whitespace-only edit changes it (§13 B6)" (:311-312),
  `"catalogue_sha256": hashlib.sha256(DEFAULT_CATALOGUE_PATH.read_bytes())…` (:313),
  `"prompt_sha256": hashlib.sha256(SYSTEM_PROMPT_PATH.read_bytes())…` (:314).
- `src/advisor/agent.py:32` — `SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"`.
- `src/advisor/catalogue.py:25` — `DEFAULT_CATALOGUE_PATH = Path(__file__).parent / "data" / "catalogue.json"`.
- `src/advisor/evals/judging.py:150-153` — `_prompt_hash` hashes
  `jg.build_prompt(...).encode()`: text, so already line-ending free
  (reference only; out of scope).
- `src/advisor/evals/baseline.py:1` — docstring "… (§17). Pure."; it imports
  no I/O and is not in `CORE_CODE`.
- `src/advisor/evals/baseline.py:14-25` — `EVAL_PATHS`; `run.py`,
  `baseline.py`, `analysis.py` and `evals/baseline.json` are not in it.
- `src/advisor/evals/baseline.py:27-28` — `HASH_FIELDS = ("cases_sha256", "prompt_sha256", "catalogue_sha256")`, `SOURCE_FIELDS = ("provider", "model", *HASH_FIELDS)`.
- `src/advisor/evals/baseline.py:45-53` — `baseline_from` copies each
  `SOURCE_FIELDS` value that is a string, plus `source` and `cases`.
- `src/advisor/evals/baseline.py:82-108` — `compare`; :92-96 warn
  `f"{key} differs: baseline {a or '(none)'}, report {b or '(none)'}"` for
  every differing `SOURCE_FIELDS` key.
- `src/advisor/evals/baseline.py:111-126` — `format_comparison`, warnings as `warning: …` lines.
- `src/advisor/evals/analysis.py:42-49` — imports from `advisor.evals.baseline`.
- `src/advisor/evals/analysis.py:69` — `DEFAULT_BASELINE = Path("evals") / "baseline.json"`.
- `src/advisor/evals/analysis.py:134-143` — the `baseline` (report, `--out`),
  `compare` (report, `--baseline`) and `owes-run` (`--base`) parsers.
- `src/advisor/evals/analysis.py:167-170` — `_write` writes UTF-8 with `newline="\n"`.
- `src/advisor/evals/analysis.py:335-336` — `baseline`, `compare`, `owes-run` dispatch to `_eval_run_command`.
- `src/advisor/evals/analysis.py:381-424` — `_eval_run_command`: reads the
  report with `parse_report` (exit 2 on unreadable or invalid), `baseline`
  writes `baseline_from(report, args.report.name)`, `compare` exits 0 always.
- `src/advisor/evals/report.py:19-41` — `parse_report` needs a `cases` list
  of objects with `id`, `question`, `answer`, `status`; a baseline file
  (`cases` is a dict) does not parse.
- `scripts/intent-check-lib.mjs:155-160` — `CORE_CODE` is `agent`,
  `catalogue`, `guardrails`, `models/`, `evals/(cases|score).py`; nothing
  this plan touches is core code, and the list is not changed.
- `tests/test_boundaries.py:151` — `advisor.evals.analysis` and
  `advisor.evals.run` must load no web framework and no SDK (both stay so).
- `tests/test_evals_run.py:58` — `write_cases` uses `path.write_text(...)`.
- `tests/test_evals_run.py:127-133` — asserts `cases_sha256 == hashlib.sha256(<file>.read_bytes())`.
- `tests/test_evals_run.py:375-380` — asserts `prompt_sha256` is the raw sha256 of `SYSTEM_PROMPT_PATH`.
- `tests/test_evals_run.py:705-717` — asserts `catalogue_sha256` is the raw
  sha256 of `DEFAULT_CATALOGUE_PATH` and differs from the other two.
- `tests/test_evals_baseline.py:55-66` — `rep()` builds reports with no `hash_form`.
- `tests/test_evals_baseline.py:117-130` — "warns once per differing field" (5 warnings; 1 when `catalogue_sha256` is absent).
- `tests/test_analysis_baseline_cli.py:32-49` — `baseline` writes the fields; a report without `catalogue_sha256` writes none.
- `tests/test_analysis_baseline_cli.py:61-71` — `compare` prints flips and `warning: model differs`, exits 0.
- `evals/baseline.json:2-6` — `source` `20261124T210400Z-ollama.json`,
  provider `ollama`, model `qwen3:8b`, `cases_sha256` `d5f5e275…`,
  `prompt_sha256` `c2a38987…`, `catalogue_sha256` `c2e56cb2…`; no `hash_form`.
- `evals/runs/20261124T210400Z-ollama.json` (main checkout only;
  `.gitignore:24` ignores `evals/runs/`) — the same three hashes. Checked
  here: each equals the sha256 of the CRLF form of the file at `62fc0e5`, and
  each committed blob is LF (no `\r`). The `lf` hashes are therefore the
  blobs' sha256: cases `90a614f9697db20aa9c2d1f4c4b504698fb79904ad59ada68ecc3f7fe3ab038a`,
  prompt `071fd576d51a3dcb10229b6af2fd51dd0de3eb7cc52741fb7a2ca63fe0b4a533`,
  catalogue `b3640395856eb6f8154fe086d7ac4d9232feda35f539137a377995cb6b47d857`.
- `git log` — the three files last changed at `1e4ef61` (§26), before §25's
  run, so that run saw `main`'s content.
- `git config core.autocrlf` — `true`; there is no `.gitattributes`.
- `REVIEW-POLICY.md:119-134` — the owed-path list; `:135-140` — "The content
  is read through the report's `prompt_sha256`, `cases_sha256` and
  `catalogue_sha256`, which must match the branch's files".
- `REVIEW-POLICY.md:30` — `.claude/skills/**` and this file are Reviewed tier.
- `REVIEW-POLICY.md:76-89` — live check rule 1 paths: `cli.py`, `models/`, `tracing.py`, `prompts/`, `infra/`.
- `.claude/skills/auto/SKILL.md:269-278` — step 6.3: "compare its
  `cases_sha256`, `prompt_sha256` and `catalogue_sha256` with the sha256 of
  `evals/cases.jsonl`, `src/advisor/prompts/system.md` and
  `src/advisor/data/catalogue.json` in the worktree at the reviewed commit."
- `.claude/skills/review/SKILL.md:95-100` — the same check for a reviewer
  agent: "equal the sha256 of `evals/cases.jsonl`, …".
- `README.md:188-207` — "Eval runs on every change…": the three commands and what `compare` warns about.
- `README.md:232-235` and `:355-357` — reports record `prompt_sha256` and `catalogue_sha256`.
- `CLAUDE.md:35` — the `owes-run|baseline|compare` command line; `:206-208` — "Eval runs on changes" architecture note.
- `docs/decisions/0003-catalogue-changes.md:16` — "A report's
  `catalogue_sha256` (bytes of the catalogue file) says which catalogue it saw".

## Design decisions (within the intent's assumptions)

- **The helper** is `content_sha256(data: bytes) -> str` in
  `src/advisor/evals/baseline.py` (already pure, already owns
  `HASH_FIELDS`): `hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()`,
  plus `HASH_FORM = "lf"`. No new module, so `CORE_CODE` and
  `tests/test_boundaries.py` need no change.
- **Which files** are hashed is wired once, in `run.py`:
  `content_hashes(cases: bytes) -> dict[str, str]` returns the three fields
  from the given case bytes, `DEFAULT_CATALOGUE_PATH` and
  `SYSTEM_PROMPT_PATH` (module globals, read at call time). The report and
  the `hashes` command both call it.
- **The form marker.** A new report carries `"hash_form": "lf"` next to the
  hashes. A report or baseline without it is the raw-byte form (before §29).
  `baseline_from` copies it when present. It is not a `SOURCE_FIELDS` entry,
  so it never yields a warning of its own.
- **`compare`**: provider and model warn as today. For each hash field that
  differs: same form on both sides → today's text
  (`cases_sha256 differs: baseline …, report …`); different forms → the same
  text followed by `; hashed differently (baseline: raw bytes, before §29;
  report: lf), so this does not show whether the content changed`. Equal
  hashes never warn.
- **The content check is a command**:
  `uv run advisor-analysis hashes [<report-or-baseline>] [--cases <path>]`,
  run in the worktree at the reviewed commit. Without a file it prints the
  three `lf` hashes. With one (any JSON object carrying the hash fields, so
  `evals/baseline.json` works too) it prints one line per field,
  `<field> matches` / `<field> differs: recorded …, files …` /
  `<field> not recorded`, and exits 0 when all three match, 1 otherwise, 2
  for an unreadable or invalid file. A file without `hash_form` is checked
  against the raw bytes, and the output says "(raw bytes: recorded before §29)".
- **The baseline rewrite** is `advisor-analysis baseline <report> --rehash`:
  for a raw-form report only, each recorded hash must equal the sha256 of
  the file on disk as-is, in LF form or in CRLF form; then the baseline is
  written with the `lf` hashes and `hash_form`. Otherwise it exits 2 naming
  the field ("the report was not made on these files") and writes nothing.
  On an `lf` report `--rehash` exits 2 ("already line-ending free").
- **Skill and policy text** (this makes the tier Reviewed; see "Tier"):
  `/auto` step 6.3 and the review skill's eval-run paragraph replace "compare
  … with the sha256 of `<files>`" by "run `uv run advisor-analysis hashes
  <report>` in the worktree at the reviewed commit; it hashes the three files
  as the run does and exits 1 naming a field that differs". `REVIEW-POLICY.md:138-140`
  gains only a parenthesis "(`advisor-analysis hashes <report>` checks
  them)". The meaning of the check does not change (the report must be a run
  of the reviewed content); only how its hashes are computed is named.
- **No `.gitattributes`**: with the hash folding `\r\n`, the checkout's form
  no longer matters, and the intent puts renormalisation out of scope.

## Subtasks

Each ends with `npm run verify` green and a commit.

1. **The helper and the run (the fix).** Add `content_sha256` and
   `HASH_FORM` to `baseline.py`; add `content_hashes` to `run.py` and build
   the report's three hashes and `"hash_form": "lf"` from it; drop the
   now-unused `hashlib` import if nothing else uses it; rewrite the
   `:311-312` comment ("CRLF read as LF, so a checkout's line endings don't
   change it; any other whitespace edit still does (§13 B6, §29)"). Tests
   first: the helper tests (they fail: no `content_sha256`), the run test on
   LF and CRLF inputs, and the three existing raw-byte assertions
   (`test_evals_run.py:132`, `:378-379`, `:712-713`) moved to
   `content_sha256`.
2. **`baseline_from` and `compare` know the form.** Copy `hash_form` in
   `baseline_from`; the form-aware hash warnings in `compare`. Tests in
   `tests/test_evals_baseline.py` and `tests/test_analysis_baseline_cli.py`.
3. **`hashes` and `baseline --rehash`.** The pure parts in `baseline.py`
   (`content_check(recorded, lf, raw) -> (lines, ok)` and
   `rehash(report, files: Mapping[str, bytes]) -> dict` raising
   `BaselineError`), the I/O in `analysis.py` (parser, dispatch through
   `_eval_run_command`, files read via `run.content_hashes` and the same two
   path globals). CLI tests in `tests/test_analysis_baseline_cli.py`.
4. **Rewrite `evals/baseline.json`.** In the worktree, with the branch's
   three files equal to `main`'s:
   `uv run advisor-analysis baseline C:/Users/eric/src/product-advice-agent/evals/runs/20261124T210400Z-ollama.json --rehash`.
   Then `uv run advisor-analysis hashes evals/baseline.json` must exit 0.
   `git diff main -- evals/baseline.json` must show only the three hash
   values (now the blob hashes listed above) and the added `hash_form`;
   `source`, provider, model and every case status unchanged. Commit the file
   alone ("§29: evals/baseline.json rehashed from 20261124T210400Z-ollama.json").
5. **Docs, skills and policy (Reviewed).** `README.md` "Eval runs…" (the
   `hashes` command, `--rehash`, the form warning, `hash_form`) and the report
   description at `:232-235`/`:355-357`; `CLAUDE.md:35` and `:206-208`;
   `docs/decisions/0003-catalogue-changes.md:16` (append: since §29 the hash
   folds CRLF to LF, `hash_form: "lf"`; older reports hashed raw bytes);
   `.claude/skills/auto/SKILL.md:273-276`; `.claude/skills/review/SKILL.md:96-98`;
   `REVIEW-POLICY.md:138-140` (the parenthesis only). No other skill, agent
   or policy line changes, and no skill version bump (none of the earlier
   edits to these skills bumped one).

## Tests

Failing first (subtask 1, `tests/test_evals_baseline.py`):
`test_content_sha256_is_the_same_for_lf_crlf_and_mixed` — one content as
`b"a\nb\nc\n"`, `b"a\r\nb\r\nc\r\n"` and `b"a\r\nb\nc\r\n"` gives one value,
equal to `hashlib.sha256(b"a\nb\nc\n")`. It fails today (no helper; and
`run.py`'s raw hashing gives three values).

Behavioural lines and the test that fails if each is mutated:

| Line | Mutation | Test that fails |
| --- | --- | --- |
| `content_sha256` folds `\r\n` | removed (raw bytes) | `test_content_sha256_is_the_same_for_lf_crlf_and_mixed` |
| folds only `\r\n` | `.strip()`, `splitlines()`, lone `\r` folded, final newline dropped | `test_content_sha256_still_sees_other_whitespace` (trailing space, extra blank line, missing final newline, lone `\r` each change the hash) |
| `run.py` cases hash uses the helper | back to `hashlib.sha256(raw)` | `test_report_hashes_ignore_line_endings` (`test_evals_run.py`: two runs, case file written with `write_bytes` as LF then CRLF, `run.SYSTEM_PROMPT_PATH` and `run.DEFAULT_CATALOGUE_PATH` monkeypatched to LF then CRLF copies in `tmp_path`; all three fields equal across the runs and equal the sha256 of the LF bytes) |
| catalogue hash uses the helper | raw | same test |
| prompt hash uses the helper | raw | same test |
| `"hash_form": "lf"` in the report | removed | same test asserts `report["hash_form"] == "lf"` |
| `baseline_from` copies `hash_form` | removed | `test_baseline_copies_hash_form` (and a raw report gives none) |
| same-form differing hash warns plainly | no warning / form note added | `test_compare_same_form_still_warns_when_content_changed` (both `lf`, `cases_sha256` differs → exactly one warning, `cases_sha256 differs`, no "hashed differently") |
| equal hashes never warn | warns | `test_identical_run_has_no_flips` (existing) plus the same with `hash_form` on both |
| mixed forms say so | plain text | `test_compare_names_mixed_hash_forms` (raw baseline, `lf` report, all three differ → three warnings, each with "hashed differently" and "before §29") |
| `hash_form` is not a warning field of its own | added to `SOURCE_FIELDS` | `test_compare_warns_once_per_differing_field` (existing, count 5) plus `test_compare_names_mixed_hash_forms` (count 3, not 4) |
| `hashes` exit 0 on match | exit 1 | `test_hashes_matches_a_report_made_on_lf_files_from_crlf_files` (report hashes from LF bytes, working files CRLF) |
| `hashes` exit 1 naming the field | exit 0, or wrong field | `test_hashes_names_the_field_that_differs` (catalogue copy edited) |
| `hashes` on a raw-form file checks raw bytes | `lf` used | `test_hashes_checks_an_old_report_against_raw_bytes` (says "before §29"; match on the raw bytes, differ on another form) |
| `hashes` reads a baseline file | `parse_report` used | `test_hashes_accepts_a_baseline_file` |
| missing field | counted as match | `test_hashes_reports_a_field_not_recorded` (exit 1) |
| unreadable file | traceback | `test_hashes_unreadable_or_invalid_file_exits_2` |
| `--rehash` accepts raw/LF/CRLF forms of the files | refuses one form | `test_rehash_writes_lf_hashes_when_the_report_saw_these_files` (parametrised over the three forms; written file has the blob-form hashes and `hash_form`) |
| `--rehash` refuses other content | writes anyway | `test_rehash_refuses_a_report_of_other_content` (mixed-ending bytes like §26's → exit 2 naming `cases_sha256`, no file written) |
| `--rehash` on an `lf` report | rewrites | `test_rehash_refuses_an_lf_report` |

All tests use `tmp_path` files and monkeypatched path globals; none reads the
committed files' bytes as the expectation, and none calls a model or the
network (`tests/conftest.py` already fails any socket connect). The existing
`test_evals_run.py` assertions at `:132`, `:378-379`, `:712-713` become
`content_sha256(...)` comparisons.

## Validation

- `npm run verify` green after every subtask.
- `npm run check:intent` PASS.
- `uv run advisor-analysis hashes evals/baseline.json` in the worktree exits
  0 with three "matches" lines (outcome 2 without a model: the committed
  baseline equals the files as the run now hashes them). The same command on
  an LF checkout gives the same result (the reviewer may confirm with
  `git show HEAD:<file> | sha256sum`, which equals the `lf` hash for LF blobs).
- `uv run advisor-analysis compare C:/Users/eric/src/product-advice-agent/evals/runs/20261124T210400Z-ollama.json`
  in the worktree prints three "hashed differently … before §29" warnings
  (old report against the new baseline), which shows the mixed-form text on
  real data.
- `uv run advisor-analysis owes-run --base main` prints "not owed".
- Live check: none owed. No rule-1 path (`cli.py`, `models/`, `tracing.py`,
  `prompts/`, `infra/`) and not `.claude/settings.json`; the change is file
  hashing and comparison, fully driven by the tests above, so no Not-checked
  item needs a live run. The first real `advisor-eval` after the merge will
  carry `hash_form: "lf"`; the coordinator can see it then, but it is not a
  gate.
- Eval run: not owed. The diff touches `src/advisor/evals/run.py`,
  `baseline.py`, `analysis.py`, tests, docs, two skills, `REVIEW-POLICY.md`
  and `evals/baseline.json`; none is in `EVAL_PATHS`
  (`baseline.py:14-25`).

## Tier

**Reviewed.** Subtask 5 edits `.claude/skills/auto/SKILL.md`,
`.claude/skills/review/SKILL.md` and `REVIEW-POLICY.md` (all Reviewed by
path, `REVIEW-POLICY.md:30`). The skill edits are needed: both say "the
sha256 of" the files, which after this change no longer equals a CRLF
checkout's report hash, so the content check could not be stated without
changing their text. The `REVIEW-POLICY.md` edit adds the command name only;
its rule ("must match the branch's files") is unchanged. The code alone
(`run.py`, `baseline.py`, `analysis.py`) would be Attested.

## Assumptions I made

- **Only `\r\n` is folded**, not a lone `\r` (the intent: "`\r\n` read as
  `\n`"). Text mode would also fold a lone `\r`; git's autocrlf never
  produces one, and keeping it visible is closer to §13 B6.
- **The helper lives in `baseline.py`**, not a new module: it is pure, holds
  `HASH_FIELDS`, and is what `compare` and the check already import.
- **A marker field (`hash_form`)** is how `compare` tells old from new
  hashes; the intent requires the distinction but not the mechanism.
- **`--rehash` is a permanent option**, not a one-off script, so the
  baseline is written by a command that proves content equality (the
  intent's "not hand-edited"), and so a baseline written later from a
  pre-§29 report of another intent can be brought to the `lf` form the same
  way.
- **`hashes` accepts a baseline file** as well as a report, so outcome 2 can
  be checked without a model run.
- **No change to `/deliver`'s skill**: a baseline written from a pre-§29
  report stays raw-form and `compare` then says "hashed differently"; that is
  the warning the intent allows.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
