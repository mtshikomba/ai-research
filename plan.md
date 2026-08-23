Plan: restore and generalize MVP for portable team-agent

Status
- Current workspace: feature branch feature/story-1-user-can-sign-up-with-email
- A PR was opened against develop: https://github.com/mtshikomba/ai-scrum-team/pull/1

Completed (recent work)
- Restored a Markdown-backed backlog and added backlog.md as the human-editable source of truth.
- Implemented MarkdownBacklogAdapter at src/my_1st_crew/backlog_adapter.py.
- Reintroduced MVP orchestration in src/my_1st_crew/team.py to pass backlog context into agent prompts.
- Implemented story-level git workflow and commit gating at src/my_1st_crew/git_workflow.py.
- Added guarded PR creation (gh CLI or GitHub API) that targets the repository's default branch.
- Added ProjectContext in src/my_1st_crew/project_context.py to detect repo language, default branch, and validation commands so the agent can run in arbitrary repos.
- Updated README.md and .github/copilot-instructions.md with notes about the portability and the story-first workflow.

Current behavior
- Running the MVP CLI (PYTHONPATH=src python -m my_1st_crew.cli) will:
  1) Load backlog.md as the backlog
  2) Run tasks sequentially using the MockLLM adapter
  3) For engineer tasks, create a feature branch, run detected validation commands, commit when validation passes, and (optionally) open a PR into the detected default branch
- PR creation is gated behind environment/credentials and controlled by AUTO_CREATE_PR (set to "true" to enable automatic PR creation).

Next steps (recommended, prioritized)
1. Safety: Keep MockLLM as default and require an explicit opt-in to run a real LLM. Add an "adapter config" file to control this.
2. CI for agent PRs: Add a GitHub Actions workflow that runs the detected validation commands on PRs opened by the agent and fails merges until checks pass.
3. Provenance: Create an artifacts/ directory and record agent prompts, outputs, model metadata, validator results and git refs for every generated artifact.
4. Hardening: Add pre-commit hooks, secret-scanning, and optional manual approval step before pushing to remote in protected environments.
5. Discovery improvements: Expand ProjectContext to detect monorepos and prioritized scripts; expose a summary prompt at kickoff so users see detected commands and can override them.
6. Bootstrap: Add a small installer script that can drop this agent into any target repo and run an initial discovery pass.
7. Tests: Add integration tests that exercise the full flow in a temporary repo (backlog -> branch -> commit -> (mock) PR).

Notes and choices
- The repo currently uses defensive operations when git or GitHub are not available; nothing destructive is done without credentials.
- The feature-branch naming convention: feature/<story-id>-<slug>
- Validation commands are detected by ProjectContext from common manifests (pyproject.toml, package.json, go.mod, Cargo.toml, pom.xml, Makefile). These are best-effort and will be surfaced/logged at startup.

If you want, I can:
- Commit this plan into the repo (plan.md) — already done at /Users/matheus/dev/my_crew/my_1st_crew/plan.md
- Create the bootstrap installer next
- Implement CI for PR validation now

Which would you like me to do next?