"""Focused tests for isolated internet and local research sources."""

from pathlib import Path
from tempfile import TemporaryDirectory
import stat
import unittest
import zipfile

from my_research_crew.research_sources import (
    InternetSearchTool,
    LocalKnowledgeError,
    ResearchSource,
    prepare_local_knowledge,
)
from my_research_crew.crew import MyResearchCrew


class ResearchSourceTests(unittest.TestCase):
    """Verify source validation and safe local knowledge preparation."""

    def test_research_source_rejects_unknown_values(self) -> None:
        """Only the two approved research sources are accepted."""
        with self.assertRaisesRegex(ValueError, "research source"):
            ResearchSource.parse("combined")

    def test_local_knowledge_reads_supported_files_and_extracts_zip(self) -> None:
        """Local mode prepares supported files, including safe ZIP contents."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "notes.md").write_text("Local evidence", encoding="utf-8")
            with zipfile.ZipFile(knowledge_dir / "archive.zip", "w") as archive:
                archive.writestr("history.txt", "Archived evidence")

            prepared = prepare_local_knowledge(knowledge_dir)

            self.assertEqual(prepared.file_count, 2)
            self.assertIn("Local evidence", prepared.context)
            self.assertIn("Archived evidence", prepared.context)
            self.assertTrue(
                (knowledge_dir / ".extracted" / "archive" / "history.txt").exists()
            )

    def test_local_knowledge_rejects_archive_path_traversal(self) -> None:
        """ZIP entries cannot escape the ignored knowledge directory."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            with zipfile.ZipFile(knowledge_dir / "unsafe.zip", "w") as archive:
                archive.writestr("../secret.txt", "sensitive")

            with self.assertRaisesRegex(LocalKnowledgeError, "unsafe path"):
                prepare_local_knowledge(knowledge_dir)

    def test_local_knowledge_rejects_absolute_archive_paths(self) -> None:
        """Absolute ZIP entries cannot write outside the extraction directory."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            with zipfile.ZipFile(knowledge_dir / "unsafe.zip", "w") as archive:
                archive.writestr("/private.txt", "sensitive")

            with self.assertRaisesRegex(LocalKnowledgeError, "unsafe path"):
                prepare_local_knowledge(knowledge_dir)

    def test_local_knowledge_rejects_archive_links(self) -> None:
        """ZIP links cannot redirect extraction outside the local store."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            link = zipfile.ZipInfo("linked.txt")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(knowledge_dir / "unsafe.zip", "w") as archive:
                archive.writestr(link, "../secret.txt")

            with self.assertRaisesRegex(LocalKnowledgeError, "links"):
                prepare_local_knowledge(knowledge_dir)

    def test_local_knowledge_requires_usable_files(self) -> None:
        """Local mode blocks before kickoff when no supported files exist."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "image.png").write_bytes(b"not research text")

            with self.assertRaisesRegex(LocalKnowledgeError, "No usable"):
                prepare_local_knowledge(knowledge_dir)

    def test_local_knowledge_rejects_corrupt_archives(self) -> None:
        """Corrupt ZIP data produces a safe actionable error."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            (knowledge_dir / "corrupt.zip").write_bytes(b"not a zip archive")

            with self.assertRaisesRegex(LocalKnowledgeError, "corrupt"):
                prepare_local_knowledge(knowledge_dir)

    def test_local_knowledge_rejects_encrypted_archives(self) -> None:
        """Encrypted ZIP entries fail safely before content extraction."""
        with TemporaryDirectory() as temporary_directory:
            knowledge_dir = Path(temporary_directory) / "knowledge"
            knowledge_dir.mkdir()
            archive_path = knowledge_dir / "encrypted.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("private.txt", "sensitive")

            archive_data = bytearray(archive_path.read_bytes())
            local_header = archive_data.index(b"PK\x03\x04")
            central_header = archive_data.index(b"PK\x01\x02")
            archive_data[local_header + 6] |= 0x1
            archive_data[central_header + 8] |= 0x1
            archive_path.write_bytes(archive_data)

            with self.assertRaisesRegex(LocalKnowledgeError, "Encrypted"):
                prepare_local_knowledge(knowledge_dir)

    def test_crew_tools_are_isolated_by_source(self) -> None:
        """Only Internet mode receives an external research tool."""
        internet_crew = MyResearchCrew(source=ResearchSource.INTERNET)
        local_crew = MyResearchCrew(
            source=ResearchSource.LOCAL,
            source_context="Local evidence",
        )

        self.assertIsInstance(internet_crew.researcher().tools[0], InternetSearchTool)
        self.assertEqual(local_crew.researcher().tools, [])

    def test_legacy_mvp_config_is_not_present(self) -> None:
        """The active research crew configuration is the only supported config set."""
        config_dir = Path(__file__).resolve().parents[1] / "src" / "my_research_crew" / "config"

        self.assertFalse((config_dir / "mvp_agents.yaml").exists())
        self.assertFalse((config_dir / "mvp_tasks.yaml").exists())


if __name__ == "__main__":
    unittest.main()
