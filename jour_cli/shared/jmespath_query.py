import json
from typing import Any, Dict, List

import jmespath

from jour_cli.shared.note_content import _parse_note_content
from jour_cli.storage.note_store import Note


def query_notes(notes: List[Note], expression: str) -> str:
    """Apply a JMESPath expression to structured notes and serialize its result."""
    records: List[Dict[str, Any]] = []
    for note in notes:
        _, body = _parse_note_content(note.content)
        records.append(
            {
                "id": note.id,
                "tags": note.tags,
                "content": note.content,
                "body": body,
            }
        )

    return json.dumps(jmespath.search(expression, records), ensure_ascii=False)
