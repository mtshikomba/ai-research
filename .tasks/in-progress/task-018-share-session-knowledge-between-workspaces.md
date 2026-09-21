# Task 018: Share session knowledge between workspaces

## Story
As a user, I want the knowledge files I upload during my session to be available when I switch between Research and Executive briefing so that I do not need to upload the same materials twice.

The shared knowledge must remain private to my current browser session and must not become shared project knowledge or visible to another user session.

## Product requirement
Session Knowledge is one shared collection for the current browser session. Files uploaded from either the Research or Executive briefing workspace must be visible as available session knowledge in the other workspace and must be usable by local runs in both workspaces.

Switching workspaces must not clear, duplicate, relocate, or replace the current session knowledge. The collection remains stored under the existing session-scoped knowledge directory and is purged when the session expires.

## Scope
- Use one canonical session knowledge collection for all workspaces in a browser session.
- Make uploaded files available after switching between Research and Executive briefing.
- Allow uploads initiated from either workspace to add to the same collection.
- Show consistent readiness and file-count status in both workspaces.
- Keep local Research and local Executive briefing runs restricted to the shared current-session collection.
- Preserve session isolation and existing expiry cleanup.

## Acceptance Criteria
1. Cross-workspace availability
   - A file uploaded in Research is visible as available session knowledge in Executive briefing after switching workspaces.
   - A file uploaded in Executive briefing is visible as available session knowledge in Research after switching workspaces.
   - Switching workspaces does not require the user to upload the same file again.
   - Existing session uploads remain available after repeated workspace switches and reruns.

2. Shared session collection
   - Both workspace upload controls write to the same canonical session knowledge directory.
   - Uploading from either workspace adds to the session collection according to the documented add/replace behavior.
   - The UI reports the same usable-file count and readiness state in both workspaces.
   - Duplicate selections do not create misleading duplicate content or inflate the reported usable-file count unexpectedly.
   - A workspace switch does not clear valid session knowledge or show a false empty state.

3. Execution behavior
   - Local Research runs read only the shared current-session knowledge collection.
   - Local Executive briefing runs read only the same shared current-session knowledge collection.
   - Internet Research and Internet Executive briefing do not read session knowledge.
   - Adding knowledge in one workspace immediately makes it eligible for local execution in the other workspace after the normal Streamlit rerun.

4. Privacy and lifecycle
   - Session knowledge remains isolated from other browser sessions.
   - Session knowledge never writes to or modifies shared project knowledge or `knowledge/peshiko`.
   - The existing 10-minute session expiry purges the shared collection once, leaving shared project knowledge intact.
   - After expiry, both workspaces show an empty session knowledge state and require a new upload.

5. UX
   - Use consistent workspace-neutral copy such as `Session knowledge` in both workspaces.
   - Explain that the collection is shared between Research and Executive briefing for the current session.
   - Show readiness and usable-file count in both local modes.
   - Make add/replace behavior explicit and predictable when a user uploads from either workspace.
   - Do not suggest that session knowledge is available to Internet mode.
   - Keep the control and status readable at desktop and narrow/mobile widths.

6. Validation
   - Tests upload a file through the Research path and verify it is available to Executive briefing.
   - Tests upload a file through the Executive briefing path and verify it is available to Research.
   - Tests confirm both runners receive the same session knowledge directory.
   - Tests confirm workspace switching preserves files, readiness, and counts.
   - Tests confirm expiry purges the shared session collection without touching shared knowledge.
   - AppTest or browser validation covers upload, workspace switch, readiness, and local-run gating.
   - Full formatting, lint, and regression checks continue to pass.

## Non-Goals
- This work does not make session knowledge global, permanent, account-scoped, or available to another user.
- This work does not merge session knowledge into shared project knowledge or `knowledge/peshiko`.
- This work does not expose session knowledge to Internet research modes.
- This work does not change supported file formats or archive safety limits.
- This work does not redesign the overall dashboard navigation.

## Security and privacy notes
- Derive every workspace upload path from the same validated current session identifier.
- Keep the canonical session knowledge root explicit at the dashboard/service boundary.
- Do not trust workspace-specific filenames or widget state as an authorization boundary.
- Do not log private file contents or expose uploaded filenames beyond necessary validation feedback.
- Preserve the existing safe ZIP extraction and session purge boundaries.

## Implementation guidance
- Prefer one shared session knowledge state key and one canonical directory over separate Research and Executive stores.
- Avoid treating the Streamlit uploader widget's transient value as the source of truth; inspect the persisted session directory for readiness and counts.
- When both workspace uploaders are rendered conditionally, ensure switching does not discard or reset the persisted collection.
- Keep both `run_crew()` and `run_executive_crew()` pointed at the same explicit session knowledge path for local runs.
- Centralize shared upload, readiness, and status rendering where it reduces divergence without obscuring workspace-specific form behavior.

## UX review checklist
- Upload once in either workspace, switch workspaces, and see the same session-ready state.
- The status clearly communicates that the collection is shared across the two workspaces but private to the session.
- Local action buttons are enabled consistently when the shared collection is ready.
- Internet modes remain clearly separated from session knowledge.
- Expiry returns both workspaces to the same empty state.

## Ready for engineering
This ticket is ready for technical review. The required source boundary is one canonical, session-scoped knowledge collection shared by Research and Executive briefing while remaining unavailable to Internet modes and other sessions.
