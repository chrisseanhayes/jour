from dataclasses import dataclass
from typing import Any, Dict, List

import yaml

from jour_cli.shared.note_content import (
    _add_front_matter_kvp,
    _add_front_matter_tag,
    _get_note_type,
    _parse_note_content,
    _parse_note_kvp,
    _remove_front_matter_tag,
)
from jour_cli.shared.note_formats import DEFAULT_NOTE_FORMATS, NoteFormatRegistry


@dataclass(frozen=True)
class NoteDocument:
    """Parsed view of a note while retaining its original serialized content."""

    content: str
    note_type: str
    front_matter: Dict[str, Any]
    tags: List[str]
    body: str
    kvp: Dict[str, Any]

    @classmethod
    def from_content(cls, content: str) -> "NoteDocument":
        tags, body = _parse_note_content(content)
        return cls(
            content=content,
            note_type=_get_note_type(content),
            front_matter=_parse_front_matter(content),
            tags=tags,
            body=body,
            kvp=_parse_note_kvp(content),
        )

    def validate_body(
        self, formats: NoteFormatRegistry = DEFAULT_NOTE_FORMATS
    ) -> Any:
        """Validate the body using its registered note format."""
        return formats.validate(self.note_type, self.body)

    def structured_data(
        self, formats: NoteFormatRegistry = DEFAULT_NOTE_FORMATS
    ) -> Any:
        """Parse structured data when the note type has a registered format."""
        return formats.parse_if_supported(self.note_type, self.body)

    def add_tag(self, tag: str) -> "NoteDocument":
        return self.from_content(_add_front_matter_tag(self.content, tag))

    def remove_tag(self, tag: str) -> "NoteDocument":
        return self.from_content(_remove_front_matter_tag(self.content, tag))

    def set_kvp(self, key: str, value: str) -> "NoteDocument":
        return self.from_content(_add_front_matter_kvp(self.content, key, value))


def _parse_front_matter(content: str) -> Dict[str, Any]:
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        front_matter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid note front matter: {error}") from error
    if not isinstance(front_matter, dict):
        raise ValueError("Note front matter must be a mapping.")
    return front_matter
