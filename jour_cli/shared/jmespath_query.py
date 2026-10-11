import json
from typing import Any, Dict, List

import jmespath

from jour_cli.shared.note_content import (
    _get_note_type,
    _parse_json_note_data,
    _parse_note_content,
)
from jour_cli.storage.note_store import Note


def query_notes(notes: List[Note], expression: str) -> str:
    """Apply a JMESPath expression to structured notes and serialize its result."""
    records: List[Dict[str, Any]] = []
    for note in notes:
        _, body = _parse_note_content(note.content)
        note_type = _get_note_type(note.content)
        data = _parse_json_note_data(note.content)
        record = dict(data) if data is not None else {}
        record.update(
            {
                "id": note.id,
                "type": note_type,
                "tags": note.tags,
                "content": note.content,
                "body": body,
                "data": data,
            }
        )
        records.append(
            record
        )

    return json.dumps(jmespath.search(expression, records), ensure_ascii=False)
