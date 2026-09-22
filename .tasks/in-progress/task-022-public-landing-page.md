# Task 022: Create a focused public landing page

## Story
As a prospective user visiting the public AI Research site, I want to understand the application's use case and core capabilities quickly so that I can decide whether it fits my research and executive briefing workflow.

## Product requirement
Create a concise, public-facing landing page for AI Research. The page should explain what the application does, who it helps, and the small set of implemented features that matter to a prospective user. It must guide interested users to the working dashboard without becoming a second technical README or exposing private application details.

The landing page must use only verified functionality currently present in the application. It must not claim unsupported integrations, permanent storage, authentication, collaboration, account management, forceful cancellation, or other roadmap features.

## Scope
- Add a public landing page for the AI Research repository/application.
- Present the primary use case: local-first research and executive briefings using Ollama.
- Present the implemented Research and Executive Briefing workspaces.
- Present session-scoped knowledge uploads and cross-workspace availability.
- Present Internet and Local knowledge source separation.
- Present Markdown and on-demand PDF report downloads.
- Present active-run Stop behavior accurately as cooperative cancellation.
- Provide a clear primary action to open or launch the working dashboard.
- Keep the public page visually focused, responsive, accessible, and free of unrelated project noise.

## Acceptance Criteria
1. Public purpose and audience
   - The first viewport clearly identifies AI Research.
   - The page explains the core use case in concise language: research and executive briefings in a local-first workspace powered by Ollama.
   - The page identifies relevant users or use cases without inventing market claims, customer logos, metrics, or testimonials.
   - The page communicates the privacy-oriented session model without promising account-level privacy or permanent storage.

2. Verified feature presentation
   - The page accurately presents the Research workspace.
   - The page accurately presents the Executive Briefing workspace.
   - The page accurately presents Internet and Local knowledge source separation.
   - The page accurately presents session-scoped knowledge uploads, supported knowledge workflows, and sharing between the two workspaces.
   - The page accurately presents Markdown downloads and on-demand PDF generation.
   - The page accurately presents active-run Stop behavior as cooperative cancellation at safe execution boundaries.
   - Every visible feature claim can be traced to current application behavior or tests.

3. Conversion and navigation
   - The primary call to action clearly opens the working dashboard or configured application URL.
   - The CTA does not imply that public visitors can use a dashboard that is not deployed or reachable.
   - Secondary navigation is limited to relevant actions such as opening the dashboard, viewing the repository, or reading setup information.
   - The landing page does not force users through a marketing funnel, newsletter form, account creation flow, or unrelated links.

4. Content discipline
   - The page contains only information relevant to understanding and trying AI Research.
   - Remove template language, generic crewAI explanations, internal task workflow details, development history, and noisy technical implementation lists from the public page.
   - Do not expose local network addresses, credentials, private knowledge paths, session identifiers, report filesystem paths, or provider traces.
   - Do not claim authentication, multi-user administration, permanent cloud storage, real-time collaboration, arbitrary document support, or forceful process termination unless separately implemented.
   - Copy is concise, scannable, and understandable without reading the README first.

5. Visual and responsive UX
   - Use a clear visual hierarchy with a strong product name, short use-case statement, feature highlights, and a visible primary CTA.
   - Use visual assets or a relevant product-oriented visual treatment that supports the research/executive-workspace subject without adding decorative noise.
   - Avoid dashboard controls, internal status messages, raw configuration values, or dense technical tables on the landing page.
   - The page works at desktop and 390px-wide mobile layouts without horizontal scrolling, clipping, or overlapping content.
   - Typography, contrast, focus states, and interactive controls meet accessible usability expectations.
   - Motion, if used, is restrained and does not obscure content or delay access to the CTA.

6. Deployment and privacy
   - The public landing page can be served independently from the private/local execution dashboard if the dashboard requires Ollama or local session state.
   - Public deployment instructions identify required environment configuration without publishing secrets or private network addresses.
   - The page does not execute research, access knowledge files, load Ollama models, or create reports merely by being viewed.
   - Any analytics, external fonts, images, or third-party assets are either avoided or documented and privacy-reviewed.

7. Validation
   - Browser validation confirms the primary use case, feature claims, CTA, and navigation at desktop and mobile widths.
   - Browser validation confirms the page does not expose private configuration or internal paths.
   - Accessibility checks cover heading hierarchy, keyboard focus, link names, contrast, and mobile overflow.
   - Tests or static checks verify all documented feature claims remain aligned with current implementation.
   - Formatting, linting, and the existing application test suite continue to pass.

## Non-Goals
- This work does not redesign the authenticated or working Streamlit dashboard.
- This work does not create authentication, billing, account management, or public report sharing.
- This work does not add new research, executive, knowledge, export, or cancellation capabilities.
- This work does not publish private reports, session uploads, local knowledge, or Ollama configuration.
- This work does not turn the landing page into a long-form product manual or technical reference.

## Security and privacy notes
- Treat the landing page as publicly readable and keep all copy and assets free of secrets and private paths.
- Do not expose the local Ollama endpoint currently used by development configuration.
- Keep execution endpoints and local session data behind the dashboard boundary.
- Validate any user-controlled or URL-based CTA destination and avoid open redirects.
- Prefer local or repository-owned assets over unreviewed third-party embeds.

