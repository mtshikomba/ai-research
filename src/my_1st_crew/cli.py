import os
import sys
import json
import argparse
from my_1st_crew.team import Crew


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the my_1st_crew MVP against a project root")
    parser.add_argument("--repo-root", dest="repo_root", help="Path to the target repository root the agent should operate on. Defaults to this project.", default=None)
    args = parser.parse_args(argv)

    if args.repo_root:
        project_root = os.path.abspath(args.repo_root)
    else:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    crew = Crew(project_root)

    # minimal example inputs
    inputs = {"project_requirement": "Build a secure user authentication system with email/password and Google OAuth."}

    result = crew.kickoff(inputs=inputs)

    print('\n===== SPRINT RESULT =====')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
