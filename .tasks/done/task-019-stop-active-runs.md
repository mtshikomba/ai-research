# Task 019: Disable run actions and allow users to stop active runs

## Story
As a user, I want the Research and Executive briefing run buttons to become inactive immediately after starting a run, and I want a clear way to stop an active run if it is taking too long or is no longer needed.

## Product requirement
When a Research or Executive briefing run starts, the dashboard must enter an explicit active-run state before execution begins. The submitted run action and other conflicting inputs must be disabled while the run is active, and a visible Stop action must be available.

Pressing Stop must request cancellation of the active run, prevent its result from being presented as a successful completed report, restore the workspace to an idle state, and communicate clearly whether the run stopped before completion. The same behavior must apply to Research and Executive briefing.

## Scope
- Disable `Run research` immediately after submission.
- Disable `Prepare executive brief` immediately after submission.
- Disable conflicting workspace, source, model, topic, question, and knowledge-upload controls while a run is active.
- Add a visible Stop action for the active Research or Executive briefing run.
- Define and implement a cooperative cancellation boundary for CrewAI/Ollama execution.
- Restore idle controls after successful completion, failure, or cancellation.
- Ensure cancelled runs do not leave misleading successful results or stale busy state.

## Acceptance Criteria
1. Run-state transitions
   - Before submission, the relevant run action is enabled when all inputs are valid.
   - On submission, the app records the active run state before starting provider execution.
   - While active, the submitted action is disabled and cannot start a duplicate run.
   - Workspace switching, source selection, model selection, knowledge upload, and run inputs are disabled or otherwise protected from conflicting changes while active.
   - On success, failure, or cancellation, the app returns to an idle state.

2. Stop behavior
   - A clearly labeled `Stop` action is visible while a Research run is active.
   - A clearly labeled `Stop` action is visible while an Executive briefing run is active.
   - Pressing Stop requests cancellation without starting another CrewAI run.
   - The user receives a clear status message such as `Run stopped` or `Run cancellation requested`.
   - A cancelled run does not render a successful Research report or Executive brief.
   - A cancelled run does not leave a stale report result in the active workspace.
   - The Stop action becomes unavailable after the run has completed, failed, or been cancelled.

3. Cancellation contract
   - The cancellation mechanism explicitly states whether it interrupts provider execution immediately or cooperatively stops at the next safe boundary.
   - Provider, subprocess, or CrewAI resources are cleaned up after cancellation.
   - A cancellation request that arrives just after completion produces one consistent final state, not both success and cancellation.
   - Cancellation failures are surfaced as safe, actionable messages without exposing credentials, prompts, or raw provider traces.
   - Existing 10-minute session expiry and session-knowledge purge behavior remain intact during active or cancelled runs.

4. Report and data safety
   - No cancelled result is presented as a completed report or executive brief.
   - Partial files, if produced by the underlying run, are not advertised as final downloadable reports.
   - Existing completed reports from earlier runs remain unaffected.
   - Session knowledge remains unchanged by stopping a run.
   - The Stop action cannot broaden filesystem, subprocess, provider, or network access.

5. UX
   - Active-run state is visually and textually obvious without relying on color alone.
   - The Stop control is placed near the active progress/status indicator and remains usable at desktop and narrow/mobile widths.
   - The user can distinguish `running`, `cancellation requested`, `cancelled`, `failed`, and `completed` states.
   - Controls do not flicker back to enabled while provider work is still active.
   - A successful or failed run preserves the existing result and error presentation patterns.
   - The user is not asked to restart the browser or application to recover from a stopped run.

6. Validation
   - Tests verify the run action becomes disabled during an active Research run.
   - Tests verify the run action becomes disabled during an active Executive briefing run.
   - Tests verify duplicate submissions are rejected while active.
   - Tests verify Stop requests cancellation for both workflows.
   - Tests verify cancellation returns the UI to idle and does not render a successful result.
   - Tests cover completion racing with a cancellation request.
   - AppTest or browser validation confirms active, stopping, cancelled, failed, and completed states.
   - Full formatting, lint, and regression checks continue to pass.

## Non-Goals
- This work does not redesign the entire dashboard execution experience.
- This work does not guarantee forceful termination of an external provider process unless the selected execution architecture supports it safely.
- This work does not add arbitrary process-kill controls exposed to users.
- This work does not change CrewAI prompts, research-source policy, session knowledge scope, or report content.
- This work does not cancel already completed runs or delete previously completed reports.

