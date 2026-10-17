from typing import Any

from pydantic import BaseModel

# Schema keywords whose value is a mapping of *names* to schemas, not a schema itself.
_NAME_MAPS = {"properties", "$defs", "definitions"}
# Keywords that only add noise (or risk) for a model that has to fill the schema in.
_DROPPED = {"title", "default"}


def _clean(node: Any) -> Any:
    if isinstance(node, list):
        return [_clean(item) for item in node]
    if not isinstance(node, dict):
        return node

    cleaned: dict[str, Any] = {}
    for key, value in node.items():
        if key in _DROPPED:
            continue
        if key in _NAME_MAPS and isinstance(value, dict):
            # Keep every name (a field may itself be called "title"), clean each schema under it.
            cleaned[key] = {name: _clean(schema) for name, schema in value.items()}
        else:
            cleaned[key] = _clean(value)
    return cleaned


def to_gemini_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    JSON Schema for `response_json_schema`, derived from a Pydantic model so the schema the model
    must follow and the validator that checks its answer can never drift apart.
    Auto-generated `title` and `default` keywords are removed; field descriptions are kept because
    they are instructions to the model.
    """
    return _clean(model.model_json_schema())
