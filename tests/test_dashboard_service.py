"""Focused tests for dashboard configuration and CrewAI execution."""

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from my_research_crew.dashboard_service import (
    DEFAULT_OLLAMA_API_BASE,
    DEFAULT_OLLAMA_MODEL,
    CrewRunResult,
    ExecutiveRunResult,
    OllamaSettings,
    get_safe_error_message,
    get_ollama_settings,
    list_ollama_models,
    run_crew,
    run_executive_crew,
    select_ollama_model,
)
from my_research_crew.peshiko_crew import PeshikoInvestmentsCrew
from my_research_crew.report_storage import (
    PROJECT_ROOT,
    create_report_path,
    report_output_file,
)
from my_research_crew.crew import MyResearchCrew
from my_research_crew.research_sources import LocalKnowledgeError, ResearchSource


class DashboardServiceTests(unittest.TestCase):
    """Verify dashboard settings and CrewAI execution delegation."""

    def test_get_ollama_settings_uses_defaults(self) -> None:
        """The dashboard falls back to the approved local Ollama settings."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("my_research_crew.dashboard_service.load_dotenv"),
        ):
            settings = get_ollama_settings()

        self.assertEqual(settings.model, DEFAULT_OLLAMA_MODEL)
        self.assertEqual(settings.api_base, DEFAULT_OLLAMA_API_BASE)

    def test_run_crew_sets_ollama_settings_and_passes_inputs(self) -> None:
        """The runner configures Ollama and delegates to the existing crew."""
        kickoff = MagicMock(return_value="crew output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch.dict(
                    os.environ,
                    {
                        "MODEL": "ollama/test-model",
                        "API_BASE": "http://ollama.test:11434",
                    },
                    clear=True,
                ),
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service._create_crew",
                    return_value=crew,
                ) as create_crew,
            ):
                result = run_crew(
                    "  local AI  ",
                    "gpt-oss:120b-cloud",
                    ResearchSource.INTERNET,
                )

        self.assertEqual(
            result,
            CrewRunResult("crew output", report_path, ResearchSource.INTERNET.label),
        )
        create_crew.assert_called_once_with(
            report_path,
            "gpt-oss:120b-cloud",
            ResearchSource.INTERNET,
            "Internet research enabled. Local knowledge files were not read.",
        )
        kickoff.assert_called_once()
        inputs = kickoff.call_args.kwargs["inputs"]
        self.assertEqual(inputs["topic"], "local AI")
        self.assertEqual(inputs["research_source"], "Internet")
        self.assertTrue(inputs["current_year"].isdigit())

    def test_run_crew_prepares_local_knowledge_without_internet_fallback(self) -> None:
        """Local mode passes local context and never constructs internet mode."""
        crew = MagicMock()
        crew.kickoff.return_value = "local output"

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service.prepare_local_knowledge"
                ) as prepare,
                patch(
                    "my_research_crew.dashboard_service._create_crew",
                    return_value=crew,
                ) as create_crew,
            ):
                prepare.return_value.context = "Private local evidence"
                result = run_crew(
                    "quarterly performance",
                    "gpt-oss:120b-cloud",
                    ResearchSource.LOCAL,
                )

        self.assertEqual(result.source, "Local knowledge")
        create_crew.assert_called_once_with(
            report_path,
            "gpt-oss:120b-cloud",
            ResearchSource.LOCAL,
            "Private local evidence",
        )

    def test_run_crew_does_not_fallback_when_local_knowledge_is_empty(self) -> None:
        """A local preparation failure stops execution before crew creation."""
        with (
            patch(
                "my_research_crew.dashboard_service.prepare_local_knowledge",
                side_effect=LocalKnowledgeError("No usable local knowledge files."),
            ),
            patch("my_research_crew.dashboard_service._create_crew") as create_crew,
        ):
            with self.assertRaisesRegex(LocalKnowledgeError, "No usable"):
                run_crew("topic", "model", ResearchSource.LOCAL)

        create_crew.assert_not_called()

    def test_run_crew_does_not_mutate_environment_model_settings(self) -> None:
        """A dashboard selection stays scoped to its run rather than `.env`."""
        crew = MagicMock()
        crew.kickoff.return_value = "crew output"

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch.dict(
                    os.environ,
                    {"MODEL": "llama3.1:latest", "API_BASE": "http://ollama.test"},
                    clear=True,
                ),
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service._create_crew",
                    return_value=crew,
                ),
            ):
                run_crew("local AI", "gpt-oss:120b-cloud")
                self.assertEqual(os.environ["MODEL"], "llama3.1:latest")
                self.assertEqual(os.environ["API_BASE"], "http://ollama.test")

    def test_run_executive_crew_passes_context_and_model(self) -> None:
        """The executive runner delegates the selected model and safe context."""
        kickoff = MagicMock(return_value="executive output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            with (
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.peshiko_crew.PeshikoInvestmentsCrew",
                ) as executive_crew,
            ):
                executive_crew.return_value.crew.return_value = crew
                result = run_executive_crew(
                    "Should we expand?",
                    "Cash reserves are constrained.",
                    "llama3.1:latest",
                )

        self.assertEqual(result, ExecutiveRunResult("executive output", report_path))
        executive_crew.assert_called_once_with(
            report_path=report_path, model="llama3.1:latest"
        )
        self.assertEqual(
            kickoff.call_args.kwargs["inputs"]["executive_question"],
            "Should we expand?",
        )

    def test_peshiko_crew_has_ceo_context_for_specialist_tasks(self) -> None:
        """The CEO brief consumes the CFO, COO, and CIO task assessments."""
        crew = PeshikoInvestmentsCrew(model="llama3.1:latest")
        brief = crew.ceo_brief()

        self.assertEqual(len(brief.context), 3)
        self.assertEqual(
            brief.agent.role.strip(),
            "Peshiko Investments Group Chief Executive Officer",
        )

    def test_peshiko_crew_prioritizes_local_knowledge_before_internet(self) -> None:
        """The Peshiko crew is explicitly local-first and only falls back to internet research when needed."""
        crew = PeshikoInvestmentsCrew(model="llama3.1:latest")

        self.assertIn("knowledge/peshiko", crew.cfo_assessment().description)
        self.assertIn("only use internet research", crew.cfo_assessment().description)
        self.assertIn("knowledge/peshiko", crew.ceo_brief().description)

    def test_peshiko_crew_extracts_local_archives_before_fallback(self) -> None:
        """Local zip archives under knowledge/peshiko are extracted and summarized before research fallback."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            knowledge_dir = project_root / "knowledge" / "peshiko" / "business-data"
            knowledge_dir.mkdir(parents=True)
            archive_path = knowledge_dir / "historical-pack.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("notes.txt", "Historical operating context")

            summary = PeshikoInvestmentsCrew._local_knowledge_summary(project_root)

            self.assertIn("knowledge/peshiko", summary)
            self.assertIn("historical-pack.zip", summary)
            self.assertTrue((knowledge_dir / "historical-pack" / "notes.txt").exists())

    def test_crew_normalizes_selected_ollama_model(self) -> None:
        """Raw Ollama model names become LiteLLM-compatible CrewAI identifiers."""
        crew = MyResearchCrew(model="gpt-oss:120b-cloud")

        self.assertEqual(crew._llm().model, "ollama/gpt-oss:120b-cloud")

    def test_run_crew_rejects_an_empty_topic(self) -> None:
        """The runner rejects invalid dashboard input before starting CrewAI."""
        with self.assertRaisesRegex(ValueError, "Enter a topic"):
            run_crew("   ", "gpt-oss:120b-cloud")

    def test_run_crew_rejects_an_unknown_research_source(self) -> None:
        """The service validates source values before crew construction."""
        with patch("my_research_crew.dashboard_service._create_crew") as create_crew:
            with self.assertRaisesRegex(ValueError, "research source"):
                run_crew("local AI", "gpt-oss:120b-cloud", "combined")

        create_crew.assert_not_called()

    def test_select_ollama_model_prefers_requested_default(self) -> None:
        """The requested default wins when it is available from Ollama."""
        selected = select_ollama_model(
            ["llama3.1:latest", "gpt-oss:120b-cloud"], "llama3.1:latest"
        )

        self.assertEqual(selected, "gpt-oss:120b-cloud")

    def test_select_ollama_model_uses_configured_fallback(self) -> None:
        """The configured model is used when the requested default is absent."""
        selected = select_ollama_model(["llama3.1:latest", "gemma4:26b"], "gemma4:26b")

        self.assertEqual(selected, "gemma4:26b")

    def test_list_ollama_models_removes_invalid_and_duplicate_names(self) -> None:
        """Inventory parsing exposes only unique, usable Ollama model names."""
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with (
            patch("my_research_crew.dashboard_service.urlopen", return_value=response),
            patch("my_research_crew.dashboard_service.json.load") as load,
        ):
            load.return_value = {
                "models": [
                    {"name": "gpt-oss:120b-cloud"},
                    {"name": " llama3.1:latest "},
                    {"name": "gpt-oss:120b-cloud"},
                    {"name": ""},
                    {},
                ]
            }
            models = list_ollama_models(
                OllamaSettings("fallback", "http://ollama.test")
            )

        self.assertEqual(models, ["gpt-oss:120b-cloud", "llama3.1:latest"])

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

    def test_create_report_path_is_unique_and_contained(self) -> None:
        """Report directories are unique, topic-derived, and remain under reports."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory).resolve()
            first_path = create_report_path("../../Local LLM research!", project_root)
            second_path = create_report_path("../../Local LLM research!", project_root)

            self.assertEqual(first_path.name, "report.md")
            self.assertEqual(second_path.name, "report.md")
            self.assertNotEqual(first_path.parent, second_path.parent)
            self.assertTrue(first_path.parent.is_relative_to(project_root / "reports"))
            self.assertTrue(second_path.parent.is_relative_to(project_root / "reports"))
            self.assertIn("local-llm-research", first_path.parent.name)

    def test_report_output_file_rejects_paths_outside_reports(self) -> None:
        """CrewAI output paths cannot point outside the project reports folder."""
        outside_path = PROJECT_ROOT.parent / "report.md"

        with self.assertRaisesRegex(ValueError, "reports directory"):
            report_output_file(outside_path)

    def test_dashboard_shows_renamed_title_and_empty_input_message(self) -> None:
        """The dashboard renders the renamed crew and validates empty input."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud", "llama3.1:latest"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()

        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "My Research Crew")
        self.assertEqual(app.segmented_control[1].label, "Research source")
        self.assertEqual(app.segmented_control[1].value, "Internet")
        self.assertEqual(app.selectbox[0].value, "gpt-oss:120b-cloud")

        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud", "llama3.1:latest"],
        ):
            app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertEqual(
            app.warning[0].value, "Enter a topic before starting the crew."
        )

    def test_dashboard_shows_peshiko_executive_workspace(self) -> None:
        """The executive workspace exposes labeled Peshiko briefing inputs."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud", "llama3.1:latest"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[0].set_value("Executive briefing").run()

        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Peshiko Investments Group")
        self.assertEqual(app.text_area[0].label, "Executive question")
        self.assertEqual(app.text_area[1].label, "Business context (optional)")
        self.assertEqual(app.button[0].label, "Prepare executive brief")

    def test_dashboard_explains_local_research_mode(self) -> None:
        """Local mode identifies its isolation and remains selected on rerun."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[1].set_value("Local knowledge").run()

        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control[1].value, "Local knowledge")
        self.assertIn("will not access the internet", app.success[0].value)

    def test_dashboard_locks_research_controls_during_a_run(self) -> None:
        """The selected source and form controls remain visible but disabled."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30)
            app.session_state["run_in_progress"] = True
            app.session_state["research-source"] = "Local knowledge"
            app.run()

        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control[1].value, "Local knowledge")
        self.assertTrue(app.segmented_control[1].disabled)
        self.assertTrue(app.selectbox[0].disabled)
        self.assertTrue(app.text_input[0].disabled)
        self.assertTrue(app.button[0].disabled)

    def test_dashboard_disables_run_when_models_are_unavailable(self) -> None:
        """The dashboard prevents execution when Ollama model inventory fails."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch.dict(os.environ, {"API_BASE": "http://127.0.0.1:1"}):
            app = AppTest.from_file(app_path, default_timeout=30).run()

        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertTrue(app.button[0].disabled)
