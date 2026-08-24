import os
import sys
from typing import Any, Dict

import yaml

from .artifacts import ArtifactStore
from .backlog_adapter import MarkdownBacklogAdapter
from .git_workflow import GitWorkflow
from .llm_adapter import MockLLMAdapter
from .project_context import ProjectContext
from .validator import Validator


class Crew:
    """Minimal orchestrator for the MVP.

    Loads config from the existing project config directory and specifically
    prefers the MVP files there when present.
    """

    ENGINEER_TASKS = {"backend_development_task", "frontend_development_task"}

    def __init__(self, project_root: str, dry_run: bool = False, safe_mode: bool = False, confirm_push: bool = False):
        self.project_root = project_root
        self.dry_run = bool(dry_run)
        self.safe_mode = bool(safe_mode)
        self.confirm_push = bool(confirm_push)

        # Prefer config in target repo when present, otherwise fall back to the agent package config
        candidate_config_1 = os.path.join(project_root, "src", "my_1st_crew", "config")
        candidate_config_2 = os.path.join(project_root, "config")
        if os.path.isdir(candidate_config_1):
            self.config_dir = candidate_config_1
        elif os.path.isdir(candidate_config_2):
            self.config_dir = candidate_config_2
        else:
            agent_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.config_dir = os.path.join(agent_repo_root, "src", "my_1st_crew", "config")

        agent_file = os.path.join(self.config_dir, "mvp_agents.yaml")
        task_file = os.path.join(self.config_dir, "mvp_tasks.yaml")

        if not os.path.exists(agent_file):
            agent_file = os.path.join(self.config_dir, "agents.yaml")
        if not os.path.exists(task_file):
            task_file = os.path.join(self.config_dir, "tasks.yaml")

        with open(agent_file, "r", encoding="utf-8") as f:
            self.agents = yaml.safe_load(f) or {}
        with open(task_file, "r", encoding="utf-8") as f:
            self.tasks = yaml.safe_load(f) or {}

        self.project_context = ProjectContext(project_root)
        self.backlog_adapter = MarkdownBacklogAdapter(project_root)
        self.backlog = self.backlog_adapter.load()
        self.git_workflow = GitWorkflow(project_root, dry_run=self.dry_run, safe_mode=self.safe_mode, confirm_push=self.confirm_push)
        self.adapter = MockLLMAdapter()
        self.validator = Validator()
        self.artifact_store = ArtifactStore(project_root)
        self.artifacts = {}
        self.validation_command = self.project_context.test_command or "python -m compileall ."

    def kickoff(self, inputs: Dict[str, Any]):
        """Run tasks sequentially using the provided inputs."""
        context = {"inputs": inputs, "backlog": self.backlog}
        results = {}

        for task_name, task_cfg in self.tasks.items():
            agent_id = task_cfg.get("agent")
            agent_cfg = self.agents.get(agent_id, {})
            story = self._story_for_task(task_name, context)
            if task_name in self.ENGINEER_TASKS:
                branch_name = self.git_workflow.ensure_story_branch(story, base_branch=self.project_context.default_branch)
                if branch_name:
                    context["current_branch"] = branch_name
                    context["current_story"] = story
                    print(f"\n--- Working on story branch: {branch_name} (base={self.project_context.default_branch}) ---")

            prompt = self._build_prompt(task_name, task_cfg, agent_cfg, context)

            print(f"\n--- Running task: {task_name} (agent={agent_id}) ---")
            response = self.adapter.generate(prompt=prompt, expected=task_cfg.get("expected_output"))

            valid, errors = self.validator.validate(task_cfg.get("expected_output"), response)
            if not valid:
                print(f"Validation failed for {task_name}: {errors}")
                results[task_name] = {"status": "validation_failed", "errors": errors, "output": response}
                break

            print(f"Task {task_name} produced valid {task_cfg.get('expected_output')}")
            results[task_name] = {"status": "ok", "output": response}

            if task_name in self.ENGINEER_TASKS:
                if self.dry_run:
                    commit_result = {"status": "dry_run", "reason": "dry-run mode enabled; no commit performed"}
                    results[task_name]["git"] = commit_result
                    results[task_name]["pull_request"] = {"status": "skipped", "reason": "dry-run; PR not created"}
                elif self.confirm_push:
                    if not sys.stdin.isatty():
                        print("Confirmation required to commit/push but no interactive TTY available; skipping commit/PR")
                        commit_result = {"status": "skipped", "reason": "confirmation required but no TTY"}
                        results[task_name]["git"] = commit_result
                        results[task_name]["pull_request"] = {"status": "skipped", "reason": "confirmation required"}
                    else:
                        resp = input(f"Commit changes for task '{task_name}' on branch '{context.get('current_branch')}'? [y/N]: ")
                        if resp.strip().lower() != 'y':
                            commit_result = {"status": "skipped", "reason": "user declined commit"}
                            results[task_name]["git"] = commit_result
                            results[task_name]["pull_request"] = {"status": "skipped", "reason": "user declined commit"}
                        else:
                            commit_result = self.git_workflow.commit_story(
                                task_name=task_name,
                                story=story,
                                validation_command=self.validation_command,
                            )
                            results[task_name]["git"] = commit_result
                            if commit_result.get("status") == "committed":
                                if self.safe_mode:
                                    pr_result = {"status": "skipped", "reason": "safe_mode enabled; automatic PR creation disabled"}
                                elif os.getenv("AUTO_CREATE_PR", "").lower() == "true":
                                    pr_result = self.git_workflow.create_pr_for_branch(story, base_branch=self.project_context.default_branch)
                                else:
                                    pr_result = {"status": "skipped", "reason": "AUTO_CREATE_PR is not enabled for this environment"}
                                results[task_name]["pull_request"] = pr_result
                else:
                    commit_result = self.git_workflow.commit_story(
                        task_name=task_name,
                        story=story,
                        validation_command=self.validation_command,
                    )
                    results[task_name]["git"] = commit_result
                    if commit_result.get("status") == "committed":
                        if self.safe_mode:
                            pr_result = {"status": "skipped", "reason": "safe_mode enabled; automatic PR creation disabled"}
                        elif os.getenv("AUTO_CREATE_PR", "").lower() == "true":
                            pr_result = self.git_workflow.create_pr_for_branch(story, base_branch=self.project_context.default_branch)
                        else:
                            pr_result = {"status": "skipped", "reason": "AUTO_CREATE_PR is not enabled for this environment"}
                        results[task_name]["pull_request"] = pr_result

            context[task_name] = response
            self.artifacts[task_name] = response

            try:
                validation_record = {"valid": bool(valid), "errors": errors}
                git_meta = results[task_name].get("git") if isinstance(results.get(task_name), dict) else None
                pr_meta = results[task_name].get("pull_request") if isinstance(results.get(task_name), dict) else None
                git_info = {"commit": git_meta, "pr": pr_meta} if git_meta or pr_meta else None
                self.artifact_store.save(
                    task_name=task_name,
                    prompt=prompt,
                    output=response,
                    validation=validation_record,
                    git_meta=git_info,
                )
            except Exception:
                pass

        self.backlog_adapter.save(self.backlog)
        return results

    def _story_for_task(self, task_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        stories = context.get("backlog", {}).get("stories", [])
        if stories:
            return stories[0]
        return {"id": "STORY-1", "title": "Default story"}

    def _build_prompt(self, task_name: str, task_cfg: Dict[str, Any], agent_cfg: Dict[str, Any], context: Dict[str, Any]) -> str:
        backlog_summary = self.backlog_adapter.format_summary(context.get("backlog", {"stories": []}))
        branch_name = context.get("current_branch")
        story_id = (context.get("current_story") or {}).get("id", "")
        prompt = (
            f"Agent role: {agent_cfg.get('role')}\n"
            f"Goal: {agent_cfg.get('goal')}\n\n"
            f"Task: {task_cfg.get('description')}\n\n"
            f"Inputs: {context.get('inputs')}\n\n"
            f"Current backlog: {backlog_summary}\n\n"
            f"Current story: {story_id}\n"
            f"Working branch: {branch_name or 'not set'}\n"
            f"Detected repo stack: {self.project_context.language}\n"
            f"Suggested validation command: {self.validation_command}\n\n"
            "Please produce structured JSON matching the expected output type."
        )
        return prompt
