import jsonschema
from typing import Tuple, Any

# JSON validation schemas for the active research workflow.
SCHEMAS = {
    "backlog": {
        "type": "object",
        "properties": {
            "stories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "title", "acceptance"],
                    "properties": {"id": {"type": "string"}, "title": {"type": "string"}, "acceptance": {"type": "array"}}
                }
            }
        },
        "required": ["stories"]
    },
    "api_spec": {
        "type": "object",
        "properties": {"openapi": {"type": "string"}, "paths": {"type": "object"}},
        "required": ["openapi", "paths"]
    },
    "code_bundle": {
        "type": "object",
        "properties": {"files": {"type": "object"}},
        "required": ["files"]
    },
    "test_plan": {
        "type": "object",
        "properties": {"tests": {"type": "array"}},
        "required": ["tests"]
    }
}

class Validator:
    def __init__(self):
        self.schemas = SCHEMAS

    def validate(self, expected_type: str, data: Any) -> Tuple[bool, str]:
        """Validate `data` against the schema for expected_type.

        Returns (valid, error_message_or_empty)
        """
        schema = self.schemas.get(expected_type)
        if schema is None:
            return False, f"No schema for expected output type: {expected_type}"
        try:
            # jsonschema accepts native python structures
            jsonschema.validate(instance=data, schema=schema)
            return True, ""
        except jsonschema.ValidationError as e:
            return False, str(e)
