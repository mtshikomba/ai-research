# task-002: clean up legacy project files

## User Story

As a repository maintainer, I want obsolete generated artifacts, example-project
fixtures, and superseded planning documents removed so that the CrewAI project
contains only current source, configuration, and documentation.

## Scope

- Retain the concise `.github/copilot-instructions.md` pointer to the canonical
  `AGENTS.md` policy.
- Remove legacy generated run artifacts under `artifacts/` and
  `example_target_project/artifacts/`.
- Remove the obsolete `example_target_project` fixture and legacy planning,
  backlog, roadmap, and MVP documents currently deleted in the working tree.

## Acceptance Criteria

- [x] The PR contains only the existing cleanup deletions and the canonical
  Copilot-instructions pointer change, plus this task record.
- [x] No files under `src/`, `tests/`, `pyproject.toml`, or active CrewAI
  configuration are removed or modified.
- [x] Generated artifact directories and the obsolete example-project fixture
  are absent after the change.
- [x] Removed planning and MVP documents have no remaining in-repository
  references that would produce broken documentation links.
- [x] `.github/copilot-instructions.md` remains a minimal pointer to
  `AGENTS.md` and does not duplicate repository policy.
- [x] A repository status and diff check confirm the PR file set matches this
  scope and contains no whitespace errors.

## Out of Scope

- Changing CrewAI application behavior, dependencies, or configuration.
- Updating the current README unless a broken link requires it.
- Deleting files not already represented by the current working-tree changes.

## Validation

- Inspect the staged diff and changed-file list.
- Search tracked documentation for references to removed documents and fixture
  paths.
- Run `git diff --check`.