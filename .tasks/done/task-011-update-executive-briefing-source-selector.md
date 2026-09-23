# task-011: update executive briefing source selector

## User Story

As a user of the executive briefing workflow, I want to change the research source between Internet and Local Knowledge so that I can choose the evidence source that best matches my briefing needs and keep the workflow aligned with the selected source.

## Scope

- Update the executive briefing UI to expose a source selector for the available research modes.
- Support switching between Internet and Local Knowledge within the briefing flow.
- Ensure the selected source is passed through to the crew execution and report generation pipeline.
- Preserve the current behavior for the active research-source model without introducing a third unsupported mode.
- Validate the UX at desktop and mobile widths for clarity, readability, and state handling.

## Acceptance Criteria

- [ ] The executive briefing form includes a source selector with exactly two options: Internet and Local Knowledge.
- [ ] The user can switch sources before starting the briefing without leaving the current workflow.
- [ ] Selecting Internet shows the correct message that the run uses public internet sources and does not read local knowledge files.
- [ ] Selecting Local Knowledge triggers a local knowledge readiness check and shows a clear warning if no usable local evidence is available.
- [ ] The selected source is passed through to the executive crew and reflected in the report output summary.
- [ ] Local Knowledge mode remains explicit and does not silently fall back to Internet without a clear workflow decision.
- [ ] The run action is disabled while a briefing is in progress and re-enabled when the run completes.
- [ ] Loading, error, and empty states for the source-selection path are clear and actionable for the user.
- [ ] The interface remains usable and readable at desktop and mobile widths.

## UX Implementation Notes

- Follow the same segmented-control pattern already used in the research workspace so the executive briefing UI feels consistent with the dashboard.
- Reuse the existing `ResearchSource` enum and readiness checks from the current source validation model rather than introducing a new source abstraction.
- For Local Knowledge, disable the submit action and show a warning when no usable files are present under the supported knowledge directory.
- For Internet, keep the source selection explicit and ensure the run does not read any local evidence files.
- Display the selected source in the result panel summary so the user can confirm the source used for the generated briefing.
- Ensure the control layout remains accessible and easy to operate on smaller mobile widths.

## Out of Scope

- Reworking the overall executive briefing architecture.
- Adding a new research source beyond the existing supported modes.
- Changing unrelated dashboard behavior outside the briefing source selection flow.

## Validation

- Check the executive briefing form and wiring for source selection.
- Verify the source choice reaches the crew execution path.
- Test the UI in desktop and mobile layouts.
- Run the relevant automated tests for source handling and report generation.
