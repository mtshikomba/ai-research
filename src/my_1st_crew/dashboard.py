"""Streamlit dashboard for running the configured CrewAI crew through Ollama.

The dashboard keeps Streamlit rendering separate from crew execution.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from my_1st_crew.dashboard_service import (
    get_ollama_settings,
    get_safe_error_message,
    run_crew,
)


def _display_result(result: Any) -> None:
    """Render CrewAI output without exposing internal execution details.

    Args:
        result: Value returned by the CrewAI kickoff.
    """
    output = getattr(result, "raw", result)
    st.markdown(str(output))


def main() -> None:
    """Render and run the Streamlit CrewAI dashboard."""
    st.set_page_config(page_title="My1StCrew", page_icon="M", layout="wide")
    settings = get_ollama_settings()

    if "run_in_progress" not in st.session_state:
        st.session_state.run_in_progress = False

    st.title("My1StCrew")
    st.caption("CrewAI research dashboard powered by your local Ollama server")

    with st.sidebar:
        st.subheader("Local model")
        st.code(settings.model, language=None)
        st.caption(settings.api_base)

    with st.form("crew-run-form", clear_on_submit=False):
        topic = st.text_input(
            "Research topic",
            placeholder="e.g. practical uses of local LLMs",
            disabled=st.session_state.run_in_progress,
        )
        submitted = st.form_submit_button(
            "Run crew",
            disabled=st.session_state.run_in_progress,
            type="primary",
        )

    if not submitted:
        return

    st.session_state.run_in_progress = True
    try:
        with st.spinner("Running the CrewAI workflow..."):
            result = run_crew(topic)
    except ValueError as error:
        st.warning(str(error))
    except Exception as error:
        st.error(get_safe_error_message(error))
    else:
        st.subheader("Crew result")
        _display_result(result)
    finally:
        st.session_state.run_in_progress = False


if __name__ == "__main__":
    main()
