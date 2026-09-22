# Task 016: Download research reports as Markdown or PDF

## Story
As a user, I want to download my completed research report as a Markdown or PDF file so that I can archive, share, or continue working with the result outside the dashboard.

The download options should be available for reports produced by both the Research and Executive briefing workspaces.

## Product requirement
After a successful run, the dashboard must provide clear download actions for the generated report in its existing Markdown form and as a PDF. Downloads must use the completed report for the current run, preserve the report content, and avoid exposing unrelated reports or private session knowledge.

The existing report directory structure and `report.md` artifact remain canonical. PDF bytes must be generated on demand when the user requests a PDF download and must not be cached or stored as a permanent second report artifact.

## Scope
- Add a Markdown download action for completed Research reports.
- Add a PDF download action for completed Research reports.
- Add the same Markdown and PDF download actions for completed Executive briefing reports.
- Use the current run's report content and filename-safe download names.
- Generate PDF bytes only when the user requests the PDF download.
- Keep report downloads available after the run result is rendered during the active Streamlit session.
- Preserve the existing report storage path and report output behavior.

## Acceptance Criteria
1. Markdown downloads
   - A completed Research report can be downloaded as a `.md` file.
   - A completed Executive briefing can be downloaded as a `.md` file.
   - The Markdown download contains the complete generated report content, not only the visible summary or metadata.
   - The download filename is stable, descriptive, and ends in `.md`.

2. PDF downloads
   - A completed Research report can be downloaded as a `.pdf` file.
   - A completed Executive briefing can be downloaded as a `.pdf` file.
   - The PDF contains the report content in a readable layout with preserved headings, paragraphs, and basic Markdown structure where practical.
   - PDF generation occurs on demand and does not run during report execution or initial result rendering.
   - PDF bytes are not cached in the reports directory or retained as a permanent artifact after download.
   - The PDF is generated safely without exposing credentials, local paths, private session knowledge, or unrelated report data.
   - The download filename is stable, descriptive, and ends in `.pdf`.

3. Report integrity and isolation
   - Downloaded Markdown and PDF content correspond to the selected completed run.
   - A user cannot download another report merely by changing a visible label or topic value.
   - Downloads do not read arbitrary filesystem paths supplied by the user.
   - Existing report directories and `report.md` files remain unchanged by normal downloads.
   - Session-scoped knowledge is not included in a report download unless it was intentionally incorporated into the generated report output.

4. UX
   - Download actions appear next to the completed report result in both workspaces.
   - Actions are clearly labeled, for example `Download Markdown` and `Download PDF`.
   - Actions are not shown before a report is successfully generated.
   - The controls remain usable at desktop and narrow/mobile widths without overlapping the report content.
   - PDF generation failure produces an actionable message while leaving Markdown download available.
   - Download actions do not trigger a new CrewAI run or modify the report content.

5. Validation
   - Tests verify Markdown bytes match the completed report content.
   - Tests verify generated PDF output is non-empty and has a valid PDF signature or can be parsed by the selected PDF validation tool.
   - Tests cover both Research and Executive briefing report downloads.
   - Tests cover safe download filenames and report-path containment.
   - AppTest or equivalent UI validation confirms download actions appear only after a successful result.
   - Formatting, linting, and the full existing test suite continue to pass.

## Non-Goals
- This work does not redesign report content or the report storage directory structure.
- This work does not add DOCX, HTML, or other export formats.
- This work does not create permanent user accounts or cloud document storage.
- This work does not make reports publicly accessible or add sharing links.
- This work does not expose raw CrewAI execution logs or private uploaded knowledge as separate downloads.

## Security and privacy notes
- Treat report paths and download names as application-controlled values, not direct user filesystem paths.
- Keep generated files contained within the existing reports boundary or use in-memory download bytes.
- Do not include credentials, provider settings, private prompts, or internal filesystem paths in downloaded output unless they are already part of the intentional report content.
- Avoid logging report contents or generated PDF bytes.
- If a PDF library is introduced, pin or constrain it consistently with the repository dependency policy and validate its input/output boundary.

## Implementation guidance
- Reuse the existing completed `report.md` path from `CrewRunResult` and `ExecutiveRunResult`.
- Prefer Streamlit download controls backed by bytes or validated application-owned paths.
- Keep Markdown export direct and deterministic.
- Isolate PDF conversion in a focused helper that can be unit-tested independently from CrewAI execution.
- Prefer an established Python PDF-generation library over handwritten PDF syntax.
- Preserve the report's Markdown content as the source of truth for both formats.
- Invoke the PDF conversion helper only from the PDF download action; keep Markdown download immediate and independent.

## UX review checklist
### Primary flow
1. The user completes a Research run or Executive briefing successfully.
2. The completed report appears in its existing bordered result container.
3. A compact export action row appears directly below the report content and before technical metadata.
4. The user can download Markdown immediately from the current report.
5. The user explicitly requests PDF generation, waits for the conversion to complete, and then downloads the generated in-memory PDF.

### Placement and controls
- Place the export actions in the completed report container, directly below the rendered report and above `Model`, `Research source`, and `Saved report` metadata.
- Use a responsive horizontal action group that wraps cleanly on narrow screens.
- Label actions clearly as `Download Markdown` and `Download PDF`; use familiar download icons where supported without relying on icons alone.
- Keep the Markdown action available independently if PDF generation fails.
- Do not show export actions before a successful result, during a run, or after a run error.

### On-demand PDF states
- Before request: show a `Download PDF` action without generating PDF bytes during initial result rendering.
- While converting: show a clear busy state and prevent duplicate PDF requests.
- Ready: provide the PDF download action with the same report-specific filename and indicate that the file is ready.
- Conversion error: show an actionable error near the export actions and keep `Download Markdown` working.
- Do not expose generated PDF bytes, temporary paths, or conversion tracebacks in the visible UI.

### Responsive and accessibility criteria
- Export controls remain readable and usable at desktop and narrow/mobile widths; they may wrap vertically without overlapping report content.
- Controls have visible text labels, predictable focus order, and clear disabled/busy states.
- Download feedback must not rely on color alone.
- Filenames should identify the workflow/report without exposing private session paths or uploaded filenames.

## Ready for engineering
UX review is complete with the export placement, responsive behavior, and on-demand PDF states defined above. This ticket is ready for technical review; implementation only needs to select a maintained PDF-generation library and generate in-memory download bytes when the user explicitly requests the PDF.
