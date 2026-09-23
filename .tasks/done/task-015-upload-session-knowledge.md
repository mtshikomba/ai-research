# Task 015: Upload session knowledge for research and executive briefings

## Story
As a user, I want to upload knowledge files or a ZIP folder into my session knowledge area so that local research and executive briefings can read and use my own materials.

Uploaded knowledge must remain isolated to my current session and must not modify shared project knowledge or another user's session.

## Product requirement
The dashboard must provide an optional upload workflow for supported knowledge files and ZIP archives. Uploaded content must be stored under the current browser session's session-scoped knowledge directory and made available to local Research and Executive briefing runs after successful validation.

When the user selects local knowledge in either the Research or Executive briefing workspace, that workflow must read only the uploaded content in the current session's knowledge directory. Shared project knowledge, including `knowledge/peshiko`, must not be included in that run, and uploads must never overwrite or contaminate the shared `knowledge/` directory.

## Scope
- Add a multi-file uploader to the dashboard knowledge workflow.
- Accept supported individual knowledge files and ZIP archives containing supported files.
- Store uploaded files beneath the current session's knowledge directory.
- Make the current session's knowledge directory the exclusive local-research source.
- Reuse or extend the existing local-knowledge validation and safe ZIP extraction behavior.
- Show the user whether uploaded content is ready for local research and executive briefing runs.
- Apply the same session upload flow to the Research and Executive briefing workspaces.
- Ensure session expiry cleanup removes uploaded session knowledge through the existing purge boundary.

## Acceptance Criteria
1. Uploads
   - The user can upload one or more supported knowledge files.
   - The user can upload a ZIP file representing a knowledge folder.
   - Supported individual file types include the existing approved formats: TXT, Markdown, CSV, JSON, YAML, and YML.
   - Unsupported file types are rejected safely with an actionable user-facing message.
   - Empty uploads do not crash the dashboard.

2. Session isolation
   - Uploaded files are written only beneath the current session's knowledge directory.
   - Uploads never write into or replace the shared project `knowledge/` directory.
   - A user's uploaded content is not visible to another browser session.
   - Session expiry removes the uploaded session knowledge and leaves shared knowledge intact.

3. Safe archive handling
   - ZIP archives are validated before extraction.
   - Archive path traversal, absolute paths, symbolic links, encrypted entries, corrupt archives, excessive file counts, and excessive uncompressed size are rejected safely.
   - Extracted files remain contained within the current session's knowledge directory.
   - Existing file-size and total-context limits remain enforced.

4. Local research behavior
   - After a successful upload, the dashboard reports the session knowledge as ready when it contains usable content.
   - A local research run reads the uploaded session knowledge content.
   - A local research run reads only the current session's knowledge directory.
   - Shared project knowledge is not merged into, searched by, or used as fallback content for the session's local run.
   - The run does not silently fall back to internet research when local mode is selected and uploaded content is invalid or unavailable.
   - The research result identifies local knowledge as its selected source without exposing private file contents in status messages or logs.

5. Executive briefing behavior
   - The Executive briefing workspace exposes the same session knowledge uploader and readiness state when `Local knowledge` is selected.
   - A local executive briefing reads only the current session's knowledge directory.
   - Shared `knowledge/peshiko` content is not merged into, searched by, or used as fallback content for the session's local executive briefing.
   - The executive run remains disabled until the session knowledge contains usable content.
   - The executive result identifies local knowledge as its selected source without exposing private file contents in status messages or logs.

6. UX
   - The uploader is clearly labeled as session knowledge or private session knowledge.
   - The UI explains which file formats are accepted and that uploads are removed when the session expires.
   - Upload success, rejection, and empty/invalid knowledge states are understandable and actionable.
   - The uploader and readiness status remain usable at desktop and narrow/mobile widths.
   - The user can replace or add to the current session knowledge without restarting the application.
   - The uploader and readiness message are available in both Research and Executive briefing local modes.

7. Validation
   - Tests cover individual supported file uploads.
   - Tests cover ZIP upload and safe extraction into the session directory.
   - Tests confirm shared knowledge is not modified.
   - Tests cover invalid file types and unsafe/corrupt archives.
   - Tests confirm local research consumes the session upload directory.
   - Tests confirm local executive briefings consume the session upload directory and exclude shared Peshiko knowledge.
   - AppTest or equivalent UI validation covers upload, readiness, and error states in both workspaces.

