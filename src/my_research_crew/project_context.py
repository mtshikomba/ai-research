from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional


class ProjectContext:
    """Detect the target repo's stack and the commands that are already valid there."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.language = self.detect_language()
        self.default_branch = self.detect_default_branch()
        self.test_command = self.detect_test_command()
        self.build_command = self.detect_build_command()
        self.lint_command = self.detect_lint_command()

    def detect_language(self) -> str:
        root = self.project_root
        if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists() or (root / "setup.py").exists():
            return "python"
        if (root / "package.json").exists():
            return "node"
        if (root / "go.mod").exists():
            return "go"
        if (root / "Cargo.toml").exists():
            return "rust"
        if (root / "pom.xml").exists() or (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
            return "java"
        if (root / ".csproj").exists() or (root / ".sln").exists():
            return "dotnet"
        return "generic"

    def detect_default_branch(self) -> str:
        git_root = self._git_root()
        if not git_root:
            return "develop"

        for candidate in ("origin/HEAD", "origin/develop", "origin/main", "origin/master", "develop", "main", "master"):
            result = subprocess.run(["git", "-C", str(self.project_root), "rev-parse", "--verify", candidate], capture_output=True, text=True)
            if result.returncode == 0:
                if candidate.startswith("origin/"):
                    return candidate.replace("origin/", "")
                return candidate

        current = subprocess.run(["git", "-C", str(self.project_root), "branch", "--show-current"], capture_output=True, text=True)
        if current.returncode == 0 and current.stdout.strip():
            return current.stdout.strip()

        return "develop"

    def detect_test_command(self) -> str:
        commands = []
        if (self.project_root / "package.json").exists():
            package = self._read_json(self.project_root / "package.json")
            scripts = (package or {}).get("scripts", {})
            for key in ("test", "test:ci", "ci:test"):
                if key in scripts:
                    commands.append(self._npm_script_cmd(scripts[key]))
            if commands:
                return commands[0]
            commands.append("npm test -- --runInBand")

        if (self.project_root / "pyproject.toml").exists():
            pyproject = self._read_toml(self.project_root / "pyproject.toml")
            if pyproject and "tool" in pyproject and "pytest" in pyproject["tool"]:
                commands.append("pytest -q")
            if self._has_test_files() and self._command_exists("pytest"):
                commands.append("PYTHONPATH=. pytest -q")
            if commands:
                return commands[0]
            commands.append(self._compile_command())

        if (self.project_root / "go.mod").exists():
            return "go test ./..."
        if (self.project_root / "Cargo.toml").exists():
            return "cargo test"
        if (self.project_root / "pom.xml").exists():
            return "mvn test"
        if (self.project_root / "build.gradle").exists() or (self.project_root / "build.gradle.kts").exists():
            return "./gradlew test"
        if (self.project_root / "requirements.txt").exists() or (self.project_root / "setup.py").exists():
            if self._has_test_files() and self._command_exists("pytest"):
                return "PYTHONPATH=. pytest -q"
            return "PYTHONPATH=. python -m compileall ."

        return "python -m compileall ."

    def detect_build_command(self) -> str:
        if (self.project_root / "package.json").exists():
            package = self._read_json(self.project_root / "package.json")
            scripts = (package or {}).get("scripts", {})
            for key in ("build", "build:ci", "compile"):
                if key in scripts:
                    return self._npm_script_cmd(scripts[key])
            return "npm run build"
        if (self.project_root / "pyproject.toml").exists():
            return "python -m compileall ."
        if (self.project_root / "go.mod").exists():
            return "go build ./..."
        if (self.project_root / "Cargo.toml").exists():
            return "cargo build"
        if (self.project_root / "pom.xml").exists():
            return "mvn package -DskipTests"
        if (self.project_root / "build.gradle").exists() or (self.project_root / "build.gradle.kts").exists():
            return "./gradlew assemble"
        if (self.project_root / ".sln").exists() or (self.project_root / ".csproj").exists():
            return "dotnet build"
        return "python -m compileall ."

    def detect_lint_command(self) -> str:
        if (self.project_root / "package.json").exists():
            package = self._read_json(self.project_root / "package.json")
            scripts = (package or {}).get("scripts", {})
            for key in ("lint", "lint:fix", "eslint"):
                if key in scripts:
                    return self._npm_script_cmd(scripts[key])
            return "npm run lint -- --max-warnings=0" if "lint" in scripts else "npm run lint" if "lint" in scripts else "npx eslint ."
        if (self.project_root / "pyproject.toml").exists():
            return "ruff check ." if self._command_exists("ruff") else "python -m compileall ."
        if (self.project_root / "Cargo.toml").exists():
            return "cargo clippy -- -D warnings"
        if (self.project_root / "pom.xml").exists():
            return "mvn -q checkstyle:check"
        return "python -m compileall ."

    def validation_commands(self):
        commands = []
        for command in (self.test_command, self.lint_command, self.build_command):
            if command and command not in commands:
                commands.append(command)
        return commands

    def _git_root(self) -> Optional[str]:
        result = subprocess.run(["git", "-C", str(self.project_root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    def _npm_script_cmd(self, script: str) -> str:
        if script.startswith("npm ") or script.startswith("pnpm ") or script.startswith("yarn "):
            return script
        return f"npm run {script}"

    def _read_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _read_toml(self, path: Path):
        try:
            content = path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return {}

        lowered = content.lower()
        result = {}
        if "[tool.pytest.ini_options]" in lowered or "pytest" in lowered:
            result = {"tool": {"pytest": True}}
        return result

    def _has_test_files(self) -> bool:
        for dir_name in ("tests", "test"):
            path = self.project_root / dir_name
            if not path.exists():
                continue
            for candidate in path.rglob("*.py"):
                if candidate.is_file():
                    return True
        return False

    def _command_exists(self, cmd: str) -> bool:
        return subprocess.run(["bash", "-lc", f"command -v {cmd} >/dev/null 2>&1"], capture_output=True).returncode == 0

    def _compile_command(self) -> str:
        """Return a lightweight syntax-validation command."""
        source_dir = self.project_root / "src"

        if source_dir.exists():
            return "python -m compileall -q src"

        return "python -m compileall -q ."   

    