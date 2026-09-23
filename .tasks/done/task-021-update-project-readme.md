# Task 021: Rewrite the README for the AI Research project

## Story
As a user or contributor, I want the README to describe this project accurately so that I can understand its purpose, available features, setup, and supported workflows without encountering template or unrelated documentation.

## Product requirement
Rewrite `README.md` to speak only about this repository and its implemented functionality. The README must present accurate, concise documentation for the AI Research dashboard, its Research and Executive Briefing workspaces, Ollama configuration, session-scoped knowledge, report downloads, and session lifecycle behavior.

The README must not describe features, integrations, workflows, support channels, branding, or future capabilities that are not implemented in this project.

## Scope
- Replace the generic template introduction with an accurate AI Research project overview.
- Document installation using the repository's UV and Python requirements.
- Document Ollama configuration using the supported environment variables.
- Document how to launch the Streamlit dashboard.
- Describe the Research workspace and its Internet and Local knowledge modes.
- Describe the Executive Briefing workspace.
- Describe session-scoped knowledge uploads, supported file types, ZIP safety, workspace sharing, and session expiry.
- Describe Markdown and on-demand PDF report downloads.
- Describe active-run Stop behavior and its cooperative cancellation contract.
- Describe independent Research and Executive workspace name customization with the current generic defaults.
- Remove stale template, unrelated workflow-reuse, and generic support sections.

## Acceptance Criteria
1. Project identity
   - The README names and describes this repository as AI Research.
   - The introduction explains the local-first research dashboard without referring to a generic scaffold or unrelated project.
   - Technical package names such as `my_research_crew` are mentioned only where needed for commands or repository structure.

2. Setup and configuration
   - The README states the supported Python version range: `>=3.10,<3.13`.
   - Installation uses the repository's UV workflow and existing dependency lockfile.
   - Ollama configuration documents `MODEL` and `API_BASE` without inventing unsupported settings.
   - Dashboard startup uses the actual `streamlit run src/my_research_crew/dashboard.py` command.
   - Instructions do not require credentials, cloud accounts, or services not used by the project.

3. Implemented functionality
   - The README accurately documents the Research workspace and its Internet and Local knowledge source choices.
   - The README accurately documents the Executive Briefing workspace and its question/context workflow.
   - The README accurately documents session-scoped knowledge uploads, supported file formats, ZIP validation, workspace sharing, and 10-minute expiry cleanup.
   - The README accurately documents Markdown downloads and on-demand PDF generation.
   - The README accurately documents the Stop action and cooperative cancellation limitation without promising forceful provider termination.
   - The README accurately documents independent workspace names with defaults `Research Crew` and `Executive Briefing`.
   - All documented behavior matches current source code and user-facing labels.

4. Accuracy boundaries
   - Remove generic crewAI template language that does not describe this project.
   - Remove the unrelated `ProjectContext` reuse-in-another-repository section.
   - Remove generic support links, Discord invitations, and calls to action that are not project-specific requirements.
   - Do not claim shared project knowledge is used by session-local runs when the current implementation uses session uploads.
   - Do not claim permanent storage, account-level settings, authentication, arbitrary document formats, or forceful cancellation unless implemented separately.

5. Documentation quality
   - Organize the README with concise sections for overview, requirements, setup, configuration, dashboard usage, knowledge, reports, and session behavior.
   - Use copyable commands and accurate repository-relative paths.
   - Explain important safety/privacy behavior without exposing credentials or private data.
   - Keep the README readable on GitHub and avoid unnecessary template narrative.

6. Validation
   - Every command and path in the README exists or is supported by the repository.
   - A documentation review compares each feature claim against the implementation and tests.
   - Run applicable Markdown or repository documentation checks if available.
   - The change must not modify application code or dependencies.

## Non-Goals
- This work does not change application behavior or add new features.
- This work does not rename Python packages, classes, report paths, or Streamlit keys.
- This work does not create a separate user manual or API reference.
- This work does not document speculative roadmap items.

## Documentation safety notes
- Never include real credentials, private server tokens, or sensitive local knowledge examples.
- Use placeholder local-network values only where already established by the project configuration.
- Keep statements about local files, session expiry, reports, and cancellation aligned with current implementation behavior.

## Implementation guidance
- Use the current dashboard labels and source behavior as the authoritative user-facing vocabulary.
- Verify claims against `dashboard.py`, `dashboard_service.py`, `research_sources.py`, `report_exports.py`, `execution_service.py`, and the test suite.
- Preserve useful setup instructions while rewriting the narrative around this project.
- Prefer concise examples that users can run from the repository root.

## Ready for engineering
This ticket is ready for implementation as a documentation-only change. The README should describe only verified AI Research functionality and remove all generic or unrelated material.
