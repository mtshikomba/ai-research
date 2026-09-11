"""Configuration and execution boundary for the Streamlit dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any

from dotenv import load_dotenv

DEFAULT_OLLAMA_MODEL = "ollama/llama3.1:latest"
DEFAULT_OLLAMA_API_BASE = "http://192.168.1.153:11434"


@dataclass(frozen=True)
class OllamaSettings:
    """Settings used by CrewAI to connect to an Ollama server.

    Attributes:
        model: LiteLLM-compatible Ollama model identifier.
        api_base: Base URL for the Ollama server.
    """

    model: str
    api_base: str


def get_ollama_settings() -> OllamaSettings:
    """Load Ollama settings from the environment with local-network defaults.

    Returns:
        The configured model and Ollama API base URL.
    """
    load_dotenv()
    return OllamaSettings(
        model=os.getenv("MODEL", DEFAULT_OLLAMA_MODEL),
        api_base=os.getenv("API_BASE", DEFAULT_OLLAMA_API_BASE),
    )


def _create_crew() -> Any:
    """Create the existing configured CrewAI crew on demand.

    Returns:
        The configured CrewAI crew instance.
    """
    from my_1st_crew.crew import My1StCrew

    return My1StCrew().crew()


def get_safe_error_message(error: Exception) -> str:
    """Convert a provider failure into a safe, actionable dashboard message.

    Args:
        error: Exception raised while starting or running the crew.

    Returns:
        A message that guides the user without exposing provider details.
    """
    error_text = str(error).lower()
    if any(
        term in error_text for term in ("connection", "connect", "refused", "timeout")
    ):
        return (
            "Could not reach Ollama. Confirm the configured server is running "
            "and reachable."
        )
    if any(term in error_text for term in ("model", "not found", "404")):
        return (
            "The configured Ollama model is unavailable. Pull the model, then "
            "try again."
        )
    return (
        "The crew could not complete this run. Check the local Ollama "
        "configuration and try again."
    )


def run_crew(topic: str) -> Any:
    """Run the configured CrewAI crew for a dashboard topic.

    Args:
        topic: Research topic supplied by the dashboard user.

    Returns:
        The output returned by the CrewAI kickoff.

    Raises:
        ValueError: If the supplied topic is empty.
        Exception: If CrewAI or the configured Ollama service cannot complete
            the run.
    """
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("Enter a topic before starting the crew.")

    settings = get_ollama_settings()
    os.environ["MODEL"] = settings.model
    os.environ["API_BASE"] = settings.api_base

    return _create_crew().kickoff(
        inputs={
            "topic": normalized_topic,
            "current_year": str(datetime.now().year),
        }
    )
