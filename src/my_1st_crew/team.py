import os
import yaml
from typing import Dict, Any

from .backlog_adapter import MarkdownBacklogAdapter
from .git_workflow import GitWorkflow
from .llm_adapter import MockLLMAdapter
from .validator import Validator


class Crew:
    """Minimal orchestrator for the MVP.

    Loads config from the existing project config directory and specifically
    prefers the MVP files there when present.
    """

    ENGINEER_TASKS = {"backend_development_task", "frontend_development_task"}

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.config_dir = os.path.join(project_root, "src", "my_1st_crew", "config")
        if not os.path.isdir(self.config_dir):
            self.config_dir = os.path.join(project_root, "config")

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

        self.backlog_adapter = MarkdownBacklogAdapter(project_root)
        self.backlog = self.backlog_adapter.load()
        self.git_workflow = GitWorkflow(project_root)
        self.adapter = MockLLMAdapter()
        self.validator = Validator()
        self.artifacts = {}

    def kickoff(self, inputs: Dict[str, Any]):
        """Run tasks sequentially using the provided inputs."""
        context = {"inputs": inputs, "backlog": self.backlog}
        results = {}

        for task_name, task_cfg in self.tasks.items():
            agent_id = task_cfg.get("agent")
            agent_cfg = self.agents.get(agent_id, {})
            story = self._story_for_task(task_name, context)
            if task_name in self.ENGINEER_TASKS:
                branch_name = self.git_workflow.ensure_story_branch(story)
                if branch_name:
                    context["current_branch"] = branch_name
                    context["current_story"] = story
                    print(f"\n--- Working on story branch: {branch_name} ---")

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
                commit_result = self.git_workflow.commit_story(
                    task_name=task_name,
                    story=story,
                    validation_command="PYTHONPATH=src python -m compileall src",
                )
                results[task_name]["git"] = commit_result
                if commit_result.get("status") == "committed":
                    pr_result = self.git_workflow.create_pr_for_branch(story, base_branch="develop")
                    results[task_name]["pull_request"] = pr_result

            context[task_name] = response
            self.artifacts[task_name] = response

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
            f"Working branch: {branch_name or 'not set'}\n\n"
            "Please produce structured JSON matching the expected output type."
        )
        return prompt
