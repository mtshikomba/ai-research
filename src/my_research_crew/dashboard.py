"""Streamlit dashboard for running the configured CrewAI crew through Ollama.

The dashboard keeps Streamlit rendering separate from crew execution.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from my_research_crew.dashboard_service import (
    DEFAULT_OLLAMA_MODEL,
    OllamaModelInventoryError,
    OllamaSettings,
    get_ollama_settings,
    get_safe_error_message,
    list_ollama_models,
    run_crew,
    run_executive_crew,
    select_ollama_model,
)


def _display_result(result: Any) -> None:
    """Render CrewAI output without exposing internal execution details.

    Args:
        result: Value returned by the CrewAI kickoff.
    """
    output = getattr(result, "raw", result)
    st.markdown(str(output))


@st.cache_data(ttl=30, show_spinner="Loading available Ollama models...")
def _load_models(api_base: str) -> list[str]:
    """Load available models with a short cache for dashboard reruns."""
    return list_ollama_models(OllamaSettings(model="", api_base=api_base))


def _render_research_workspace(
    available_models: list[str], selected_default: str
) -> None:
    """Render the existing research workflow."""
    st.title("My Research Crew")
    st.caption("A focused research workspace for your local Ollama models")
    _render_model_summary(available_models, "Local research workflow")

    with st.container(border=True):
        st.subheader(":material/tune: Research setup")
        st.caption("Choose a model and topic, then let the crew prepare a report.")
        with st.form("research-run-form", clear_on_submit=False):
            model = _model_selector(available_models, selected_default, "research")
            topic = st.text_input(
                "Research topic",
                placeholder="e.g. practical uses of local LLMs",
                disabled=st.session_state.run_in_progress or not available_models,
            )
            submitted = st.form_submit_button(
                "Run research",
                disabled=st.session_state.run_in_progress or not available_models,
                type="primary",
            )

    if submitted:
        _run_research(topic, model)


def _render_executive_workspace(
    available_models: list[str], selected_default: str
) -> None:
    """Render the Peshiko Investments Group executive briefing workflow."""
    st.title("Peshiko Investments Group")
    st.caption("Executive briefing workspace")
    _render_model_summary(available_models, "CEO-led executive assessment")

    with st.container(border=True):
        st.subheader(":material/account_balance: Executive briefing")
        st.caption("Prepare CFO, COO, and CIO assessments for CEO synthesis.")
        st.info(
            "Source order: local Peshiko knowledge first. Extract any zipped business or historical archives in knowledge/peshiko before using internet research as a fallback."
        )
        with st.form("executive-run-form", clear_on_submit=False):
            model = _model_selector(available_models, selected_default, "executive")
            question = st.text_area(
                "Executive question",
                placeholder=(
                    "e.g. What are the risks and next steps for this investment "
                    "decision?"
                ),
                disabled=st.session_state.run_in_progress or not available_models,
            )
            context = st.text_area(
                "Business context (optional)",
                placeholder=(
                    "Reporting period, relevant figures, constraints, or "
                    "assumptions. Do not include credentials."
                ),
                disabled=st.session_state.run_in_progress or not available_models,
            )
            submitted = st.form_submit_button(
                "Prepare executive brief",
                disabled=st.session_state.run_in_progress or not available_models,
                type="primary",
            )

    if submitted:
        _run_executive_brief(question, context, model)


def _render_model_summary(available_models: list[str], workflow_name: str) -> None:
    """Render shared workflow context for a dashboard workspace."""
    if not available_models:
        return
    summary_left, summary_right = st.columns((2, 1))
    with summary_left:
        st.caption(f":material/hub: {workflow_name}")
    with summary_right:
        st.metric("Models online", len(available_models))


def _model_selector(
    available_models: list[str], selected_default: str, workspace: str
) -> str | None:
    """Render a stable, labeled model selector for one workspace."""
    return st.selectbox(
        "Model",
        available_models,
        index=available_models.index(selected_default) if available_models else None,
        key=f"{workspace}-model",
        disabled=st.session_state.run_in_progress or not available_models,
    )


def _run_research(topic: str, model: str | None) -> None:
    """Execute and render a research run."""
    st.session_state.run_in_progress = True
    try:
        with st.spinner(f"Running the research workflow with {model}..."):
            run_result = run_crew(topic, model or "")
    except ValueError as error:
        st.warning(str(error))
    except Exception as error:
        st.error(get_safe_error_message(error))
    else:
        with st.container(border=True):
            st.subheader(":material/description: Research report")
            _display_result(run_result.output)
            st.divider()
            st.caption(f"Model: {model}")
            st.caption(f"Saved report: {run_result.report_path}")
    finally:
        st.session_state.run_in_progress = False


def _run_executive_brief(question: str, context: str, model: str | None) -> None:
    """Execute and render a Peshiko CEO-led executive briefing."""
    st.session_state.run_in_progress = True
    try:
        with st.spinner(
            f"Preparing CFO, COO, and CIO assessments with {model} for CEO synthesis..."
        ):
            run_result = run_executive_crew(question, context, model or "")
    except ValueError as error:
        st.warning(str(error))
    except Exception as error:
        st.error(get_safe_error_message(error))
    else:
        with st.container(border=True):
            st.subheader(":material/account_balance: CEO executive brief")
            _display_result(run_result.output)
            st.divider()
            st.caption(f"Model: {model}")
            st.caption(f"Saved report: {run_result.report_path}")
    finally:
        st.session_state.run_in_progress = False


def main() -> None:
    """Render research and Peshiko executive workspaces."""
    st.set_page_config(page_title="My Research Crew", page_icon="M", layout="wide")
    settings = get_ollama_settings()
    st.session_state.setdefault("run_in_progress", False)

    try:
        available_models = _load_models(settings.api_base)
        selected_default = select_ollama_model(available_models, settings.model)
    except OllamaModelInventoryError:
        available_models = []
        selected_default = ""
        st.error("Could not load Ollama models. Confirm the server is reachable.")

    with st.sidebar:
        st.subheader(":material/dns: Local Ollama")
        st.caption(settings.api_base)
        if st.session_state.run_in_progress:
            st.warning("Run in progress")
        elif available_models:
            st.success("Ready")

    workspace = st.segmented_control(
        "Workspace",
        ["Research", "Executive briefing"],
        default="Research",
        key="workspace",
        disabled=st.session_state.run_in_progress,
        required=True,
    )
    if available_models and selected_default != DEFAULT_OLLAMA_MODEL:
        st.info(f"Using available model: {selected_default}")

    if workspace == "Executive briefing":
        _render_executive_workspace(available_models, selected_default)
    else:
        _render_research_workspace(available_models, selected_default)


if __name__ == "__main__":
    main()