## Security and reliability notes
- Treat Stop as a state transition request, not as permission to execute arbitrary shell commands.
- Keep cancellation state scoped to the current Streamlit browser session.
- Do not use shared module-level mutable cancellation state across users.
- Ensure provider credentials and private prompts are not included in cancellation messages or logs.
- Bound cleanup and cancellation waits so a stopped run cannot leave the dashboard permanently busy.

## Implementation guidance
- Model execution as an explicit state machine, for example `idle`, `running`, `cancellation_requested`, `cancelled`, `failed`, and `completed`.
- Use session state for the current run state and cancellation request, with a run identifier to reject stale callbacks.
- Select an execution approach that permits the UI to rerun while work is active; a synchronous callback cannot provide a responsive Stop control by itself.
- Keep Research and Executive briefing cancellation behavior behind a shared execution-state abstraction where practical.
- Preserve existing safe error handling and report-result persistence for completed runs.

## UX review checklist
- Start Research, confirm the button disables, then stop the run.
- Start Executive briefing, confirm the button disables, then stop the run.
- Confirm workspace and source controls do not allow conflicting changes while active.
- Confirm cancellation messages are clear and the idle state returns without a false result.
- Confirm narrow/mobile layout keeps the Stop action visible and usable.

## UX review
### Primary flow
1. The user enters a valid Research topic or Executive question and submits the run.
2. The dashboard immediately replaces the submit action with an active-run status region.
3. The status region shows the workflow name, a concise progress message, and a visible `Stop` action.
4. The user can stop the run, receives a cancellation status, and returns to an idle form without a false result.
5. On completion or failure, the status region is replaced by the existing result or error presentation.

### Placement and state copy
- Place the active-run status directly beside or immediately above the disabled run form controls; keep the Stop action in the same visual group as the progress indicator.
- Use clear text states: `Running research`, `Running executive briefing`, `Stopping...`, `Run stopped`, `Run failed`, and `Run completed`.
- The submit button must visibly change to a disabled state as soon as the run is accepted.
- Disable workspace switching, source selection, model selection, uploads, and input fields while active; do not merely hide their current values.
- After cancellation, preserve the entered topic/question where possible so the user can adjust and retry without retyping.
- Do not show download controls or a completed-result panel for a cancelled run.

### Cancellation interaction
- `Stop` must be a normal visible button with a text label, not a hidden keyboard action or icon-only control.
- The first click changes the label/state to `Stopping...` and disables duplicate Stop clicks.
- The user must see whether cancellation is requested or complete; do not imply immediate termination if the provider stops cooperatively.
- If cancellation cannot complete, show an actionable safe error and retain a clear busy state until the execution boundary is resolved.
- A completion/cancellation race must show exactly one terminal state.

### Responsive and accessibility criteria
- The Stop action remains visible and reachable at desktop and 390px-wide mobile layouts.
- The active status and Stop action wrap vertically without horizontal scrolling or overlapping form content.
- State changes are conveyed through text and accessible button labels, not color alone.
- Focus moves predictably to the active status or Stop action after submission where the chosen async architecture permits it.
- Screen readers can distinguish the workflow, current state, and available Stop action.

### Browser acceptance flow
- Start a Research run in a browser and verify the submit button becomes disabled before provider work completes.
- Verify `Stop` is visible, click it, and verify `Stopping...` then `Run stopped` or the documented cooperative-cancellation result.
- Repeat the same flow for Executive briefing.
- Verify no successful report/download controls appear after cancellation.
- Verify the controls return to idle and a new run can be started without refreshing the browser.

## UX review outcome
The asynchronous dashboard shell and visible Stop control now use a cooperative cancellation boundary. The cancellation event is propagated into both `run_crew()` and `run_executive_crew()`, checked before provider work starts, and checked again after provider return so a late result is discarded when Stop was requested.

The provider call itself is not force-killed; the UI truthfully reports `Stopping...` until the active operation reaches the safe boundary. This is the documented cancellation contract and prevents cancelled output from being published as a completed result.

## Ready for engineering
UX review is complete. The cooperative cancellation contract is implemented for Research and Executive briefing, with active-state, Stop, cancellation, and late-result safety tests passing. Browser validation should confirm the terminal stopped state against a real provider run before release.
