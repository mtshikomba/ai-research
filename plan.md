Plan and recent changes (updated 2026-08-24T04:09:45+02:00)

Summary
-------
This update implements two requested items for the MVP:

A) Store provenance artifacts inside the target repository under artifacts/ (recommended for provenance).
B) Harden the non-invasive flow with explicit dry-run, safe-mode, and interactive confirmation options.

What was changed
----------------
- Added ArtifactStore (src/my_1st_crew/artifacts.py) which writes artifacts into <project_root>/artifacts/<iso-ts>-<task>/.
  Each artifact folder includes metadata.json, prompt.txt, output.json (or output.txt), validation.json and git.json when available.

- Added CLI flags to control safe/dry-run behavior:
  - --dry-run        : simulate actions; no commits, pushes, or PRs are performed
  - --safe-mode      : allow local commits but never push or open PRs automatically
  - --confirm-push   : require interactive confirmation before commit/push/PR (requires a TTY)
  These flags are passed through the CLI and into the Crew orchestrator.

- Hardened Crew/kickoff behavior (src/my_1st_crew/team.py):
  - The Crew constructor now accepts dry_run, safe_mode, and confirm_push and passes them to GitWorkflow.
  - For engineer tasks:
    - If --dry-run is enabled, commits and PRs are skipped (status recorded as dry_run).
    - If --safe-mode is enabled, commits may still be performed but PR creation is skipped.
    - If --confirm-push is enabled, the CLI will require an interactive confirmation before performing commit/push/PR.
  - Every task run saves provenance via ArtifactStore into the target repo's artifacts/ folder.

- GitWorkflow constructor updated to accept dry_run, safe_mode and confirm_push flags for future behavior alignment (methods are still defensive).

How to use
----------
Run the agent against a target repo (example_target_project included):

  PYTHONPATH=src python -m my_1st_crew.cli --repo-root example_target_project

Run in dry-run (no commits/pushes):

  PYTHONPATH=src python -m my_1st_crew.cli --repo-root example_target_project --dry-run

Run with safe mode (no automatic pushes/PRs):

  PYTHONPATH=src python -m my_1st_crew.cli --repo-root example_target_project --safe-mode

Run with interactive confirmations (requires TTY):

  PYTHONPATH=src python -m my_1st_crew.cli --repo-root example_target_project --confirm-push

Notes / Caveats
---------------
- ArtifactStore is best-effort and will not cause the run to fail if writing artifacts fails.
- confirm-push requires an interactive terminal; in non-interactive environments it will skip commit/push/PR with a helpful status.
- The agent still uses a conservative validation command for commits (compileall) — consider wiring ProjectContext-detected validation to git_workflow in a follow-up.

Next steps
----------
1. Optionally wire ProjectContext's discovered validation commands into the commit gating path so the correct test/lint/build commands are run per-project.
2. Add an artifacts index (artifacts/index.json) for easier querying and auditing across runs.
3. Add a small integration test to exercise dry-run/safe-mode/confirm flows in a temporary repo.

If you want, the next immediate task can be:
- (A) Add artifacts/index.json and a CLI helper to list artifacts (recommended), or
- (B) Wire ProjectContext to choose validation_command for commits, or
- (C) Add an installer/bootstrapping script to embed the agent into a target repo.