### Public exposure assumptions
- The landing page is public and informational.
- This task does not add authentication or claim that the Streamlit dashboard is authenticated.
- The dashboard CTA must point only to a deliberately deployed dashboard URL; it must never expose the development Ollama endpoint or a private local address.
- If the dashboard URL is missing or invalid, show a clear unavailable/setup state instead of silently linking to localhost or a development URL.
- Deployment owners remain responsible for protecting any publicly reachable dashboard and its execution/provider endpoints; that protection is outside this landing-page task.
- Public copy must use `session-scoped` or `temporary` for knowledge handling and must not promise confidential or guaranteed private storage.

## Implementation guidance
- Use `landing/index.html` as the public entry point and keep its assets under `landing/`.
- Store the public dashboard destination in a generated deployment file such as `landing/config.js`, created from `DASHBOARD_URL` during deployment; keep `landing/config.example.js` as the documented template and do not commit deployment-specific URLs or secrets.
- Accept only absolute `http://` or `https://` dashboard URLs from deployment configuration. Show an unavailable CTA state when the value is absent or invalid.
- Define local preview as `python -m http.server 8000 --directory landing` and avoid adding a frontend framework unless the repository gains a demonstrated need for one.
- Preserve the existing Streamlit dashboard entry point and workflow behavior.
- Centralize feature copy so it can be reviewed against the implementation and updated when capabilities change.
- Keep landing-page content separate from operational dashboard state and CrewAI execution code.
- Use the current README and dashboard labels as source material, but rewrite them for public scanning rather than copying technical instructions wholesale.
- Validate the configured CTA as an allowed HTTP(S) destination and avoid open redirects.
- Prefer repository-owned assets and fonts; document any third-party asset or analytics dependency.

## UX review checklist
- First viewport communicates AI Research, the use case, and the primary CTA.
- Feature highlights cover only Research, Executive Briefing, session knowledge, source separation, report exports, and cooperative Stop behavior.
- Public visitors can distinguish the informational landing page from the working dashboard.
- Desktop and 390px mobile screenshots show no clipping or horizontal overflow.
- Keyboard and screen-reader users can reach and understand the primary CTA.
- No private URLs, credentials, filesystem paths, or internal workflow terminology appear.

## UX review
### Recommended information architecture
1. **Hero**: `AI Research`, a one-sentence local-first use-case statement, and one primary `Open dashboard` CTA.
2. **Use cases**: concise Research and Executive Briefing descriptions for users deciding which workflow fits them.
3. **Feature highlights**: Internet/Local source separation, private session knowledge, report downloads, and cooperative Stop behavior.
4. **Trust boundary**: explain that session uploads are temporary and isolated, without implying accounts or permanent cloud storage.
5. **Final CTA**: repeat the dashboard action with a short setup expectation, not a long technical explanation.

### Content rules
- Keep the first viewport focused on product identity, use case, and dashboard entry.
- Use short feature statements with one idea per item; avoid paragraphs copied from the README.
- Do not lead with implementation terms such as CrewAI classes, Python modules, report paths, internal state, or task workflow.
- Avoid unsupported marketing claims such as faster research, guaranteed privacy, team collaboration, enterprise readiness, or model performance.
- The public page should not mention the development Ollama endpoint or local filesystem paths.
- Clearly distinguish `Open dashboard` from any repository/setup link.

### Browser and responsive review
- At desktop width, confirm the hero and primary CTA are visible without scrolling and that the next feature band is hinted below the fold.
- At 390px width, confirm the hero copy, feature items, and CTA wrap naturally without horizontal overflow.
- Verify keyboard focus reaches the primary CTA and any secondary navigation in a logical order.
- Verify headings form a meaningful hierarchy and interactive controls have descriptive accessible names.
- Verify the landing page loads without starting Ollama discovery, reading session knowledge, or creating reports.
- Verify the dashboard CTA points to the configured public dashboard URL and fails clearly when no dashboard URL is configured; do not silently link to a private development address.

## UX review outcome
The recommended architecture is a separate static/public landing entry point that links to the operational Streamlit dashboard. This keeps public marketing content independent from local Ollama discovery and session state, while allowing the landing page to present only verified application capabilities.

## Technical review resolution
- Public landing page: `landing/index.html` with no Python, Streamlit, Ollama, session, or report execution on page load.
- Dashboard destination: deployment-generated `landing/config.js` from `DASHBOARD_URL`, with a visible unavailable state when unset or invalid.
- Exposure model: the landing page is public; dashboard authentication/protection is not introduced by this ticket and must not be implied by copy.
- Feature copy: centralize and review against current dashboard labels and tests.
- Validation: serve `landing/` with `python -m http.server 8000 --directory landing`, run browser checks at desktop and 390px widths, and verify CTA behavior with configured and missing `DASHBOARD_URL` values.

## Ready for engineering
UX and technical review are complete. The preferred architecture is a separate static/public entry point with an explicit configured dashboard CTA, no implicit authentication claim, concise verified feature copy, and desktop/mobile browser validation.
