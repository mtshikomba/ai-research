import os
import json
import argparse
from my_research_crew.team import Crew


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the my_research_crew research workflow against a project root"
    )
    parser.add_argument(
        "--repo-root",
        dest="repo_root",
        help=(
            "Path to the target repository root the agent should operate on. "
            "Defaults to this project."
        ),
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Run in dry-run mode: do not commit or push any changes",
    )
    parser.add_argument(
        "--safe-mode",
        dest="safe_mode",
        action="store_true",
        help="Safe mode: never perform pushes or create PRs automatically",
    )
    parser.add_argument(
        "--confirm-push",
        dest="confirm_push",
        action="store_true",
        help=(
            "Require interactive confirmation before commit/push/PR " "(requires a TTY)"
        ),
    )
    args = parser.parse_args(argv)

    if args.repo_root:
        project_root = os.path.abspath(args.repo_root)
    else:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    crew = Crew(
        project_root,
        dry_run=args.dry_run,
        safe_mode=args.safe_mode,
        confirm_push=args.confirm_push,
    )

    # minimal example inputs
    inputs = {
        "project_requirement": (
            "Build a secure user authentication system with email/password "
            "and Google OAuth."
        )
    }

    result = crew.kickoff(inputs=inputs)

    print("\n===== SPRINT RESULT =====")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
