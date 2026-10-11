import json
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml


_HASHTAG_PATTERN = re.compile(r"(?<![\w#])#([\w]+(?:-[\w]+)*)(?![\w-])")


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def _extract_hashtags(text: str) -> List[str]:
    """Extract whole-word hashtags without their leading hash symbol."""
    return list(dict.fromkeys(_HASHTAG_PATTERN.findall(text)))


def _build_note_content(
    layout: str,
    date_str: str,
    tags: List[str],
    note_body: str,
    note_type: str = "markdown",
) -> str:
    """Construct the markdown content with YAML front matter."""
    if note_type not in ("markdown", "json"):
        raise ValueError("Note type must be 'markdown' or 'json'.")
    type_metadata = "type: json\n" if note_type == "json" else ""
    return f"""---
layout: {layout}
title: "{date_str}"
date: {date_str}
{type_metadata}tags: {tags}
---

{note_body}
"""


def _get_note_type(content: str) -> str:
    """Return a note's declared type, treating untyped notes as Markdown."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return "markdown"
    front_matter = yaml.safe_load(parts[1]) or {}
    if not isinstance(front_matter, dict):
        raise ValueError("Note front matter must be a mapping.")
    note_type = front_matter.get("type", "markdown")
    if not isinstance(note_type, str):
        raise ValueError("Front matter type must be a string.")
    return note_type


def _parse_json_note_data(content: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON note body, requiring its top-level value to be an object."""
    if _get_note_type(content) != "json":
        return None
    _, body = _parse_note_content(content)
    data = json.loads(body, parse_constant=_reject_json_constant)
    if not isinstance(data, dict):
        raise ValueError("JSON note body must be a JSON object.")
    return data


def _parse_note_content(content: str) -> Tuple[List[str], str]:
    """Parse front-matter tags and body from note content."""
    parts = content.split("---", 2)
    tags = []
    body = ""
    if len(parts) >= 3:
        front_matter = yaml.safe_load(parts[1]) or {}
        if not isinstance(front_matter, dict):
            raise ValueError("Note front matter must be a mapping.")
        body = parts[2].strip()
        front_matter_tags = front_matter.get("tags", [])
        if front_matter_tags is None:
            tags = []
        elif isinstance(front_matter_tags, str):
            tags = [front_matter_tags]
        elif isinstance(front_matter_tags, list):
            if not all(isinstance(tag, str) for tag in front_matter_tags):
                raise ValueError("Front matter tags must be strings.")
            tags = front_matter_tags
        else:
            raise ValueError("Front matter tags must be a string or list of strings.")
    else:
        body = content.strip()
    return list(dict.fromkeys(tags + _extract_hashtags(body))), body


def _parse_note_kvp(content: str) -> Dict[str, Any]:
    """Parse JSON-compatible key/value metadata from note front matter."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        front_matter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid note front matter: {error}") from error
    if not isinstance(front_matter, dict):
        raise ValueError("Note front matter must be a mapping.")

    kvp = front_matter.get("kvp", {})
    if kvp is None:
        return {}
    if not isinstance(kvp, dict):
        raise ValueError("Front matter kvp must be a mapping.")
    if not all(isinstance(key, str) for key in kvp):
        raise ValueError("Front matter kvp keys must be strings.")
    try:
        json.dumps(kvp, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("Front matter kvp values must be JSON-compatible.") from error
    return kvp


def _add_front_matter_tag(content: str, tag: str) -> str:
    """Add a tag to note front matter while preserving its body and metadata."""
    parts = content.split("---", 2)
    if len(parts) >= 3:
        try:
            front_matter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as error:
            raise ValueError(f"Invalid note front matter: {error}") from error
        if not isinstance(front_matter, dict):
            raise ValueError("Note front matter must be a mapping.")
        tags = front_matter.get("tags", [])
        if tags is None:
            tags = []
        elif isinstance(tags, str):
            tags = [tags]
        elif isinstance(tags, list):
            if not all(isinstance(existing_tag, str) for existing_tag in tags):
                raise ValueError("Front matter tags must be strings.")
        else:
            raise ValueError("Front matter tags must be a string or list of strings.")
        front_matter["tags"] = list(dict.fromkeys(tags + [tag]))
        serialized_front_matter = yaml.safe_dump(
            front_matter, sort_keys=False, allow_unicode=True
        ).rstrip()
        return f"{parts[0]}---\n{serialized_front_matter}\n---{parts[2]}"

    return f"---\ntags:\n- {tag}\n---\n{content}"


def _add_front_matter_kvp(content: str, key: str, value: str) -> str:
    """Add or replace a string-valued KVP while preserving note content."""
    parts = content.split("---", 2)
    if len(parts) >= 3:
        try:
            front_matter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as error:
            raise ValueError(f"Invalid note front matter: {error}") from error
        if not isinstance(front_matter, dict):
            raise ValueError("Note front matter must be a mapping.")
        kvp = _parse_note_kvp(content)
        kvp[key] = value
        front_matter["kvp"] = kvp
        serialized_front_matter = yaml.safe_dump(
            front_matter, sort_keys=False, allow_unicode=True
        ).rstrip()
        return f"{parts[0]}---\n{serialized_front_matter}\n---{parts[2]}"

    serialized_front_matter = yaml.safe_dump(
        {"kvp": {key: value}}, sort_keys=False, allow_unicode=True
    ).rstrip()
    return f"---\n{serialized_front_matter}\n---\n{content}"


def _remove_front_matter_tag(content: str, tag: str) -> str:
    """Remove a tag from note front matter while preserving its body and metadata."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    try:
        front_matter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid note front matter: {error}") from error
    if not isinstance(front_matter, dict):
        raise ValueError("Note front matter must be a mapping.")

    tags = front_matter.get("tags", [])
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [tags]
    elif isinstance(tags, list):
        if not all(isinstance(existing_tag, str) for existing_tag in tags):
            raise ValueError("Front matter tags must be strings.")
    else:
        raise ValueError("Front matter tags must be a string or list of strings.")

    remaining_tags = [existing_tag for existing_tag in tags if existing_tag != tag]
    if len(remaining_tags) == len(tags):
        return content

    front_matter["tags"] = remaining_tags
    serialized_front_matter = yaml.safe_dump(
        front_matter, sort_keys=False, allow_unicode=True
    ).rstrip()
    return f"{parts[0]}---\n{serialized_front_matter}\n---{parts[2]}"


def _has_note_body(content: str) -> bool:
    """Return whether note content has a non-empty body after front matter."""
    _, body = _parse_note_content(content)
    return bool(body)


def _get_body_preview(body: str, max_length: int = 40) -> str:
    """Generate a single-line truncated preview of the note body."""
    body_preview = body.replace("\n", " ")
    if len(body_preview) > max_length:
        body_preview = body_preview[:max_length - 3] + "..."
    return body_preview
