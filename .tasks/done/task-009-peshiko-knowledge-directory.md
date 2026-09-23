# task-009: create peshiko knowledge directory

## User Story

As a Peshiko Investments executive, I want a dedicated local knowledge directory for investment data, historical documents, company branding, and report templates so that the CEO can generate polished PDF briefings from a consistent corporate identity and a secure working store that is never committed to Git.

## Scope

- Create a project-local directory under `knowledge/` for Peshiko-specific working materials, such as:
  - `knowledge/peshiko/`
  - `knowledge/peshiko/business-data/`
  - `knowledge/peshiko/historical-documents/`
  - `knowledge/peshiko/report-templates/`
  - `knowledge/peshiko/letterhead/`
  - `knowledge/peshiko/brand/`
- Keep all files in this directory strictly local-only and excluded from version control.
- Provide the structure needed for business data, historical documents, branded letterhead, and executive report templates.
- Ensure the CEO workflow can use the letterhead and report template when producing a PDF report document.
- Include a clear archive-handling workflow for zipped business data and historical documents, so packaged files in the local Peshiko knowledge store are retrieved, extracted, and made available for the crew before any external research.
- Define a local-first evidence policy: the Peshiko crew must check the local `knowledge/peshiko/` materials first, including extracted archive contents, and only use internet research when there is no relevant local data available.
- Document the intended use of this directory in the project docs or operational guidance.

## Acceptance Criteria

- [ ] A `knowledge/peshiko/` directory exists in the repository root and contains the required subdirectories for business data, historical documents, report templates, and brand/letterhead assets.
- [ ] These files are ignored by Git and are never committed.
- [ ] No generated or sensitive business content is accidentally added to the tracked repository tree.
- [ ] The project includes a clear, local-only convention for storing the brand package, template assets, and historical documents under `knowledge/`, including zipped archives when present.
- [ ] The Peshiko crew prioritizes `knowledge/peshiko/` data sources before any external internet lookup, including extracted contents from any zipped business or historical documents.
- [ ] Archived local business data and historical documents are retrieved and extracted into the local store so they can be used as primary evidence before internet fallback.
- [ ] Internet research is only used as a fallback when the local Peshiko knowledge store does not contain relevant information for the task.
- [ ] The CEO workflow can reference and apply the letterhead and report template when creating a report PDF.
- [ ] Documentation or code comments explain the purpose of the directory, the archive-handling workflow, the local-first policy, and the expected file usage.
- [ ] The implementation does not affect the current active research-crew behavior outside the new local knowledge workflow.

## Out of Scope

- Creating live financial or market data pipelines.
- Uploading or syncing sensitive company documents to a remote service.
- Changing the current default report generation behavior beyond adding the local Peshiko asset workflow.

## Validation

- Verify the `knowledge/peshiko/` structure exists in the working tree.
- Check `.gitignore` includes the local knowledge directory so it stays untracked.
- Confirm this directory is excluded from the git status output for local business content.
- Review the workflow docs or code paths to ensure the report template and letterhead are intended for use by the CEO PDF generation flow.