## Non-Goals
- This work does not add permanent cloud storage or account-level document management.
- This work does not expose uploaded content to internet research mode or internet executive briefings.
- This work does not read from or modify shared project knowledge during a session's local Research or Executive briefing run.
- This work does not remove the existing 10-minute session expiry policy.
- This work does not add unsupported document parsers such as PDF, DOCX, XLSX, or images unless separately approved.

## Security and privacy notes
- Treat uploaded filenames and archive entries as untrusted input.
- Keep all resolved upload and extraction paths beneath the session knowledge root.
- Do not log file contents, credentials, or private uploaded data.
- Enforce validation in Python; browser uploader restrictions are only a UX guardrail.
- Preserve the existing session purge boundary and never broaden it to shared project knowledge.

## Implementation guidance
- Use the existing session identifier to derive the upload directory.
- Prefer the existing `inspect_local_knowledge` and `prepare_local_knowledge` safety rules rather than duplicating archive parsing, while passing only the session knowledge path to those helpers.
- Keep upload persistence and local-context preparation in focused service/research-source helpers, not inside CrewAI orchestration.
- Make the session knowledge root explicit at the dashboard/service boundary so tests can verify containment.
- Keep the shared project `knowledge/` path out of the local session run entirely; do not implement a merge or fallback between the two roots.
- Pass the explicit session knowledge path into both research and executive briefing execution boundaries; do not let either runner discover shared knowledge implicitly.

## UX review
### Primary flow
1. The user selects either the Research or Executive briefing workspace.
2. The user selects `Local knowledge` in that workspace's Research source control.
3. The dashboard reveals a clearly labeled `Session knowledge` upload area in the active setup section.
4. The user uploads one or more supported files or one ZIP folder.
5. The dashboard validates and stores the upload under the current session, then shows a ready state with the number of usable files.
6. The user enters a topic or executive question and runs the selected workflow against only that session upload directory.

### Placement and copy
- Place the uploader in the active Research setup or Executive briefing container directly below that workspace's Research source selector, not in the sidebar.
- Label it `Session knowledge` or `Private session knowledge`.
- Explain: `Upload TXT, Markdown, CSV, JSON, YAML, or ZIP files. These files are private to this session and are deleted when the session expires.`
- Do not describe shared project knowledge as available for local research, because local mode is session-upload-only.
- Keep the existing Internet-mode explanation visible when Internet is selected, while hiding or disabling the session uploader when it is not relevant.
- Use workspace-neutral copy so the same control explains that uploads support both local research and local executive briefings.

### Required states
- Empty local state: explain that the user must upload supported content before the active local workflow can run; keep the relevant Run research or Prepare executive brief button disabled.
- Ready state: show a concise success message such as `Session knowledge is ready: N usable files.` and confirm that the run will stay local.
- Rejected upload: identify that the upload was not accepted and explain the supported formats or safety reason without exposing file contents.
- Mixed upload: accept valid files, report rejected files separately, and make clear which content is available for the run.
- Expired session: show the existing expiry warning and return the uploader to an empty state after session knowledge is purged.
- Upload replacement/addition: make the behavior explicit in the control copy or affordance so users know whether a new selection adds to or replaces existing session files.
- Executive local state: show the same session-ready message and make clear that the briefing will use only private session uploads, not shared Peshiko knowledge.

### Responsive and accessibility criteria
- The uploader, status message, and disabled run action must remain readable at narrow/mobile widths without horizontal scrolling.
- Status must not rely on color alone; use clear text and Streamlit status elements.
- The upload control must have a visible label and accepted-file guidance.
- Do not display uploaded private filenames or file contents in logs or broad dashboard status areas unless needed to explain a validation error.

## Ready for engineering
The source boundary is resolved: local Research and Executive briefing workflows use only the current session's uploaded knowledge directory. UX review is complete with the primary flow, placement, state, privacy-copy, and responsive criteria above. The ticket is ready for technical approval and implementation.
