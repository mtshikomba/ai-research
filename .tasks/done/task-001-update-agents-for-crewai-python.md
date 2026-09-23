# task-001: update agents for CrewAI Python

## User Story

As a scrum-team workspace user, I want the repository agent instructions to
describe CrewAI and Python engineering practices so that generated work follows
the project's actual framework, tooling, and validation workflow.

## Scope

- Replace Django-specific architecture, database, view/API, security, testing,
  migration, and review guidance in `AGENTS.md`.
- Preserve the existing team personas, ticket lifecycle, branch naming, and
  pull-request naming conventions unless a CrewAI-specific adjustment is needed.
- Align validation guidance with the project's declared Python and CrewAI
  tooling.

## Acceptance Criteria

- [x] `AGENTS.md` identifies the workspace as a CrewAI and Python engineering
  suite rather than a Django engineering suite.
- [x] Architecture guidance covers typed Python, CrewAI crew/agent/task
  configuration, separation of orchestration from adapters and tools, and
  environment-based secret handling.
- [x] Django ORM, CBV/DRF, serializer, migration, CSRF, XSS, database-index,
  and query-optimization requirements are removed or replaced with applicable
  CrewAI and Python guidance.
- [x] The Definition of Done requires focused automated tests and applicable
  formatting/lint/type validation, without requiring Django migrations.
- [x] The code-review workflow checks CrewAI configuration, tool input/output
  validation, secret exposure, error handling, and dependency risks.
- [x] Team personas and ticket/branch/PR conventions remain internally
  consistent after the update.
- [x] The revised Markdown passes a lightweight structural review for stale
  Django references and contradictory requirements.

## Out of Scope

- Changing application source code, dependencies, or CI configuration.
- Introducing a new task runner, linter, or test framework.
- Modifying existing CrewAI agents or task definitions.

## Validation

- Search `AGENTS.md` for stale Django-specific terms.
- Verify the new guidance is consistent with `pyproject.toml` and existing
  project structure.