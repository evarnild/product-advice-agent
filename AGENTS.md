# Codex Instructions

This repository has existing Claude Code guidance. Use it as shared project
context, but keep Claude-specific and Codex-specific files separate.

## Shared Project Context

- Read `CLAUDE.md` for the project overview, commands, and how work flows.
- Treat `npm run queue` as the queue and status overview. It is generated
  from each intent's `metadata.yml`, and nobody edits it. Each item's detail
  lives in `intents/<id>-<slug>/` (see `intents/README.md`).
- Apply `REVIEW-POLICY.md` when reviewing. The procedures in
  `.claude/skills/*/SKILL.md` (`intent`, `spec`, `build-plan`, `review`,
  `grid`, `ship`) are plain markdown and apply to Codex sessions too.
- Do not edit `OVERVIEW.md` unless the user explicitly asks for an overview
  update.

## Ownership Boundaries

- Do not modify `.claude/`; it is owned by Claude Code.
- Do not assume Claude's local worktrees or unpushed branches are visible
  from this checkout.
- Before starting implementation work, check `git status`, `git branch` and
  `git worktree list`. Never `git checkout` a branch in the main checkout.
- Use a Codex-created branch or worktree for Codex work when it may overlap
  with Claude Code.
- Merge into `main`, push, delete a branch or remove a worktree only when the
  owner explicitly asks for that action in the current conversation, and
  only after the preconditions in `REVIEW-POLICY.md` → "Merging".
- Record a gate in `metadata.yml` only as `intents/README.md` → "Recording a
  gate" allows. Never record `live_checked:`; that gate is the owner's.

## Verification

- Use `npm run verify` and `npm run check:intent` for final verification. Do
  not raise any lint warning cap.
