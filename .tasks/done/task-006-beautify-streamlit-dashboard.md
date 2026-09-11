# task-006: beautify Streamlit dashboard

## User Story

As a research-crew user, I want the Streamlit dashboard to feel polished,
focused, and easy to scan so that configuring a local Ollama research run and
reviewing its report feels like a purposeful workspace rather than a raw form.

## Scope

- Add a project-level Streamlit theme with a distinctive, accessible research
  workspace visual direction.
- Recompose the existing dashboard with native Streamlit layout primitives,
  clear hierarchy, and responsive containers.
- Make Ollama connection details, selected model, research prompt, run state,
  result, and saved-report location visually scannable.
- Use Material Symbols for supporting status and action affordances where
  available; preserve visible labels for all controls.
- Preserve existing model inventory, run execution, report storage, safe error,
  and no-duplicate-submission behavior.

## Acceptance Criteria

- [x] A `.streamlit/config.toml` theme provides accessible contrast, a
  deliberate typography and color system, and avoids default Streamlit visual
  styling.
- [x] The dashboard has a clear first-viewport hierarchy: product identity,
  local Ollama connection/model context, research configuration, and run action.
- [x] The model selector and research topic input are grouped as one focused
  configuration surface with a clearly associated run action.
- [x] Running, fallback, unavailable-server, no-model, empty-topic, success,
  and safe failure states remain distinct and visually understandable.
- [x] Completed results present report content and saved-report location in a
  readable, non-overlapping layout.
- [x] Existing labels, keyboard navigation, disabled states, and error safety
  behavior are preserved or improved.
- [x] Desktop and 390 px mobile layouts have no horizontal overflow, clipped
  text, obscured controls, or incoherent spacing.
- [x] Streamlit AppTest coverage protects the existing functional behavior, and
  browser validation verifies the polished UI at desktop and mobile widths.
- [x] Applicable formatting, linting, type checks, and `git diff --check` pass.

## UX Specification

### Visual Direction

- Use a calm, editorial research-workspace aesthetic rather than a marketing
  landing page or card-heavy dashboard.
- Use one expressive display face and a legible body face through Streamlit
  theme configuration; avoid default system typography.
- Favor a light mineral background with dark ink text, a restrained teal or
  forest accent for active actions, and a warm secondary accent for report
  metadata. Avoid purple gradients and decorative visual clutter.
- Keep page sections unframed where possible; reserve bordered containers for
  the run configuration and report result.

### Primary Flow

1. The user sees the product identity and local Ollama connection context.
2. The user selects a model and enters a topic in one organized configuration
   area, then starts the crew.
3. While the run is active, the configuration becomes unavailable and the page
   clearly communicates progress and selected model.
4. On completion, the report reads as a clear output document and the save
   location is secondary metadata.

## Out of Scope

- Changing Ollama model inventory, provider behavior, report storage, or CrewAI
  task execution.
- Adding custom HTML/JavaScript components, a marketing page, authentication,
  report browsing, or persistent user preferences.
- Replacing native Streamlit widgets with custom controls.

## Validation

- Run existing focused dashboard tests and add UI-level assertions only where
  the new hierarchy or states need coverage.
- Use browser screenshots and accessibility snapshots at desktop and 390 px
  mobile widths to check loading, empty, running, error, and result states.
- Verify the Streamlit theme loads and all visible text remains readable.