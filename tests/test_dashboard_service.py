"""Focused tests for dashboard configuration and CrewAI execution."""

import os
import unittest
from unittest.mock import MagicMock, patch

from my_1st_crew.dashboard_service import (
    DEFAULT_OLLAMA_API_BASE,
    DEFAULT_OLLAMA_MODEL,
    get_safe_error_message,
    get_ollama_settings,
    run_crew,
)


class DashboardServiceTests(unittest.TestCase):
    """Verify dashboard settings and CrewAI execution delegation."""

    def test_get_ollama_settings_uses_defaults(self) -> None:
        """The dashboard falls back to the approved local Ollama settings."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("my_1st_crew.dashboard_service.load_dotenv"),
        ):
            settings = get_ollama_settings()

        self.assertEqual(settings.model, DEFAULT_OLLAMA_MODEL)
        self.assertEqual(settings.api_base, DEFAULT_OLLAMA_API_BASE)

    def test_run_crew_sets_ollama_settings_and_passes_inputs(self) -> None:
        """The runner configures Ollama and delegates to the existing crew."""
        kickoff = MagicMock(return_value="crew output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with (
            patch.dict(
                os.environ,
                {
                    "MODEL": "ollama/test-model",
                    "API_BASE": "http://ollama.test:11434",
                },
                clear=True,
            ),
            patch("my_1st_crew.dashboard_service._create_crew", return_value=crew),
        ):
            result = run_crew("  local AI  ")

        self.assertEqual(result, "crew output")
        kickoff.assert_called_once()
        inputs = kickoff.call_args.kwargs["inputs"]
        self.assertEqual(inputs["topic"], "local AI")
        self.assertTrue(inputs["current_year"].isdigit())

    def test_run_crew_rejects_an_empty_topic(self) -> None:
        """The runner rejects invalid dashboard input before starting CrewAI."""
        with self.assertRaisesRegex(ValueError, "Enter a topic"):
            run_crew("   ")

    def test_safe_error_message_hides_provider_details(self) -> None:
        """Provider exceptions become actionable messages without raw details."""
        message = get_safe_error_message(Exception("Connection refused: secret-value"))

        self.assertIn("Could not reach Ollama", message)
        self.assertNotIn("secret-value", message)

    def test_safe_error_message_explains_a_missing_model(self) -> None:
        """Unavailable models produce a safe, actionable message."""
        message = get_safe_error_message(Exception("Model not found: private-model"))

        self.assertIn("model is unavailable", message)
        self.assertNotIn("private-model", message)
