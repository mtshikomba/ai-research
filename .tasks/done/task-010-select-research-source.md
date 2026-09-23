# task-010: select research source

## User Story

As a research dashboard user, I want to select either internet research or the local knowledge directory before starting a run so that I control which evidence source the research crew uses.

## Scope

- Add a required `st.segmented_control` labeled `Research source` to the Research workspace with two mutually exclusive modes:
  - Internet
  - Local knowledge
- Default new sessions to Internet so existing research behavior remains predictable; retain the user's selection across normal Streamlit reruns within the session.
- Pass the selected source through the dashboard service into the research crew as an explicit, validated input.
- In Internet mode, configure the researcher to use approved internet research tools and not silently incorporate local knowledge files.
- In Local knowledge mode, configure the researcher to use files under the repository's ignored `knowledge/` directory and prevent internet fallback or external lookup.
- Support the local document formats already accepted by the project's knowledge tooling and handle local ZIP archives through a safe extraction path when applicable.
- Keep all local knowledge data ignored by Git and prevent file contents, private prompts, or credentials from appearing in logs or errors.
- Include the selected source in the completed-run summary and saved report metadata or report content.
- Update project documentation with the source-selection behavior and local data placement guidance.

## UX Acceptance Criteria

- [x] The Research setup form presents a required `st.segmented_control` labeled `Research source`, with Internet and Local knowledge visible together before the model and topic inputs.
- [x] Exactly one source is selected for every run; Internet is the documented default for a new session, and the selection persists across normal reruns.
- [x] Internet mode displays concise supporting copy that the run uses external web sources and does not read local knowledge files.
- [x] Local knowledge mode displays concise supporting copy that the run reads only from the ignored `knowledge/` directory, safely prepares supported ZIP archives, and does not access the internet.
- [x] Local knowledge readiness is shown before submission without displaying sensitive filenames or document contents; the state distinguishes ready, empty/missing, and unusable local data.
- [x] The current source remains visible while the run is in progress and in the completed report summary.
- [x] Local knowledge mode explains that files are read from `knowledge/` and remain local-only.
- [x] When Local knowledge is selected but no usable local files exist, the submit action is disabled and an actionable message identifies the expected directory without falling back to the internet.
- [x] Source controls, model selection, topic input, and submit action are disabled consistently while a run is active, without losing the visible selected source.
- [x] The control has an accessible visible label, supports keyboard selection, has no color-only meaning, and keeps both option labels readable without horizontal clipping at mobile widths.
- [x] Loading, empty, validation-error, archive-error, provider-error, success, disabled, keyboard-focus, and overflow states work at desktop and mobile widths.

## Technical Acceptance Criteria

- [x] `run_crew` accepts and validates a typed or enumerated research-source value rather than relying on display text or an implicit global setting.
- [x] The selected source is passed through the dashboard, service, CrewAI assembly, and task inputs without mutating environment configuration.
- [x] Internet mode enables only the approved internet-research path and does not read from `knowledge/`.
- [x] Local knowledge mode reads only from the repository's `knowledge/` directory and does not invoke internet research or silently fall back to it.
- [x] Local paths and extracted ZIP entries are validated to prevent traversal outside `knowledge/`; unsupported, corrupt, or encrypted archives produce safe actionable errors.
- [x] Empty, missing, unreadable, and unsupported local knowledge inputs are handled before crew kickoff.
- [x] Generated reports identify whether Internet or Local knowledge was selected without exposing sensitive local file contents in UI metadata or logs.
- [x] Existing executive Peshiko behavior remains unchanged.
- [x] Focused automated tests cover source validation, the Internet default, selection persistence, both execution paths, no-cross-source behavior, empty local knowledge, archive safety, disabled controls, dashboard state, and report source labeling.
- [x] Black formatting and flake8 linting pass for all changed Python files.

## Out of Scope

- Combining internet and local knowledge in one research run.
- Automatically falling back from Local knowledge to Internet.
- Uploading local documents through the dashboard.
- Committing files from `knowledge/` or generated reports.
- Changing the Peshiko executive crew's existing local-first policy.

## Validation

- Run focused service and crew tests proving each source selects only its permitted tools and data path.
- Run Streamlit AppTest coverage for the segmented-control default and label, both modes, selection persistence, source-specific helper copy, missing local data, disabled state, and successful report source labeling.
- Verify ZIP extraction rejects absolute paths, parent traversal, links, corrupt archives, and encrypted archives.
- Verify `git check-ignore knowledge/` and confirm local data is absent from the tracked change set.
- Run Black and flake8 checks for changed Python files.
- Review the Research workspace in a browser at desktop and mobile widths, including keyboard operation, visible focus, source-state copy, disabled controls, and text overflow.

## Implementation Evidence

- `uv run python -m unittest discover -s tests -q`
- `uv run black --check ...`
- `uv run flake8 ...`
- `git check-ignore -v knowledge/`
- Browser validation at desktop and 390 x 844 mobile widths, including immediate source-state updates, keyboard selection, and zero horizontal overflow.
