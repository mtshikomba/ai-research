# Task 020: Customize the Research and Executive workspace names

## Story
As a user, I want to customize the names of the Research and Executive workspaces independently so that each workspace reflects my organization, project, or workflow.

If I do not provide custom names, the dashboard should use generic defaults that remain clear and stable.

## Product requirement
The dashboard must provide separate optional names for the two workspaces:

- Research workspace default: `Research Crew`
- Executive workspace default: `Executive Briefing`

A custom name entered for one workspace must affect only that workspace. The two names must not share a setting, overwrite one another, or alter underlying crew classes, report paths, source behavior, or project identifiers.

## Scope
- Add an optional customization control for the Research workspace name.
- Add an optional customization control for the Executive workspace name.
- Store the two values independently in the current browser session or another approved local user-scoped mechanism.
- Render each configured name wherever its workspace title is displayed.
- Fall back to the correct generic default when a value is missing, blank, or whitespace-only.
- Make both names independently resettable.

## Acceptance Criteria
1. Independent defaults
   - A new session displays `Research Crew` for the Research workspace.
   - A new session displays `Executive Briefing` for the Executive workspace.
   - The two defaults remain independent and are not combined into one shared title.

2. Independent customization
   - The user can set a custom Research workspace name.
   - The user can set a custom Executive workspace name.
   - Changing the Research name does not change the Executive name.
   - Changing the Executive name does not change the Research name.
   - Custom names are applied to the visible workspace headings and relevant page metadata where applicable.

3. Reset and validation
   - Clearing the Research name restores exactly `Research Crew`.
   - Clearing the Executive name restores exactly `Executive Briefing`.
   - Leading and trailing whitespace is ignored before rendering.
   - Whitespace-only, missing, non-string, or otherwise invalid values safely use the relevant default.
   - Names do not crash the dashboard or alter unrelated execution behavior.

4. Session scope and safety
   - Custom names are isolated to the current browser session or approved local user scope.
   - One user's workspace names cannot change another user's session.
   - The setting does not rename Python classes, CrewAI roles, report directories, source labels, or shared project data.
   - Session expiry resets or removes the session-scoped custom names according to the existing session lifecycle policy.

5. UX
   - The two settings are clearly labeled separately, for example `Research workspace name` and `Executive workspace name`.
   - The controls explain that names are optional and blank values restore the generic defaults.
   - The controls are easy to find without mixing the two workspace settings together ambiguously.
   - Switching workspaces preserves both customized names.
   - Names remain readable at desktop and narrow/mobile widths without clipping or horizontal overflow.
   - The default names remain professional and understandable when no customization is configured.

6. Validation
   - Unit tests cover both independent defaults.
   - Tests cover customizing only Research and customizing only Executive briefing.
   - Tests cover customizing both names simultaneously.
   - Tests cover blank, whitespace-only, missing, and invalid-value fallback behavior.
   - AppTest or browser validation confirms the names persist while switching workspaces.
   - Tests confirm session expiry resets the custom names if they are session-scoped.
   - Black, flake8, and the full existing test suite continue to pass.

## Non-Goals
- This work does not rename the project, package, CrewAI classes, agent roles, report directories, or source labels.
- This work does not add account-wide administration or permanent organization branding.
- This work does not change Research or Executive briefing behavior, prompts, data sources, or execution cancellation.
- This work does not add a full branding/theme editor.

## Security and privacy notes
- Treat custom names as display values, not filesystem paths, commands, identifiers, or authorization inputs.
- Escape or safely render custom names through Streamlit's native text APIs.
- Do not log private session settings unnecessarily.
- Keep the two settings in session state rather than module-level mutable state.

## Implementation guidance
- Define separate constants for the two defaults, such as `DEFAULT_RESEARCH_WORKSPACE_NAME` and `DEFAULT_EXECUTIVE_WORKSPACE_NAME`.
- Use separate session-state keys for the two custom values.
- Centralize normalization and fallback logic in a small testable helper that accepts a custom value and a workspace-specific default.
- Keep the underlying workflow identifiers stable while using the configured names only for display and page metadata.
- Reset both settings naturally when the existing session-expiry cleanup clears session state.

## UX review checklist
- Set only the Research name and verify Executive Briefing remains unchanged.
- Set only the Executive name and verify Research Crew remains unchanged.
- Set both names, switch workspaces repeatedly, and verify each title remains correct.
- Clear each setting independently and verify the appropriate generic default returns.
- Validate desktop and 390px-wide mobile layouts for long custom names.

## UX review
### Placement and flow
1. The user opens a `Workspace names` expander in the sidebar.
2. The user sees two clearly separate optional fields: `Research workspace name` and `Executive workspace name`.
3. Each field displays its own default placeholder: `Research Crew` or `Executive Briefing`.
4. The user enters either or both names; each heading updates on the next normal Streamlit rerun.
5. The user clears one field and that workspace alone returns to its generic default.
6. Switching workspaces confirms the two names remain independent.

### Recommended copy and controls
- Expander label: `Workspace names`.
- Research field label: `Research workspace name`.
- Executive field label: `Executive workspace name`.
- Helper text: `Optional. Leave blank to use Research Crew.` and `Optional. Leave blank to use Executive Briefing.`
- Keep the two fields adjacent but visually distinct; do not use one combined input because the names have separate defaults and lifecycles.
- Use visible text fields with stable session-state keys, not URL query parameters or hidden controls.

### Required states
- Default: main headings show `Research Crew` and `Executive Briefing`.
- Research customized only: Research heading changes; Executive remains `Executive Briefing`.
- Executive customized only: Executive heading changes; Research remains `Research Crew`.
- Both customized: each main heading reflects its own value.
- Cleared value: the corresponding default returns immediately after rerun.
- Whitespace-only or invalid value: silently normalize to the corresponding default without showing a blank heading.
- Active run: naming fields are disabled while execution is active so headings do not change mid-run.
- Session expiry: both fields return to their generic defaults with the existing fresh-session behavior.

### Responsive and accessibility criteria
- The sidebar expander and both fields remain usable at desktop and 390px-wide mobile layouts.
- Long names wrap or truncate safely in the main heading without horizontal overflow or overlap.
- Field labels and helper text clearly identify which workspace each value controls.
- Reset behavior must be achievable by clearing the relevant field; no color-only reset indicator is allowed.
- Customized headings remain readable and maintain the existing heading hierarchy.

## UX review outcome
The proposed flow is ready for implementation: two independent session-scoped text fields in a sidebar `Workspace names` expander, with workspace-specific defaults and clear reset copy. Browser validation should cover default, one-sided customization, both customized, independent reset, workspace switching, session expiry, and 390px-wide rendering.

## UX review results
- Browser review confirmed the default Research heading renders as `Research Crew`.
- Browser review confirmed the collapsed sidebar exposes a `Workspace names` expander.
- The implementation passed the AppTest coverage for independent custom values and workspace switching.
- Full regression validation passed with 57 tests, plus Black, flake8, and `git diff --check`.
- Live browser entry/reset testing of both fields remains to be completed because the shared Streamlit tab was carrying stale active-run state and the sidebar interaction was not reliably actionable during this review.

## Ready for engineering
UX review is substantially complete. The approved defaults are `Research Crew` and `Executive Briefing`, and the two workspace names are independently customizable and independently resettable through the reviewed sidebar flow. Final browser verification should still exercise direct field entry and reset in a fresh Streamlit session.
