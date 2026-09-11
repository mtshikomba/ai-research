# task-003: add streamlit dashboard

## User Story

As a CrewAI project user, I want a Streamlit dashboard that runs the existing
crew with Ollama models hosted on my local server and presents its result so that
I can use the project without invoking the command line directly.

## Scope

- Add Streamlit as a declared project dependency compatible with the supported
  Python versions.
- Add a dedicated dashboard module and documented launch command.
- Provide a dashboard form for the existing crew inputs and a clear command to
  start a run.
- Reuse the existing CrewAI assembly and orchestration rather than duplicating
  agents, tasks, or provider setup in the UI.
- Support a locally hosted Ollama model using environment-based configuration
  for the model identifier and server endpoint, with documented defaults that
  match the local-network Ollama service.
- Present running, success, and failure states, including actionable error
  messages that do not disclose secrets.

## Acceptance Criteria

- [x] The project declares Streamlit as an application dependency and the
  dashboard starts with a documented `streamlit run` command.
- [x] The first dashboard view identifies the CrewAI project and exposes the
  inputs required for an existing crew run.
- [x] A user can start a crew run from the dashboard; the UI uses the existing
  crew configuration and orchestration path.
- [x] The dashboard reads the Ollama model and endpoint from environment-based
  configuration, supports the installed `ollama/llama3.1:latest` and
  `http://192.168.1.153:11434` defaults, and does not require an OpenAI API key.
- [x] Documentation explains how to start Ollama locally, make the selected
  model available, configure the endpoint and model, and launch the dashboard.
- [x] The dashboard disables duplicate submissions while a run is in progress
  and shows a visible running state.
- [x] On success, the dashboard displays the returned crew output in a readable
  result area.
- [x] On failure, the dashboard shows an actionable, user-safe error state and
  identifies unavailable Ollama servers or models without rendering credentials,
  private prompts, or raw sensitive provider output.
- [x] The dashboard is usable at desktop and mobile widths, with keyboard-focus
  and empty-input states reviewed.
- [x] Focused tests cover the dashboard's Ollama configuration and run boundary
  without requiring a live local server; applicable formatting, linting, and
  type checks pass.

## Out of Scope

- Changing agent roles or task definitions.
- Adding authentication, persistent run history, multi-user state, or a new API
  service.
- Supporting cloud LLM providers in the dashboard.
- Replacing existing CLI entrypoints.

## Validation

- Run the focused dashboard tests with mocked crew execution and Ollama
  configuration.
- Start the Streamlit app and verify loading, empty, running, success, and error
  states at desktop and mobile widths.
- Confirm unavailable local-server and missing-model errors are actionable, and
  credentials and private prompts are not rendered in the UI or logs.