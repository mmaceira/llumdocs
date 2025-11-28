"""Generic LLM-based structured data extraction with JSON schema validation."""

from __future__ import annotations

import copy
import json
import logging
import re
import time
from pathlib import Path
from typing import TypeVar

from litellm import completion
from litellm.exceptions import APIError, BadRequestError
from pydantic import BaseModel, ValidationError

from ...llm import resolve_model
from ..settings import SETTINGS

T = TypeVar("T", bound=BaseModel)


def transform_schema(schema: dict) -> dict:
    """Transform Pydantic JSON schema for OpenAI strict mode.

    Inlines $defs, marks all properties as required, makes optional fields nullable.
    """
    transformed = copy.deepcopy(schema)

    def normalize_anyof_to_nullable(prop_schema: dict) -> None:
        """Convert anyOf to nullable type format."""
        if "anyOf" in prop_schema:
            # Extract non-null types from anyOf
            types = []
            for item in prop_schema["anyOf"]:
                if isinstance(item, dict) and "type" in item:
                    item_type = item["type"]
                    if item_type != "null":
                        types.append(item_type)
            # Convert to ["type", "null"] format
            if types:
                # If multiple types, use the first one (most common case: float | None -> number)
                prop_schema["type"] = [types[0], "null"] if len(types) == 1 else types + ["null"]
            else:
                prop_schema["type"] = ["null"]
            # Remove anyOf and default if present (we'll handle defaults separately)
            prop_schema.pop("anyOf", None)

    def make_property_nullable(prop_schema: dict, is_optional: bool) -> None:
        """Make optional property nullable."""
        # First normalize anyOf structures
        normalize_anyof_to_nullable(prop_schema)

        # Handle type field
        if "type" in prop_schema:
            prop_type = prop_schema["type"]
            if isinstance(prop_type, str):
                if is_optional and prop_type != "null":
                    prop_schema["type"] = [prop_type, "null"]
            elif isinstance(prop_type, list) and is_optional and "null" not in prop_type:
                prop_schema["type"].append("null")

    # Inline $defs
    if "$defs" in transformed:
        defs = transformed.pop("$defs")

        def inline_refs(obj, defs_dict):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref_path = obj["$ref"]
                    if ref_path.startswith("#/$defs/"):
                        def_name = ref_path.split("/")[-1]
                        if def_name in defs_dict:
                            return inline_refs(copy.deepcopy(defs_dict[def_name]), defs_dict)
                return {k: inline_refs(v, defs_dict) for k, v in obj.items()}
            if isinstance(obj, list):
                return [inline_refs(item, defs_dict) for item in obj]
            return obj

        transformed = inline_refs(transformed, defs)

    # Make all properties required (OpenAI strict requirement)
    # But handle fields with defaults - they can be null and will use default
    if "properties" in transformed:
        all_props = list(transformed["properties"].keys())
        transformed["required"] = all_props

        # Make optional fields nullable (including those with defaults)
        original_required = schema.get("required", [])
        for prop_name, prop_schema in transformed["properties"].items():
            # Fields not in required OR fields with default values should be nullable
            has_default = "default" in prop_schema
            is_optional = prop_name not in original_required or has_default
            make_property_nullable(prop_schema, is_optional)

        # Handle array items
        for prop_schema in transformed["properties"].values():
            prop_type = prop_schema.get("type")
            is_array = prop_type == "array" or (
                isinstance(prop_type, list) and "array" in prop_type
            )
            if is_array and "items" in prop_schema:
                items = prop_schema["items"]
                if isinstance(items, dict) and "properties" in items:
                    # Get original required fields from the inlined schema if available
                    # We need to check the original schema to see which fields were required
                    items_original_required = items.get("required", [])
                    all_item_props = list(items["properties"].keys())
                    items["required"] = all_item_props

                    # Make optional array item properties nullable
                    # Iterate over keys to ensure we modify the actual dict
                    for item_prop_name in list(items["properties"].keys()):
                        item_prop = items["properties"][item_prop_name]

                        # First normalize anyOf structures to type format
                        if "anyOf" in item_prop:
                            types = []
                            for anyof_item in item_prop["anyOf"]:
                                if isinstance(anyof_item, dict) and "type" in anyof_item:
                                    item_type = anyof_item["type"]
                                    if item_type != "null":
                                        types.append(item_type)
                            if types:
                                item_prop["type"] = (
                                    [types[0], "null"] if len(types) == 1 else types + ["null"]
                                )
                            else:
                                item_prop["type"] = ["null"]
                            item_prop.pop("anyOf", None)

                        # Then make nullable if optional
                        has_default = "default" in item_prop
                        is_optional = item_prop_name not in items_original_required or has_default
                        if "type" in item_prop:
                            prop_type = item_prop["type"]
                            if isinstance(prop_type, str):
                                if is_optional and prop_type != "null":
                                    item_prop["type"] = [prop_type, "null"]
                            elif (
                                isinstance(prop_type, list)
                                and is_optional
                                and "null" not in prop_type
                            ):
                                item_prop["type"].append("null")

    return transformed


