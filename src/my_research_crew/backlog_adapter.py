from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class MarkdownBacklogAdapter:
    """Minimal backlog adapter backed by a Markdown file.

    This isolates the project-management storage layer so the repo can later swap
    to Jira or another PM platform without changing the task orchestration.
    """

    def __init__(self, project_root: str, filename: str = "backlog.md"):
        self.project_root = Path(project_root)
        self.backlog_path = self.project_root / filename

    def load(self) -> Dict[str, Any]:
        if not self.backlog_path.exists():
            default = self._default_backlog()
            self.save(default)
            return default

        text = self.backlog_path.read_text(encoding="utf-8")
        stories = self._parse_markdown(text)
        if not stories:
            default = self._default_backlog()
            self.save(default)
            return default
        return {"stories": stories}

    def save(self, backlog: Dict[str, Any]) -> None:
        self.backlog_path.write_text(self._to_markdown(backlog), encoding="utf-8")

    def format_summary(self, backlog: Dict[str, Any]) -> str:
        lines = ["Current backlog:"]
        for story in backlog.get("stories", []):
            lines.append(f"- {story.get('id', 'UNKNOWN')}: {story.get('title', 'Untitled story')}")
        return "\n".join(lines)

    def _default_backlog(self) -> Dict[str, Any]:
        return {
            "stories": [
                {
                    "id": "STORY-1",
                    "title": "User can sign up with email",
                    "status": "planned",
                    "priority": "high",
                    "acceptance": [
                        "Given a new user, when they sign up with email and password, then an account is created"
                    ],
                },
                {
                    "id": "STORY-2",
                    "title": "User can sign in securely",
                    "status": "planned",
                    "priority": "high",
                    "acceptance": [
                        "Given a registered user, when they submit valid credentials, then they are authenticated"
                    ],
                },
            ]
        }

    def _parse_markdown(self, text: str) -> List[Dict[str, Any]]:
        stories: List[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("## "):
                if current is not None:
                    stories.append(current)
                header = line[3:].strip()
                if " - " in header:
                    story_id, title = header.split(" - ", 1)
                else:
                    story_id, title = "", header
                current = {"id": story_id.strip(), "title": title.strip(), "acceptance": []}
                continue
            if current is None:
                continue
            if line.startswith("- Status:"):
                current["status"] = line.split(":", 1)[1].strip()
                continue
            if line.startswith("- Priority:"):
                current["priority"] = line.split(":", 1)[1].strip()
                continue
            if line.startswith("- Acceptance Criteria:"):
                continue
            if line.startswith("- "):
                current.setdefault("acceptance", []).append(line[2:].strip())
                continue
            if line.startswith("  - "):
                current.setdefault("acceptance", []).append(line[4:].strip())

        if current is not None:
            stories.append(current)

        return stories

    def _to_markdown(self, backlog: Dict[str, Any]) -> str:
        lines = ["# Product backlog", ""]
        for story in backlog.get("stories", []):
            story_id = story.get("id", "STORY")
            title = story.get("title", "Untitled story")
            lines.append(f"## {story_id} - {title}")
            if story.get("status"):
                lines.append(f"- Status: {story['status']}")
            if story.get("priority"):
                lines.append(f"- Priority: {story['priority']}")
            acceptance = story.get("acceptance", [])
            if acceptance:
                lines.append("- Acceptance Criteria:")
                for item in acceptance:
                    lines.append(f"  - {item}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"
