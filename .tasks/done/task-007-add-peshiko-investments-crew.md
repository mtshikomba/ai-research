# task-007: add Peshiko Investments crew

## User Story

As a Peshiko Investments Group leader, I want an executive AI crew and
Streamlit dashboard so that I can submit business questions and receive an
organized CEO-led response incorporating financial, operational, and
information-management perspectives.

## Scope

- Add a dedicated Peshiko Investments Group CrewAI configuration and crew
  assembly separate from the existing research crew.
- Define four declarative executive agents:
  - **CEO:** orchestrates the crew, keeps recommendations aligned with company
    vision, reconciles tradeoffs, and produces the final executive brief.
  - **CFO:** analyzes accounting, finance, cash flow, budgeting, and financial
    risk from supplied information.
  - **COO:** analyzes daily operations, execution capacity, process, and
    operating risk from supplied information.
  - **CIO:** analyzes data, information systems, information quality, and
    technology risk from supplied information.
- Define a sequential executive workflow in which CFO, COO, and CIO assessments
  provide context for a final CEO synthesis.
- Add a Peshiko dashboard experience, accessible from the Streamlit app, that
  lets a user select an available Ollama model, submit an executive question,
  supply optional business context, start one crew run, and read the resulting
  executive brief.
- Save each executive brief under the existing ignored `reports/` structure,
  clearly identifying it as a Peshiko executive run.
- Reuse existing local Ollama selection, safe error handling, run-state control,
  and report-path safety boundaries.

## Acceptance Criteria

- [x] Peshiko has an isolated CrewAI configuration and assembly path; the
  existing research crew and dashboard flow remain functional.
- [x] CEO, CFO, COO, and CIO agents have declarative roles, goals, backstories,
  and task ownership appropriate to their responsibilities.
- [x] CFO, COO, and CIO assessments receive the submitted question and optional
  business context; the CEO receives their outputs and produces the final brief.
- [x] The final CEO brief distinguishes financial, operational, data/information,
  strategic, risk, and recommended-next-step considerations.
- [x] The dashboard exposes a Peshiko executive-workspace view with a labeled
  model selector, executive question input, optional business-context input,
  and clear run action.
- [x] The dashboard reuses the live Ollama model inventory and defaults to
  `gpt-oss:120b-cloud` when it is available.
- [x] Loading, empty-question, unavailable-server, no-model, running, success,
  and safe failure states are actionable; duplicate submissions are prevented.
- [x] Successful executive runs save an ignored report under a unique
  `reports/` subdirectory and display the saved path with the selected model.
- [x] No credentials, private prompts, or raw sensitive provider errors are
  rendered in the dashboard or logs.
- [x] Focused tests cover executive crew configuration, task context flow,
  dashboard inputs, selected-model propagation, report storage, and safe errors
  without a live LLM.
- [x] Streamlit AppTest and desktop/mobile browser validation cover the Peshiko
  dashboard’s initial, empty, loading, running, success, and error states.
- [x] Applicable formatting, linting, type checks, and a real local Ollama smoke
  run pass.

## UX Specification

### Primary Flow

1. The user enters the Peshiko executive workspace from the Streamlit app.
2. The user selects an Ollama model, submits an executive question, and may add
   relevant business context such as a reporting period, financial figures, or
   operating constraints.
3. The page identifies that CFO, COO, and CIO assessments are being prepared
   for CEO synthesis while the run is active.
4. The final executive brief presents recommendations first, followed by
   financial, operational, and information considerations and the saved report
   location.

### Responsive and Accessibility Requirements

- Preserve visible labels and keyboard order for model, question, context, and
  submit controls.
- Keep the executive input fields vertically usable at 390 px widths with no
  horizontal overflow or obscured result content.
- Use native Streamlit controls and the existing research-workspace visual
  language; do not build a marketing page or custom HTML component.

## UX Review Handoff

### Workspace Structure

- Make `Peshiko Investments Group` the first visible identifier in the
  executive workspace, with `Executive briefing` as the supporting context.
- Keep the Ollama server and selected model as quiet operational context in the
  sidebar, using the established model-selector pattern.
- Group the executive question, optional business context, and run action in a
  single bordered briefing surface. The optional context field must clearly
  indicate that users should not provide credentials or account access details.
- Use a distinct, clearly labeled view switch or navigation item to separate
  `Research` from `Executive briefing`; preserve the existing research flow.

### Result Hierarchy

- Present the CEO recommendation and next steps first.
- Follow with clearly labeled CFO, COO, and CIO perspectives, then a compact
  risk-and-assumptions section and saved-report metadata.
- Treat the selected model and saved path as secondary operational details;
  they must not compete with the executive recommendation.
- Do not display hidden prompts, agent chain-of-thought, raw tool output, or
  provider exception details.

### Required States

- **Loading:** Reserve the briefing result area while the local model inventory
  or crew is loading so the page does not jump.
- **Empty question:** Keep the submitted context intact and show an inline,
  actionable validation message beside the executive intake surface.
- **Running:** Disable the model, question, context, and submit controls; show
  that CFO, COO, and CIO assessments are being prepared for CEO synthesis.
- **Unavailable server/no models:** Show a safe, actionable status and disable
  the executive run action without erasing entered question/context values.
- **Success:** Show the CEO-led brief, selected model, and saved report path in
  stable regions that do not overlap at desktop or mobile widths.
- **Failure:** Show a concise recovery message with no sensitive provider data.

### UX Acceptance Criteria

- [x] The executive workspace has a visible Peshiko Investments Group identity
  and a clear navigation distinction from the research workspace.
- [x] The briefing form groups model, executive question, optional business
  context, and run action with visible labels and logical keyboard order.
- [x] CEO recommendations appear before CFO, COO, and CIO perspectives in a
  completed executive brief.
- [x] Loading, empty, running, unavailable, success, and failure states retain
  entered values where applicable and communicate safe next actions.
- [x] At desktop and 390 px mobile widths, no executive text, controls, result
  sections, model details, or saved-report metadata overlap or overflow.

## Assumptions and Open Inputs

- The first release analyzes user-supplied context only; it does not connect to
  accounting systems, banking, ERP, document stores, or external market data.
- Executive outputs are advisory and must not initiate transactions, change
  records, or make autonomous investment decisions.
- The exact Peshiko corporate vision, investment mandate, reporting cadence,
  and financial/operational data schemas will be provided in a follow-up ticket
  before external data integrations are introduced.

## Out of Scope

- Connecting to accounting, banking, ERP, CRM, or document-management systems.
- Persistent user accounts, authorization, multi-user workspaces, or automated
  investment and operational actions.
- Replacing the existing research crew or deleting existing dashboard behavior.

## Validation

- Use mocked CrewAI and Ollama boundaries to verify executive task orchestration
  and dashboard state behavior.
- Run the Peshiko crew with a non-sensitive sample business question through the
  configured local Ollama server.
- Verify ignored executive reports are not included in the staged change set.
- Validate desktop and 390 px mobile dashboard flows and screen-reader-visible
  labels through Streamlit AppTest and browser accessibility snapshots.