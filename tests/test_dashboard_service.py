"""Focused tests for dashboard configuration and CrewAI execution."""

from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import os
from types import SimpleNamespace
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
    purge_session_knowledge,
    run_crew,
    save_session_knowledge,
    run_executive_crew,
    select_ollama_model,
    session_knowledge_dir,
    session_has_expired,
)
from my_research_crew.peshiko_crew import PeshikoInvestmentsCrew
from my_research_crew.report_storage import (
    PROJECT_ROOT,
    create_report_path,
    report_output_file,
)
from my_research_crew.report_exports import (
    markdown_download,
    pdf_download,
    report_download_filename,
)
from my_research_crew.crew import MyResearchCrew
from my_research_crew.research_sources import (
    LocalKnowledgeError,
    ResearchSource,
    prepare_local_knowledge,
)


class DashboardServiceTests(unittest.TestCase):
    """Verify dashboard settings and CrewAI execution delegation."""

    def test_report_downloads_read_contained_markdown_and_generate_pdf(self) -> None:
        """Report exports preserve content and produce valid in-memory PDF bytes."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            report_path = project_root / "reports" / "research-run" / "report.md"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(
                "# Quarterly report\n\nPrivate findings: 6G – resilient café.",
                encoding="utf-8",
            )

            markdown_bytes = markdown_download(report_path, project_root)
            pdf_bytes = pdf_download(report_path, project_root)

            self.assertEqual(
                markdown_bytes,
                "# Quarterly report\n\nPrivate findings: 6G – resilient café.".encode(
                    "utf-8"
                ),
            )
            self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
            self.assertGreater(len(pdf_bytes), 100)
            self.assertEqual(
                report_download_filename(report_path, ".md"), "research-run.md"
            )
            self.assertEqual(
                report_download_filename(report_path, ".pdf"), "research-run.pdf"
            )

    def test_report_download_rejects_paths_outside_reports(self) -> None:
        """Exports cannot read arbitrary paths outside the reports directory."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            outside_path = project_root / "private.txt"
            outside_path.write_text("private", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "reports directory"):
                markdown_download(outside_path, project_root)

    def test_save_session_knowledge_accepts_files_and_zip_without_shared_writes(
        self,
    ) -> None:
        """Uploads are stored in the session root and ZIP content is readable."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            shared_file = project_root / "knowledge" / "shared.txt"
            shared_file.parent.mkdir(parents=True)
            shared_file.write_text("shared content", encoding="utf-8")
            archive_buffer = BytesIO()
            with zipfile.ZipFile(archive_buffer, "w") as archive:
                archive.writestr("folder/notes.md", "private archive content")

            result = save_session_knowledge(
                "session-42",
                [
                    SimpleNamespace(name="notes.txt", getvalue=lambda: b"private file"),
                    SimpleNamespace(
                        name="folder.zip", getvalue=lambda: archive_buffer.getvalue()
                    ),
                ],
                project_root,
            )

            knowledge_dir = session_knowledge_dir("session-42", project_root)
            self.assertEqual(result.accepted_files, 2)
            self.assertEqual(result.rejected_files, ())
            self.assertIn("private file", (knowledge_dir / "notes.txt").read_text())
            prepared = prepare_local_knowledge(knowledge_dir)
            self.assertIn("private archive content", prepared.context)
            self.assertEqual(shared_file.read_text(), "shared content")

    def test_save_session_knowledge_rejects_unsupported_files(self) -> None:
        """Unsupported uploads are rejected without being written."""
        with TemporaryDirectory() as temporary_directory:
            result = save_session_knowledge(
                "session-42",
                [SimpleNamespace(name="secrets.pdf", getvalue=lambda: b"private")],
                Path(temporary_directory),
            )

            self.assertEqual(result.accepted_files, 0)
            self.assertEqual(result.rejected_files, ("secrets.pdf",))
            self.assertFalse(
                (
                    session_knowledge_dir("session-42", Path(temporary_directory))
                    / "secrets.pdf"
                ).exists()
            )

    def test_save_session_knowledge_rejects_unsafe_zip_entries(self) -> None:
        """ZIP traversal entries are rejected without escaping the session root."""
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, "w") as archive:
            archive.writestr("../../outside.txt", "must not escape")

        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            result = save_session_knowledge(
                "session-42",
                [
                    SimpleNamespace(
                        name="unsafe.zip", getvalue=lambda: archive_buffer.getvalue()
                    )
                ],
                project_root,
            )

            self.assertEqual(result.accepted_files, 0)
            self.assertEqual(result.rejected_files, ("unsafe.zip",))
            self.assertFalse((project_root / "outside.txt").exists())

    def test_run_crew_uses_only_explicit_session_knowledge_directory(self) -> None:
        """Local runs prepare context from the supplied session directory."""
        crew = MagicMock()
        crew.kickoff.return_value = "local output"
        with TemporaryDirectory() as temporary_directory:
            session_dir = Path(temporary_directory) / "session-42" / "knowledge"
            with (
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=Path(temporary_directory) / "report.md",
                ),
                patch(
                    "my_research_crew.dashboard_service.prepare_local_knowledge"
                ) as prepare,
                patch(
                    "my_research_crew.dashboard_service._create_crew",
                    return_value=crew,
                ),
            ):
                prepare.return_value.context = "session-only content"
                run_crew(
                    "topic",
                    "model",
                    ResearchSource.LOCAL,
                    knowledge_dir=session_dir,
                )

        prepare.assert_called_once_with(session_dir)

    def test_get_ollama_settings_uses_defaults(self) -> None:
        """The dashboard falls back to the approved local Ollama settings."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("my_research_crew.dashboard_service.load_dotenv"),
        ):
            settings = get_ollama_settings()

        self.assertEqual(settings.model, DEFAULT_OLLAMA_MODEL)
        self.assertEqual(settings.api_base, DEFAULT_OLLAMA_API_BASE)

    def test_session_has_expired_after_ten_minutes(self) -> None:
        """A session is expired once its configured timeout elapses."""
        started = datetime.now(timezone.utc) - timedelta(minutes=11)

        self.assertTrue(session_has_expired(started))

    def test_purge_session_knowledge_removes_only_session_state(self) -> None:
        """The purge target is restricted to the session-specific knowledge directory."""
        with TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            session_dir = project_root / "sessions" / "session-42" / "knowledge"
            session_dir.mkdir(parents=True)
            (session_dir / "tmp.txt").write_text("stale user data", encoding="utf-8")
            shared_dir = project_root / "knowledge" / "shared"
            shared_dir.mkdir(parents=True)
            (shared_dir / "shared.txt").write_text("keep me", encoding="utf-8")

            purge_session_knowledge("session-42", project_root)

            self.assertFalse(session_dir.exists())
            self.assertTrue(shared_dir.exists())
            self.assertTrue((shared_dir / "shared.txt").exists())

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
            session_dir = Path(temporary_directory) / "session-42" / "knowledge"
            with (
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service.prepare_local_knowledge"
                ) as prepare,
                patch(
                    "my_research_crew.peshiko_crew.PeshikoInvestmentsCrew",
                ) as executive_crew,
            ):
                prepare.return_value.context = "session executive evidence"
                executive_crew.return_value.crew.return_value = crew
                result = run_executive_crew(
                    "Should we expand?",
                    "Cash reserves are constrained.",
                    "llama3.1:latest",
                    knowledge_dir=session_dir,
                )

        self.assertEqual(result, ExecutiveRunResult("executive output", report_path))
        executive_crew.assert_called_once_with(
            report_path=report_path, model="llama3.1:latest"
        )
        self.assertEqual(
            kickoff.call_args.kwargs["inputs"]["executive_question"],
            "Should we expand?",
        )

    def test_run_executive_crew_respects_selected_source(self) -> None:
        """The executive briefing chooses the selected evidence source explicitly."""
        kickoff = MagicMock(return_value="executive output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "report.md"
            session_dir = Path(temporary_directory) / "session-42" / "knowledge"
            with (
                patch(
                    "my_research_crew.dashboard_service.create_report_path",
                    return_value=report_path,
                ),
                patch(
                    "my_research_crew.dashboard_service.prepare_local_knowledge"
                ) as prepare,
                patch(
                    "my_research_crew.peshiko_crew.PeshikoInvestmentsCrew",
                ) as executive_crew,
            ):
                prepare.return_value.context = "session executive evidence"
                executive_crew.return_value.crew.return_value = crew
                result = run_executive_crew(
                    "Should we expand?",
                    "Cash reserves are constrained.",
                    "llama3.1:latest",
                    ResearchSource.LOCAL,
                    knowledge_dir=session_dir,
                )

        self.assertEqual(
            result,
            ExecutiveRunResult(
                "executive output",
                report_path,
                ResearchSource.LOCAL.label,
            ),
        )
        self.assertEqual(
            kickoff.call_args.kwargs["inputs"]["research_source"],
            ResearchSource.LOCAL.label,
        )
        self.assertIn(
            "session executive evidence",
            kickoff.call_args.kwargs["inputs"]["local_knowledge_summary"],
        )

    def test_run_executive_crew_uses_only_explicit_session_knowledge_directory(
        self,
    ) -> None:
        """Local executive runs prepare context from the supplied session path."""
        kickoff = MagicMock(return_value="executive output")
        crew = MagicMock()
        crew.kickoff = kickoff

        with TemporaryDirectory() as temporary_directory:
            session_dir = Path(temporary_directory) / "session-42" / "knowledge"
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
                    "my_research_crew.peshiko_crew.PeshikoInvestmentsCrew",
                ) as executive_crew,
            ):
                prepare.return_value.context = "private executive evidence"
                executive_crew.return_value.crew.return_value = crew
                run_executive_crew(
                    "Should we expand?",
                    "Cash reserves are constrained.",
                    "llama3.1:latest",
                    ResearchSource.LOCAL,
                    knowledge_dir=session_dir,
                )

        prepare.assert_called_once_with(session_dir)
        self.assertIn(
            "private executive evidence",
            kickoff.call_args.kwargs["inputs"]["local_knowledge_summary"],
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

    def test_dashboard_shows_report_downloads_after_successful_research(self) -> None:
        """Completed research exposes Markdown and on-demand PDF actions."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        report_directory = PROJECT_ROOT / "reports" / "task-016-download-test"
        report_path = report_directory / "report.md"
        report_directory.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            "# Downloadable report\n\nReport content.", encoding="utf-8"
        )
        result = CrewRunResult(
            "Report content.", report_path, ResearchSource.INTERNET.label
        )

        try:
            with patch(
                "my_research_crew.dashboard.list_ollama_models",
                return_value=["gpt-oss:120b-cloud"],
            ):
                app = AppTest.from_file(app_path, default_timeout=30).run()
                self.assertFalse(app.download_button)
                app.session_state["last_research_result"] = result
                app.session_state["last_research_model"] = "gpt-oss:120b-cloud"
                app.run()

            self.assertFalse(app.exception)
            self.assertEqual(app.download_button[0].label, "Download Markdown")
            self.assertEqual(app.button[-1].label, "Generate PDF")
        finally:
            report_path.unlink(missing_ok=True)
            report_directory.rmdir()

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

    def test_dashboard_executive_local_mode_requires_session_knowledge(self) -> None:
        """Executive local mode exposes session uploads and blocks empty runs."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[0].set_value("Executive briefing").run()

        self.assertFalse(app.exception)
        self.assertEqual(app.file_uploader[0].label, "Session knowledge")
        self.assertIn("Upload supported session knowledge", app.warning[0].value)
        self.assertTrue(app.button[0].disabled)

    def test_dashboard_executive_accepts_session_knowledge_upload(self) -> None:
        """The executive workspace becomes ready after a supported upload."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[0].set_value("Executive briefing").run()
            session_id = app.session_state["session_id"]
            app.file_uploader[0].set_value(
                ("briefing.txt", b"private executive evidence", "text/plain")
            ).run()

        try:
            self.assertFalse(app.exception)
            self.assertIn("Session knowledge is ready", app.success[1].value)
            self.assertFalse(app.button[0].disabled)
        finally:
            purge_session_knowledge(session_id)

    def test_dashboard_explains_local_research_mode(self) -> None:
        """Local mode requires private session knowledge before it can run."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[1].set_value("Local knowledge").run()

        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control[1].value, "Local knowledge")
        self.assertEqual(app.file_uploader[0].label, "Session knowledge")
        self.assertIn("Upload supported session knowledge", app.warning[0].value)
        self.assertTrue(app.button[0].disabled)

    def test_dashboard_accepts_session_knowledge_upload(self) -> None:
        """The local workspace reports readiness after a supported upload."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[1].set_value("Local knowledge").run()
            session_id = app.session_state["session_id"]
            app.file_uploader[0].set_value(
                ("notes.txt", b"private session evidence", "text/plain")
            ).run()

        try:
            self.assertFalse(app.exception)
            self.assertIn("Session knowledge is ready", app.success[1].value)
            self.assertFalse(app.button[0].disabled)
        finally:
            purge_session_knowledge(session_id)

    def test_session_knowledge_is_shared_between_workspaces(self) -> None:
        """Research uploads remain ready after switching to Executive briefing."""
        app_path = PROJECT_ROOT / "src" / "my_research_crew" / "dashboard.py"
        with patch(
            "my_research_crew.dashboard.list_ollama_models",
            return_value=["gpt-oss:120b-cloud"],
        ):
            app = AppTest.from_file(app_path, default_timeout=30).run()
            app.segmented_control[1].set_value("Local knowledge").run()
            session_id = app.session_state["session_id"]
            app.file_uploader[0].set_value(
                ("shared-notes.txt", b"shared session evidence", "text/plain")
            ).run()

        try:
            self.assertFalse(app.exception)
            self.assertIn(
                "shared across Research and Executive briefing", app.info[0].value
            )
            self.assertIn("up to 2MB", app.file_uploader[0].help)
            self.assertIn("up to 50MB", app.file_uploader[0].help)
            app.segmented_control[0].set_value("Executive briefing").run()

            self.assertFalse(app.exception)
            self.assertEqual(app.file_uploader[0].label, "Session knowledge")
            self.assertTrue(
                any("Session knowledge is ready" in item.value for item in app.success)
            )
            self.assertTrue(
                any("shared-notes.txt" in item.value for item in app.caption)
            )
            self.assertIn(
                "shared across Research and Executive briefing", app.info[0].value
            )
            self.assertFalse(app.button[0].disabled)
        finally:
            purge_session_knowledge(session_id)

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
