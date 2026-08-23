import os
import sys
import json
from my_1st_crew.team import Crew


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    crew = Crew(project_root)

    # minimal example inputs
    inputs = {"project_requirement": "Build a secure user authentication system with email/password and Google OAuth."}

    result = crew.kickoff(inputs=inputs)

    print('\n===== SPRINT RESULT =====')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
