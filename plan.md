# Plan: restore and generalize the MVP for a portable team agent

## Status
- Workspace: feature branch `#8`
- Goal: merge the safety/provenance improvements into the develop branch without losing the project-portability work.

## What this branch adds
- Artifact provenance storage under `<project_root>/artifacts/` for each task.
- Safe execution flags for the CLI: `--dry-run`, `--safe-mode`, and `--confirm-push`.
- Defensive git and GitHub behavior so the agent fails gracefully in local/non-auth environments.
- Project-aware validation and base-branch detection via `ProjectContext`.

## Recent work completed
- Restored a Markdown-backed backlog and made `backlog.md` the human-editable source of truth.
- Reintroduced MVP orchestration in `src/my_1st_crew/team.py` to pass backlog context into task prompts.
- Implemented story-level git workflow and commit gating in `src/my_1st_crew/git_workflow.py`.
- Added guarded PR creation (GitHub CLI or API) targeted at the detected default branch.
- Added `ProjectContext` to detect repo language, default branch, and validation commands for arbitrary repos.
- Added provenance artifacts via `src/my_1st_crew/artifacts.py`.
- Updated README and Copilot instructions to document portability and the story-first workflow.

## Current behavior
- Running the CLI (`PYTHONPATH=src python -m my_1st_crew.cli`) logs backlog tasks, executes them in sequence, and creates story branches when needed.
- For engineer tasks, the agent validates code, commits when possible, and optionally opens a PR.
- The flow remains conservative: destructive actions are skipped when credentials or GitHub auth are unavailable.

## Operating modes
1. `--dry-run` — validate locally, but do not commit, push, or open PRs.
2. `--safe-mode` — allow local commits, but skip automatic pushes/PRs.
3. `--confirm-push` — require an interactive approval before commit/push/PR actions.

## Recommended next steps
1. Add an artifact index (`artifacts/index.json`) for easier auditing and listing.
2. Wire the detected validation command into more of the commit and CI workflow.
3. Add integration tests that exercise the full branch -> commit -> PR path in a temporary repo.
