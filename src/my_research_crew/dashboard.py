"""Streamlit dashboard for running the configured CrewAI crew through Ollama.

The dashboard keeps Streamlit rendering separate from crew execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

import streamlit as st

from my_research_crew.dashboard_service import (
    DEFAULT_OLLAMA_MODEL,
    OllamaModelInventoryError,
    OllamaSettings,
    get_ollama_settings,
    get_safe_error_message,
    list_ollama_models,
    purge_session_knowledge,
    run_crew,
    run_executive_crew,
    save_session_knowledge,
    select_ollama_model,
    session_knowledge_dir,
    session_has_expired,
)
from my_research_crew.research_sources import (
    ResearchSource,
    inspect_local_knowledge,
)
from my_research_crew.report_exports import (
    markdown_download,
    pdf_download,
    report_download_filename,
)
from my_research_crew.execution_service import (
    RunState,
    request_cancellation,
    snapshot_run,
    start_run,
)

DEFAULT_RESEARCH_WORKSPACE_NAME = "Research Crew"
DEFAULT_EXECUTIVE_WORKSPACE_NAME = "Executive Briefing"


def workspace_name(custom_name: object, default_name: str) -> str:
    """Normalize one session workspace name with its independent fallback."""
    if not isinstance(custom_name, str):
        return default_name
    normalized_name = custom_name.strip()
    return normalized_name or default_name


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


def _render_session_knowledge(knowledge_dir: Path) -> Any:
    """Render the shared session knowledge uploader and return its readiness."""
    uploaded_files = st.file_uploader(
        "Session knowledge",
        type=["txt", "md", "csv", "json", "yaml", "yml", "zip"],
        accept_multiple_files=True,
        disabled=st.session_state.run_in_progress,
        help=(
            "Upload TXT, MD, CSV, JSON, YAML, or YML files up to 2MB, or a ZIP "
            "folder up to 50MB. Session knowledge is shared between Research and "
            "Executive briefing for this session and is deleted when the session "
            "expires."
        ),
        key="session-knowledge-upload",
    )
    if uploaded_files:
        upload_result = save_session_knowledge(
            st.session_state.session_id,
            uploaded_files,
        )
        if upload_result.accepted_files:
            st.success(
                f"Added {upload_result.accepted_files} session knowledge file(s)."
            )
        if upload_result.rejected_files:
            st.warning(
                "Rejected upload(s): "
                + ", ".join(upload_result.rejected_files)
                + ". Use supported text formats or a safe ZIP folder."
            )

    local_status = inspect_local_knowledge(knowledge_dir)
    st.info(
        "Session knowledge is shared across Research and Executive briefing and "
        "private to this session."
    )
    available_files = (
        sorted(
            path.relative_to(knowledge_dir).as_posix()
            for path in knowledge_dir.rglob("*")
            if path.is_file() and ".extracted" not in path.parts
        )
        if knowledge_dir.is_dir()
        else []
    )
    if available_files:
        st.caption("Available in this session: " + ", ".join(available_files))
    if local_status.is_ready:
        st.success(
            f"Session knowledge is ready: {local_status.usable_file_count} "
            "usable file(s). This run will stay local and will not access the "
            "internet."
        )
    else:
        st.warning("Upload supported session knowledge before running locally.")
    return local_status


def _render_report_downloads(report_path: Path) -> None:
    """Render Markdown download and on-demand PDF generation for a report."""
    try:
        markdown_bytes = markdown_download(report_path)
        markdown_filename = report_download_filename(report_path, ".md")
        pdf_filename = report_download_filename(report_path, ".pdf")
    except ValueError as error:
        st.error(str(error))
        return

    markdown_column, pdf_column = st.columns(2)
    with markdown_column:
        st.download_button(
            "Download Markdown",
            data=markdown_bytes,
            file_name=markdown_filename,
            mime="text/markdown",
            icon=":material/download:",
            width="stretch",
        )

    pdf_state_key = f"pdf-download:{report_path}"
    with pdf_column:
        if st.button(
            "Generate PDF",
            key=f"generate-pdf:{report_path}",
            icon=":material/picture_as_pdf:",
            width="stretch",
        ):
            try:
                st.session_state[pdf_state_key] = pdf_download(report_path)
            except ValueError as error:
                st.session_state.pop(pdf_state_key, None)
                st.error(str(error))
            except Exception:
                st.session_state.pop(pdf_state_key, None)
                st.error("The PDF could not be generated. Markdown remains available.")

        pdf_bytes = st.session_state.get(pdf_state_key)
        if pdf_bytes:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                icon=":material/download:",
                width="stretch",
                key=f"download-pdf:{report_path}",
            )


def _render_research_result(run_result: Any, model: str | None) -> None:
    """Render a completed Research result retained in session state."""
    with st.container(border=True):
        st.subheader(":material/description: Research report")
        _display_result(run_result.output)
        _render_report_downloads(run_result.report_path)
        st.divider()
        st.caption(f"Model: {model}")
        st.caption(f"Research source: {run_result.source}")
        st.caption(f"Saved report: {run_result.report_path}")


def _render_executive_result(run_result: Any, model: str | None) -> None:
    """Render a completed Executive briefing result retained in session state."""
    with st.container(border=True):
        st.subheader(":material/account_balance: CEO executive brief")
        _display_result(run_result.output)
        _render_report_downloads(run_result.report_path)
        st.divider()
        st.caption(f"Model: {model}")
        st.caption(f"Research source: {run_result.source}")
        st.caption(f"Saved report: {run_result.report_path}")


def _render_workspace_name_settings() -> tuple[str, str]:
    """Render independent workspace-name settings and return display names."""
    st.session_state.setdefault("research-workspace-name", "")
    st.session_state.setdefault("executive-workspace-name", "")
    with st.sidebar.expander("Workspace names"):
        st.text_input(
            "Research workspace name",
            key="research-workspace-name",
            placeholder=DEFAULT_RESEARCH_WORKSPACE_NAME,
            help="Optional. Leave blank to use Research Crew.",
            disabled=bool(st.session_state.get("active_run")),
        )
        st.text_input(
            "Executive workspace name",
            key="executive-workspace-name",
            placeholder=DEFAULT_EXECUTIVE_WORKSPACE_NAME,
            help="Optional. Leave blank to use Executive Briefing.",
            disabled=bool(st.session_state.get("active_run")),
        )
    return (
        workspace_name(
            st.session_state.get("research-workspace-name"),
            DEFAULT_RESEARCH_WORKSPACE_NAME,
        ),
        workspace_name(
            st.session_state.get("executive-workspace-name"),
            DEFAULT_EXECUTIVE_WORKSPACE_NAME,
        ),
    )


@st.fragment(run_every=1)
def _render_active_run() -> None:
    """Poll and render the current background run with a responsive Stop action."""
    handle = st.session_state.get("active_run")
    if handle is None:
        return
    snapshot = snapshot_run(handle)
    if snapshot.state is RunState.RUNNING:
        st.warning(f"Running {st.session_state.active_run_kind}...")
        if st.button("Stop", key="stop-active-run", type="secondary"):
            request_cancellation(handle)
            st.rerun()
        return
    if snapshot.state is RunState.CANCELLATION_REQUESTED:
        st.warning(
            "Stopping... waiting for the active operation to reach a safe boundary."
        )
        return

    st.session_state.pop("active_run", None)
    if snapshot.state is RunState.CANCELLED:
        st.info("Run stopped. No completed result was created.")
    elif snapshot.state is RunState.FAILED:
        st.error(get_safe_error_message(snapshot.error or Exception("run failed")))
    elif snapshot.state is RunState.COMPLETED:
        result_key = (
            "last_research_result"
            if st.session_state.active_run_kind == "research"
            else "last_executive_result"
        )
        model_key = (
            "last_research_model"
            if st.session_state.active_run_kind == "research"
            else "last_executive_model"
        )
        st.session_state[result_key] = snapshot.result
        st.session_state[model_key] = st.session_state.get("active_run_model")
    st.session_state.pop("active_run_kind", None)
    st.session_state.pop("active_run_model", None)
    st.rerun()


def _start_research_run(
    topic: str,
    model: str | None,
    source: ResearchSource,
    knowledge_dir: Path,
) -> None:
    """Start Research in the session-owned background executor."""
    st.session_state["active_run_kind"] = "research"
    st.session_state["active_run_model"] = model
    st.session_state["active_run"] = start_run(
        lambda cancellation_requested: run_crew(
            topic,
            model or "",
            source,
            knowledge_dir=knowledge_dir,
            cancellation_requested=cancellation_requested,
        )
    )


def _start_executive_run(
    question: str,
    context: str,
    model: str | None,
    source: ResearchSource,
    knowledge_dir: Path,
) -> None:
    """Start Executive briefing in the session-owned background executor."""
    st.session_state["active_run_kind"] = "executive briefing"
    st.session_state["active_run_model"] = model
    st.session_state["active_run"] = start_run(
        lambda cancellation_requested: run_executive_crew(
            question,
            context,
            model or "",
            source,
            knowledge_dir=knowledge_dir,
            cancellation_requested=cancellation_requested,
        )
    )


def _render_research_workspace(
    available_models: list[str],
    selected_default: str,
    knowledge_dir: Path,
    workspace_name_value: str,
) -> None:
    """Render the existing research workflow."""
    if st.session_state.get("active_run"):
        _render_active_run()
        return
    st.title(workspace_name_value)
    st.caption("A focused research workspace for your local Ollama models")
    _render_model_summary(available_models, "Local research workflow")

    with st.container(border=True):
        st.subheader(":material/tune: Research setup")
        st.caption("Choose a model and topic, then let the crew prepare a report.")
        source_label = st.segmented_control(
            "Research source",
            [ResearchSource.INTERNET.label, ResearchSource.LOCAL.label],
            default=ResearchSource.INTERNET.label,
            key="research-source",
            disabled=st.session_state.run_in_progress,
            selection_mode="single",
        )
        source = ResearchSource.parse(source_label or ResearchSource.INTERNET.label)
        if source is ResearchSource.LOCAL:
            local_status = _render_session_knowledge(knowledge_dir)
        else:
            local_status = inspect_local_knowledge(knowledge_dir)
            st.caption(
                "Uses public internet sources and does not read local "
                "knowledge files."
            )

        with st.form("research-run-form", clear_on_submit=False):
            model = _model_selector(available_models, selected_default, "research")
            topic = st.text_input(
                "Research topic",
                placeholder="e.g. practical uses of local LLMs",
                disabled=st.session_state.run_in_progress or not available_models,
            )
            submitted = st.form_submit_button(
                "Run research",
                disabled=(
                    st.session_state.run_in_progress
                    or not available_models
                    or (source is ResearchSource.LOCAL and not local_status.is_ready)
                ),
                type="primary",
            )

    if submitted:
        if not topic.strip():
            st.warning("Enter a topic before starting the crew.")
        else:
            st.session_state.pop("last_research_result", None)
            _start_research_run(topic, model, source, knowledge_dir)
            st.rerun()
    if st.session_state.get("last_research_result"):
        _render_research_result(
            st.session_state["last_research_result"],
            st.session_state.get("last_research_model"),
        )


def _render_executive_workspace(
    available_models: list[str],
    selected_default: str,
    knowledge_dir: Path,
    workspace_name_value: str,
) -> None:
    """Render the Peshiko Investments Group executive briefing workflow."""
    if st.session_state.get("active_run"):
        _render_active_run()
        return
    st.title(workspace_name_value)
    st.caption("Executive briefing workspace")
    _render_model_summary(available_models, "CEO-led executive assessment")

    with st.container(border=True):
        st.subheader(":material/account_balance: Executive briefing")
        st.caption("Prepare CFO, COO, and CIO assessments for CEO synthesis.")
        source_label = st.segmented_control(
            "Research source",
            [ResearchSource.INTERNET.label, ResearchSource.LOCAL.label],
            default=ResearchSource.LOCAL.label,
            key="executive-research-source",
            disabled=st.session_state.run_in_progress,
            selection_mode="single",
        )
        source = ResearchSource.parse(source_label or ResearchSource.LOCAL.label)
        if source is ResearchSource.LOCAL:
            local_status = _render_session_knowledge(knowledge_dir)
        else:
            local_status = inspect_local_knowledge(knowledge_dir)
            st.caption(
                "Uses public internet sources and does not read local Peshiko "
                "knowledge files."
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
                disabled=(
                    st.session_state.run_in_progress
                    or not available_models
                    or (source is ResearchSource.LOCAL and not local_status.is_ready)
                ),
                type="primary",
            )

    if submitted:
        if not question.strip():
            st.warning("Enter an executive question before starting the briefing.")
        else:
            st.session_state.pop("last_executive_result", None)
            _start_executive_run(question, context, model, source, knowledge_dir)
            st.rerun()
    if st.session_state.get("last_executive_result"):
        _render_executive_result(
            st.session_state["last_executive_result"],
            st.session_state.get("last_executive_model"),
        )


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


def _run_research(
    topic: str,
    model: str | None,
    source: ResearchSource,
    knowledge_dir: Path,
) -> None:
    """Execute and render a research run."""
    st.session_state.run_in_progress = True
    try:
        with st.spinner(f"Running {source.label} research with {model}..."):
            run_result = run_crew(
                topic,
                model or "",
                source,
                knowledge_dir=knowledge_dir,
            )
    except ValueError as error:
        st.warning(str(error))
    except Exception as error:
        st.error(get_safe_error_message(error))
    else:
        st.session_state["last_research_result"] = run_result
        st.session_state["last_research_model"] = model
    finally:
        st.session_state.run_in_progress = False


def _run_executive_brief(
    question: str,
    context: str,
    model: str | None,
    source: ResearchSource,
    knowledge_dir: Path,
) -> None:
    """Execute and render a Peshiko CEO-led executive briefing."""
    st.session_state.run_in_progress = True
    try:
        with st.spinner(
            f"Preparing CFO, COO, and CIO assessments with {model} for CEO synthesis..."
        ):
            run_result = run_executive_crew(
                question,
                context,
                model or "",
                source,
                knowledge_dir=knowledge_dir,
            )
    except ValueError as error:
        st.warning(str(error))
    except Exception as error:
        st.error(get_safe_error_message(error))
    else:
        st.session_state["last_executive_result"] = run_result
        st.session_state["last_executive_model"] = model
    finally:
        st.session_state.run_in_progress = False


def main() -> None:
    """Render research and Peshiko executive workspaces."""
    st.set_page_config(page_title="Research Crew", page_icon="M", layout="wide")
    settings = get_ollama_settings()
    st.session_state.setdefault("run_in_progress", False)
    st.session_state.setdefault("session_id", f"session-{uuid.uuid4().hex[:12]}")
    st.session_state.setdefault(
        "session_started_at",
        datetime.now(timezone.utc).isoformat(),
    )

    if session_has_expired(st.session_state.get("session_started_at")):
        session_id = st.session_state.get("session_id") or "default-session"
        purge_session_knowledge(session_id)
        st.session_state.clear()
        st.session_state["run_in_progress"] = False
        st.session_state["session_id"] = f"session-{uuid.uuid4().hex[:12]}"
        st.session_state["session_started_at"] = datetime.now(timezone.utc).isoformat()
        st.warning("Your 10-minute session expired. A fresh session has started.")

    knowledge_dir = session_knowledge_dir(st.session_state.session_id)

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
            st.caption("Ready")

    research_name, executive_name = _render_workspace_name_settings()

    workspace = st.segmented_control(
        "Workspace",
        ["Research", "Executive briefing"],
        default="Research",
        key="workspace",
        disabled=(
            st.session_state.run_in_progress
            or st.session_state.get("active_run") is not None
        ),
        required=True,
    )
    if available_models and selected_default != DEFAULT_OLLAMA_MODEL:
        st.info(f"Using available model: {selected_default}")

    if workspace == "Executive briefing":
        st.set_page_config(page_title=executive_name)
        _render_executive_workspace(
            available_models, selected_default, knowledge_dir, executive_name
        )
    else:
        st.set_page_config(page_title=research_name)
        _render_research_workspace(
            available_models, selected_default, knowledge_dir, research_name
        )


if __name__ == "__main__":
    main()
