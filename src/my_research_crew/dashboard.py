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


def main() -> None:
    """Render and run the Streamlit CrewAI dashboard."""
    st.set_page_config(page_title="My Research Crew", page_icon="M", layout="wide")
    settings = get_ollama_settings()

    if "run_in_progress" not in st.session_state:
        st.session_state.run_in_progress = False

    st.title("My Research Crew")
    st.caption("A focused research workspace for your local Ollama models")

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
            st.warning("Research run in progress")
        elif available_models:
            st.success("Ready to research")

    if available_models:
        summary_left, summary_right = st.columns((2, 1))
        with summary_left:
            st.caption(":material/hub: Local research workflow")
        with summary_right:
            st.metric("Models online", len(available_models))

    if available_models and selected_default != DEFAULT_OLLAMA_MODEL:
        st.info(f"Using available model: {selected_default}")

    with st.container(border=True):
        st.subheader(":material/tune: Research setup")
        st.caption("Choose a model and topic, then let the crew prepare a report.")
        with st.form("crew-run-form", clear_on_submit=False):
            model = st.selectbox(
                "Model",
                available_models,
                index=(
                    available_models.index(selected_default)
                    if available_models
                    else None
                ),
                disabled=st.session_state.run_in_progress or not available_models,
            )
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

    if not submitted:
        return

    st.session_state.run_in_progress = True
    try:
        with st.spinner(f"Running the CrewAI workflow with {model}..."):
            run_result = run_crew(topic, model)
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


if __name__ == "__main__":
    main()
