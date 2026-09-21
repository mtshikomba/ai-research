# Task 012: Enforce a 10-minute browser session and purge per-session knowledge data

## Story
As a product owner, I want each active browser session in the Streamlit app to expire after 10 minutes so that temporary research context and user-scoped knowledge do not persist beyond the active session window.

When a session expires, the system must remove only the session-specific knowledge data created for that browser session so the next session starts with a clean state and without stale context.

## Product scope and repository fit
This repo currently does not include a full authentication or multi-user backend. In this codebase, the practical definition of a “user session” is one browser session in the Streamlit dashboard. The session is therefore scoped to a browser/session ID and not to a shared global user account.

The storage boundary must be explicit:
- Global shared knowledge remains untouched.
- Only files created under a dedicated per-session directory are eligible for deletion.
- The implementation must not delete the project-level knowledge directory or any shared research assets.

## Session model
- Each browser session receives a session ID and a start timestamp at first load or first run.
- The session expires when the current timestamp exceeds the session start time plus 10 minutes.
- Expiration is enforced in the Streamlit app lifecycle, not only in the UI.
- When expired, the session is invalidated and the user is forced to start a fresh session.

## Required data scope for purge
The system must define and purge a dedicated session-local working area, for example:
- a session-scoped directory such as `sessions/<session-id>/knowledge` or equivalent
- any temporary extracted files, cached research context, and session-generated knowledge artifacts created under that directory only

The purge must not remove:
- the shared project `knowledge/` directory
- project-level Peshiko knowledge
- shared outputs under `reports/` that are not session-scoped
- any other global resources used by multiple users or sessions

## Acceptance Criteria
1. Session timer
   - A browser session is assigned a start timestamp when it begins.
   - The session is considered expired once 10 minutes have elapsed.
   - The user is shown a clear expiry message and is prevented from continuing with the expired session.

2. Session-specific knowledge purge
   - When the session expires, the app deletes only the user/session-specific knowledge artifacts created during that session.
   - The cleanup must remove temporary extracted files, cached summaries, and session-local knowledge generated for that browser session.
   - The deletion must occur on timeout, explicit session end, or interruption, and must be safe if run more than once.

3. Safety and data integrity
   - Global knowledge assets are never removed during a session purge.
   - The cleanup target must be a namespaced directory or metadata bucket that is unique to the active session.
   - The implementation must be idempotent: repeated cleanup attempts do not fail or leave partial state.
   - Expiry and cleanup logs must not surface session knowledge contents or sensitive research data.

4. User experience
   - The UI presents a visible countdown or warning near the 10-minute boundary.
   - At expiration, the app shows a clear reset message and requires the user to start a new session.
   - Expired session data is not still available in the next run.

5. Observability and operational behavior
   - The session expiry event records timestamp, session ID, and purge outcome status.
   - The log must show whether cleanup succeeded or failed without storing the deleted content itself.
   - Failed purge attempts must be visible to operators and must not silently leave stale session data behind.

## Non-Goals
- This work does not introduce a full authentication system or per-user account model.
- This work does not add persistent retention for shared enterprise knowledge.
- This work does not create a generic cross-user storage layer beyond the session-scoped data directory.

## Risks and technical notes
- The expiry clock must be enforced in the same place that owns the session lifecycle; otherwise stale session state can continue after the timer expires.
- The cleanup target must be a clearly namespaced, session-scoped directory, not a broad project path.
- The implementation should define the session-local storage directory before coding so the purge scope is unambiguous and auditable.

## UX / product notes
- The warning should be visible before the timeout so the user can finish or reset intentionally.
- Expiry should feel like a clean reset, not a backend crash or silent failure.
- If the user is mid-run when the timeout occurs, the system should gracefully stop and tell the user that their session-local knowledge was removed.

## Implementation readiness
This ticket is ready for engineering review. The remaining engineering decision is not product intent but implementation detail: the exact session-local storage path and the precise set of files under that path that count as session knowledge data.
