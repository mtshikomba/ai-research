# task-008: remove mvp agents and config

## User Story

As a repository maintainer, I want the legacy MVP agents, tasks, and supporting code paths removed so that the project contains only the current research-crew configuration and no superseded MVP scaffolding.

## Scope

- Remove the legacy MVP configuration files under `src/my_research_crew/config/`:
  - `mvp_agents.yaml`
  - `mvp_tasks.yaml`
- Remove or clean up all code and references that specifically prefer, load, or document the MVP config set instead of the current default crew configuration.
- Remove any legacy MVP-specific wiring in project entry points, orchestration logic, validation helpers, docs, or task descriptions that are no longer part of the active design.
- Clean up related files that were introduced solely for the MVP path, including any package/dependency files or references that exist only to support that workflow.
- Preserve the non-MVP research crew behavior and current project configuration as the canonical path.

## Acceptance Criteria

- [ ] The repository no longer contains the `mvp_agents.yaml` and `mvp_tasks.yaml` files.
- [ ] No code path in the active crew orchestration prefers the MVP config files over the current default files.
- [ ] The default project workflow still loads and executes the active research crew configuration successfully.
- [ ] Any MVP-specific comments, docstrings, CLI descriptions, or validation text are removed or updated to reflect the current non-MVP implementation.
- [ ] Legacy MVP references and related work are absent from source, docs, and configuration files.
- [ ] The package still installs and runs without the removed MVP artifacts or code paths.
- [ ] Focused tests or validation commands confirm the non-MVP flow continues to work after cleanup.

## Out of Scope

- Reworking the current research crew architecture or changing non-MVP product behavior.
- Removing unrelated project features that are not part of the MVP legacy path.
- Introducing a compatibility shim for the old MVP configuration.

## Validation

- Search the repository for `mvp_agents`, `mvp_tasks`, `MVP`, and related legacy identifiers.
- Verify the active config is loaded from the canonical non-MVP files only.
- Run the targeted test suite and any relevant smoke checks for the current crew flow.
- Confirm the repo contains no stale references to the removed MVP work.
