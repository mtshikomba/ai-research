import json
from typing import Any

class MockLLMAdapter:
    """A deterministic mock LLM adapter for development and CI.

    generate(prompt, expected) returns a Python object (dict/list) that
    conforms to one of the expected_output types: backlog, api_spec, code_bundle, test_plan.
    """

    def generate(self, prompt: str, expected: str = None) -> Any:
        # Very small deterministic heuristics to return structured objects
        if expected == "backlog":
            return {
                "stories": [
                    {
                        "id": "STORY-1",
                        "title": "User can sign up with email",
                        "acceptance": [
                            "Given a new user, when they sign up with email and password, then an account is created"
                        ],
                        "priority": "high"
                    }
                ]
            }
        if expected == "api_spec":
            return {
                "openapi": "3.0.0",
                "info": {"title": "Auth API", "version": "0.1.0"},
                "paths": {
                    "/signup": {
                        "post": {
                            "summary": "Create a user",
                            "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Signup"}}}},
                            "responses": {"201": {"description": "Created"}}
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "Signup": {"type": "object", "properties": {"email": {"type": "string"}, "password": {"type": "string"}}}
                    }
                }
            }
        if expected == "code_bundle":
            return {
                "files": {
                    "app.py": "def hello():\n    return 'hello'\n",
                    "requirements.txt": "fastapi\nuvicorn\n"
                }
            }
        if expected == "test_plan":
            return {
                "tests": [
                    {"id": "T1", "desc": "Signup with valid email", "steps": ["POST /signup with valid body", "Expect 201"]}
                ]
            }
        # default fallback
        return {"text": "No structured expected provided, echoing prompt first 200 chars", "prompt_snippet": prompt[:200]}
