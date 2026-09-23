# task-005: select Ollama model in dashboard

## User Story

As a research-crew user, I want to choose an available Ollama model in the
Streamlit dashboard so that I can run each research request with the model best
suited to the task.

## Scope

- Use `gpt-oss:120b-cloud` as the default dashboard model.
- Query the configured Ollama server's `/api/tags` endpoint to populate a
  dashboard model selector from the models currently available to that server.
- Pass the selected model through the existing dashboard service into the CrewAI
  agents for that individual run, without mutating the user's `.env` file.
- Preserve the `MODEL` environment variable as a configurable fallback when the
  requested default is unavailable.
- Provide safe, actionable loading and error states when the Ollama server is
  unreachable or returns no selectable models.

## Acceptance Criteria

- [x] The dashboard provides an accessible, labeled model selector populated
  from the configured Ollama server's current model inventory.
- [x] `gpt-oss:120b-cloud` is selected by default whenever it is available.
- [x] The selected model is used by every CrewAI agent in that dashboard run and
  is shown with the completed result and saved report location.
- [x] The model choice is scoped to the run and does not write or alter `.env`.
- [x] If the configured default is unavailable, the dashboard selects the
  environment-configured model when present, otherwise the first available
  model, and explains the fallback without exposing sensitive provider output.
- [x] If Ollama is unavailable or provides no models, the dashboard shows a
  safe, actionable state and prevents a run from starting.
- [x] Focused tests cover model-inventory parsing, default and fallback
  selection, selected-model propagation, and safe unavailable-server states
  without a live Ollama server.
- [x] Streamlit AppTest and desktop/mobile browser validation cover model
  selection, loading, empty, error, running, and completed-result states.
- [x] Applicable formatting, linting, type checks, and a real Ollama smoke test
  pass using `gpt-oss:120b-cloud`.

## UX Specification

### Primary Flow

1. On load, the dashboard shows a labeled `Model` selector above the research
   topic input and loads models from the configured Ollama server.
2. When available, `gpt-oss:120b-cloud` is preselected; the active model and
   server endpoint remain visible in the sidebar.
3. The user chooses a model, enters a topic, and selects `Run crew`.
4. During execution, the selector, topic input, and run action are disabled and
   the running state identifies the selected model.
5. On completion, the result view displays the selected model and saved report
   path alongside the report content.

### Required States

- **Loading:** Show a compact loading indicator while model inventory is being
  retrieved; do not show an empty selector as though no models exist.
- **Default unavailable:** Select the environment model when available, then the
  first available model; state that a fallback is active without exposing raw
  provider responses.
- **No models:** Show an actionable empty state and disable `Run crew`.
- **Server unavailable:** Show an actionable safe error and disable model
  selection and `Run crew`; retain the entered topic for retry after rerun.
- **Keyboard:** The selector has a visible label and can be reached before the
  topic field; form submission remains available through the button and Enter.
- **Responsive:** Keep the form controls vertically stacked at mobile widths;
  sidebar model details must not cause horizontal scrolling.

### UX Acceptance Criteria

- [x] The `Model` selector appears before the topic input, has a visible label,
  and communicates the selected model in the run result.
- [x] Loading, fallback, unavailable-server, no-model, empty-topic, running,
  success, and safe failure states are distinct and actionable.
- [x] All inputs and the submit action are disabled while a run is in progress.
- [x] Desktop and 390 px mobile views have no horizontal overflow or obscured
  model, topic, submit, result, or saved-report content.

## Out of Scope

- Downloading, deleting, or managing Ollama models from the dashboard.
- Adding cloud-provider model selection or storing per-user model preferences.
- Changing the configured Ollama server endpoint or report storage behavior.

## Validation

- Mock `/api/tags` responses in focused service and Streamlit tests.
- Verify a real dashboard run uses `gpt-oss:120b-cloud` and displays the
  selected model with the saved report path.
- Test unavailable-server and empty-model-inventory states without exposing raw
  server response details.