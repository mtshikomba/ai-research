# task-004: store reports and rename crew

## User Story

As a research-crew user, I want each research run to save its report in a
separate ignored directory and the project to be named `my_research_crew` so
that reports remain organized without entering version control and the package
has a meaningful name.

## Scope

- Replace the fixed root-level `report.md` output with a unique run directory
  under `reports/`.
- Store each generated report at
  `reports/<timestamp>-<sanitized-topic>/report.md`, where the directory name is
  filesystem-safe and collisions do not overwrite an earlier run.
- Ensure the Streamlit dashboard displays the completed result while using the
  same report-storage path as CLI/CrewAI execution.
- Add `reports/` to `.gitignore` without committing generated report content.
- Rename the Python distribution and source package from `my_1st_crew` to
  `my_research_crew`, including imports, entry points, dashboard copy,
  configuration discovery paths, tests, documentation, and CrewAI class names.

## Acceptance Criteria

- [x] Every successful research run creates one unique directory beneath
  `reports/` and writes its final report as `report.md` inside it.
- [x] Directory names contain a timestamp and a sanitized topic-derived label;
  they cannot escape `reports/` or overwrite a previous report.
- [x] The root-level `report.md` output is no longer created by the CrewAI
  reporting task.
- [x] `reports/` is ignored by Git, and no generated reports are added to the
  commit.
- [x] The Streamlit result view continues to show the completed report and can
  identify the saved report location without exposing private prompts or
  credentials.
- [x] The installed package, source directory, all internal imports, project
  scripts, and documentation use `my_research_crew`; no functional
  `my_1st_crew` references remain.
- [x] A supported Python 3.12 environment installs the renamed package and
  launches both the Streamlit dashboard and the CrewAI command entry point.
- [x] Focused tests cover report-path sanitization, uniqueness, report writing,
  and renamed imports without a live LLM; applicable formatting, linting, and
  type checks pass.
- [x] Browser validation covers a successful dashboard run's saved-report
  location plus empty, running, and error states at desktop and mobile widths.

## Out of Scope

- Migrating or retaining compatibility aliases for the `my_1st_crew` package or
  CLI command.
- Committing existing generated `report.md` or any contents of `reports/`.
- Adding report browsing, retention policies, authentication, or cloud storage.

## Validation

- Run focused report-storage and renamed-package tests with mocked CrewAI
  execution.
- Verify a real local Ollama run creates a report only beneath `reports/`.
- Verify `git status --ignored` recognizes `reports/` and leaves reports out of
  the staged change set.
- Launch Streamlit at desktop and mobile widths and verify the saved-report
  location, result, empty, running, and safe error states.