def parse_json(content: str, model_class: type[T]) -> tuple[T | None, Exception | None]:
    """Parse and validate JSON against Pydantic model.

    Handles plain JSON, markdown-wrapped JSON, nested structures, and null defaults.
    Returns (parsed_model, error) tuple.
    """
    if not content:
        return None, None

    try:
        data = json.loads(content)
        # Unwrap nested structures
        if isinstance(data, dict) and len(data) == 1:
            data = list(data.values())[0]

        # Remove null values for fields that have defaults - let Pydantic use defaults
        if isinstance(data, dict):
            model_fields = model_class.model_fields
            cleaned_data = {}
            for key, value in data.items():
                if value is None and key in model_fields:
                    field_info = model_fields[key]
                    # Skip null if field has a default (not ... and not None)
                    if field_info.default is not ... and field_info.default is not None:
                        continue
                cleaned_data[key] = value
            data = cleaned_data

        validated = model_class.model_validate(data)
        return validated, None
    except json.JSONDecodeError:
        # Extract JSON from markdown
        cleaned = re.sub(r"```json\s*\n?", "", content)
        cleaned = re.sub(r"```\s*\n?", "", cleaned)
        start = cleaned.find("{")
        if start >= 0:
            depth = 0
            for i in range(start, len(cleaned)):
                if cleaned[i] == "{":
                    depth += 1
                elif cleaned[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(cleaned[start : i + 1])
                            if isinstance(data, dict) and len(data) == 1:
                                data = list(data.values())[0]

                            # Remove null values for fields with defaults
                            if isinstance(data, dict):
                                model_fields = model_class.model_fields
                                cleaned_data = {}
                                for key, value in data.items():
                                    if value is None and key in model_fields:
                                        field_info = model_fields[key]
                                        if (
                                            field_info.default is not ...
                                            and field_info.default is not None
                                        ):
                                            continue
                                    cleaned_data[key] = value
                                data = cleaned_data

                            return model_class.model_validate(data), None
                        except (json.JSONDecodeError, ValidationError) as e:
                            return None, e
    except ValidationError as e:
        return None, e

    return None, None


def _is_openai_model(model_id: str) -> bool:
    """Check if model is an OpenAI model (not Ollama)."""
    return not model_id.startswith("ollama/")


def extract_structured_data(
    text: str,
    model_class: type[T],
    system_prompt: str,
    user_prompt_template: str,
    model: str | None = None,
    debug_dir: Path | None = None,
) -> T:
    """Extract structured data from text using LLM with schema validation."""
    model_name = model or SETTINGS.model
    model_config = resolve_model(model_name)
    is_openai = _is_openai_model(model_config.model_id)

    json_schema = model_class.model_json_schema()
    openai_schema = transform_schema(json_schema) if is_openai else None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_template.format(text=text)},
    ]

    def _call(response_format: dict):
        kwargs = {
            "model": model_config.model_id,
            "messages": messages,
            "temperature": SETTINGS.temperature,
            "max_tokens": SETTINGS.max_output_tokens,
            "response_format": response_format,
            **model_config.kwargs,
        }
        if SETTINGS.seed is not None and is_openai:
            kwargs["seed"] = SETTINGS.seed
        return completion(**kwargs)

    raw_responses = []
    last_exc = None

    for attempt in range(3):
        try:
            if SETTINGS.json_strict and is_openai and openai_schema:
                try:
                    response = _call(
                        {
                            "type": "json_schema",
                            "json_schema": {
                                "name": model_class.__name__,
                                "schema": openai_schema,
                                "strict": True,
                            },
                        }
                    )
                except (BadRequestError, APIError) as e:
                    if "400" in str(e) or "strict" in str(e).lower():
                        logging.warning("Strict mode failed, using json_object mode")
                        response = _call({"type": "json_object"})
                    else:
                        raise
            else:
                # Use json_object mode for Ollama or when strict mode is disabled
                response = _call({"type": "json_object"})

            content = response.choices[0].message.content or ""
            raw_responses.append(content)

            if not content:
                raise RuntimeError("Empty response")

            parsed, error = parse_json(content, model_class)
            if parsed:
                return parsed
            if error:
                raise error
            raise ValidationError("Failed to parse", [])

        except (ValidationError, APIError, BadRequestError, RuntimeError) as e:
            last_exc = e
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))

    # Save debug info
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "llm_responses.json").write_text(
            json.dumps(raw_responses, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    error_msg = f"Failed after {len(raw_responses)} attempts: {last_exc}"
    if raw_responses:
        error_msg += f"\nLast response: {raw_responses[-1][:300]}"
    raise RuntimeError(error_msg)
