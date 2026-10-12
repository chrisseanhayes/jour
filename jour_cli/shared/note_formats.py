import json
import re
from typing import Any, Dict, Protocol


class NoteFormat(Protocol):
    name: str

    def parse_body(self, body: str) -> Any:
        """Validate a body and return structured data when the format has it."""


class MarkdownNoteFormat:
    name = "markdown"

    def parse_body(self, body: str) -> Any:
        return None


class JsonNoteFormat:
    name = "json"

    def parse_body(self, body: str) -> Dict[str, Any]:
        data = json.loads(body, parse_constant=_reject_json_constant)
        if not isinstance(data, dict):
            raise ValueError("JSON note body must be a JSON object.")
        return data


class NoteFormatRegistry:
    """Registry of note body validators, injectable by applications and tests."""

    def __init__(self) -> None:
        self._formats: Dict[str, NoteFormat] = {}

    def copy(self) -> "NoteFormatRegistry":
        registry = NoteFormatRegistry()
        registry._formats.update(self._formats)
        return registry

    def register(self, note_format: NoteFormat) -> None:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", note_format.name):
            raise ValueError("Note format name must be a non-empty identifier.")
        if note_format.name in self._formats:
            raise ValueError(f"Note format already registered: {note_format.name}")
        self._formats[note_format.name] = note_format

    def validate(self, note_type: str, body: str) -> Any:
        note_format = self._formats.get(note_type)
        if note_format is None:
            raise ValueError(f"Unsupported note type: {note_type}")
        return self._parse_body(note_format, body)

    def parse_if_supported(
        self, note_type: str, body: str
    ) -> Any:
        note_format = self._formats.get(note_type)
        if note_format is None:
            return None
        return self._parse_body(note_format, body)

    @staticmethod
    def _parse_body(note_format: NoteFormat, body: str) -> Any:
        data = note_format.parse_body(body)
        try:
            json.dumps(data, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Note format '{note_format.name}' returned data that is not "
                "JSON-serializable."
            ) from error
        return data


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


DEFAULT_NOTE_FORMATS = NoteFormatRegistry()
DEFAULT_NOTE_FORMATS.register(MarkdownNoteFormat())
DEFAULT_NOTE_FORMATS.register(JsonNoteFormat())


def create_default_note_formats() -> NoteFormatRegistry:
    return DEFAULT_NOTE_FORMATS.copy()
