import json
import os
import re
import subprocess
from subprocess import TimeoutExpired
from typing import Any, Dict, Optional


class GitWorkflow:
    """Lightweight git helper for story-based engineering work.

    The helper intentionally fails gracefully when git or GitHub auth is missing,
    so the agent loop does not crash the MVP when operating in a lightweight local
    development environment.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root

    def ensure_story_branch(self, story: Optional[Dict[str, Any]], base_branch: Optional[str] = None) -> Optional[str]:
        repo_root = self._repo_root()
        if not repo_root:
            return None

        story_id = str((story or {}).get("id", "story")).strip() or "story"
        title = str((story or {}).get("title", "untitled-story")).strip() or "untitled-story"
        branch_name = self._branch_name_for_story(story_id, title)

        base_branch = base_branch or self._preferred_base_branch()
        if not base_branch:
            return None

        current = self._git("rev-parse", "--abbrev-ref", "HEAD", check=False)
        if current and current.stdout.strip() == branch_name:
            return branch_name

        self._ensure_base_branch(base_branch)
        if self._git("rev-parse", "--verify", branch_name, check=False).returncode == 0:
            self._git("checkout", branch_name, check=False)
        else:
            self._git("checkout", "-B", branch_name, check=False)
        return branch_name

    def commit_story(self, task_name: str, story: Optional[Dict[str, Any]], validation_command: str) -> Dict[str, Any]:
        repo_root = self._repo_root()
        if not repo_root:
            return {"status": "skipped", "reason": "git repo not detected"}

        try:
            validation = self.run_validation(validation_command)
        except TimeoutExpired:
            return {"status": "validation_failed", "command": validation_command, "stdout": "", "stderr": "validation timed out"}
        if validation.returncode != 0:
            return {
                "status": "validation_failed",
                "command": validation_command,
                "stdout": validation.stdout,
                "stderr": validation.stderr,
            }

        status = self._git("status", "--porcelain")
        if not status.stdout.strip():
            return {"status": "skipped", "reason": "no local changes to commit"}

        self._ensure_git_user()
        story_id = str((story or {}).get("id", "story")).strip() or "story"
        title = str((story or {}).get("title", "story")).strip() or "story"
        message = f"feat({story_id.lower()}): {task_name} for {story_id}"

        self._git("add", "-A")
        commit = self._git("commit", "-m", message, check=False)
        if commit.returncode != 0:
            return {
                "status": "commit_failed",
                "branch": self._branch_name_for_story(story_id, title),
                "stdout": commit.stdout,
                "stderr": commit.stderr,
            }

        return {
            "status": "committed",
            "branch": self._branch_name_for_story(story_id, title),
            "message": message,
        }

    def create_pr_for_branch(self, story: Optional[Dict[str, Any]], base_branch: str = "develop") -> Dict[str, Any]:
        branch_name = self._branch_name_for_story(
            str((story or {}).get("id", "story")).strip() or "story",
            str((story or {}).get("title", "story")).strip() or "story"
        )

        try:
            push = self._git("push", "--set-upstream", "origin", branch_name, check=False, timeout=20)
        except TimeoutExpired:
            return {"status": "skipped", "reason": "git push timed out while contacting the remote repo"}
        if push.returncode != 0:
            return {
                "status": "skipped",
                "reason": "local branch was not pushed; GitHub auth or remote permissions are unavailable",
                "stderr": push.stderr,
            }

        if self._command_exists("gh"):
            title = f"feat({branch_name})"
            body = f"## Summary\n\nThis PR was created from `{branch_name}` into `{base_branch}`."
            try:
                pr = subprocess.run(
                    ["gh", "pr", "create", "--base", base_branch, "--head", branch_name, "--title", title, "--body", body],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
            except TimeoutExpired:
                return {"status": "skipped", "reason": "gh PR creation timed out"}
            if pr.returncode == 0:
                return {"status": "opened", "branch": branch_name, "url": pr.stdout.strip()}
            return {
                "status": "skipped",
                "reason": "gh CLI is available but PR creation failed",
                "stdout": pr.stdout,
                "stderr": pr.stderr,
            }

        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if token:
            repo = self._github_repo_name()
            if repo:
                payload = {
                    "title": f"feat({branch_name})",
                    "head": branch_name,
                    "base": base_branch,
                    "body": f"## Summary\n\nThis PR was created from `{branch_name}` into `{base_branch}`.",
                }
                try:
                    response = subprocess.run(
                        [
                            "curl",
                            "-sS",
                            "-X",
                            "POST",
                            "-H",
                            "Accept: application/vnd.github+json",
                            "-H",
                            f"Authorization: Bearer {token}",
                            "-H",
                            "X-GitHub-Api-Version: 2022-11-28",
                            "https://api.github.com/repos/{repo}/pulls".format(repo=repo),
                            "-d",
                            json.dumps(payload),
                        ],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )
                except TimeoutExpired:
                    return {"status": "skipped", "reason": "GitHub API PR creation timed out"}
                if response.returncode == 0:
                    payload_data = json.loads(response.stdout or "{}")
                    if payload_data.get("html_url"):
                        return {"status": "opened", "branch": branch_name, "url": payload_data["html_url"]}
                return {
                    "status": "skipped",
                    "reason": "GitHub API PR creation failed",
                    "stdout": response.stdout,
                    "stderr": response.stderr,
                }

        return {
            "status": "skipped",
            "reason": "GitHub authentication was not configured, so the PR could not be opened automatically",
        }

    def run_validation(self, command: str):
        return subprocess.run(command, cwd=self.project_root, shell=True, capture_output=True, text=True, timeout=60)

    def _repo_root(self) -> Optional[str]:
        result = subprocess.run(["git", "-C", self.project_root, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    def _preferred_base_branch(self) -> str:
        for candidate in ("develop", "main", "master"):
            if self._git("rev-parse", "--verify", candidate, check=False).returncode == 0:
                return candidate
            if self._git("rev-parse", "--verify", f"origin/{candidate}", check=False).returncode == 0:
                return candidate
        return "develop"

    def _ensure_base_branch(self, base_branch: str) -> None:
        if self._git("rev-parse", "--verify", base_branch, check=False).returncode == 0:
            self._git("checkout", base_branch, check=False)
            return
        if self._git("rev-parse", "--verify", f"origin/{base_branch}", check=False).returncode == 0:
            self._git("checkout", "-B", base_branch, f"origin/{base_branch}", check=False)

    def _ensure_git_user(self) -> None:
        user_name = self._git("config", "user.name", check=False)
        if user_name.returncode != 0 or not user_name.stdout.strip():
            self._git("config", "user.name", "Copilot", check=False)
        user_email = self._git("config", "user.email", check=False)
        if user_email.returncode != 0 or not user_email.stdout.strip():
            self._git("config", "user.email", "copilot@example.com", check=False)

    def _branch_name_for_story(self, story_id: str, title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", (title or "story").lower()).strip("-") or "story"
        safe_story_id = re.sub(r"[^a-z0-9]+", "-", story_id.lower()).strip("-") or "story"
        return f"feature/{safe_story_id}-{slug}"[:80]

    def _command_exists(self, cmd: str) -> bool:
        result = subprocess.run(["which", cmd], capture_output=True, text=True)
        return result.returncode == 0

    def _github_repo_name(self) -> Optional[str]:
        remote = self._git("remote", "get-url", "origin", check=False)
        if remote.returncode != 0:
            return None
        url = remote.stdout.strip()
        match = re.search(r"github.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?$", url)
        if not match:
            return None
        return f"{match.group('owner')}/{match.group('repo')}"

    def _git(self, *args, check: bool = True, timeout: Optional[int] = None):
        result = subprocess.run(["git", "-C", self.project_root, *args], capture_output=True, text=True, timeout=timeout)
        if check and result.returncode != 0:
            raise RuntimeError(f"git command failed: {' '.join(args)}\n{result.stderr or result.stdout}")
        return result
