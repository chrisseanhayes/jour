import json
from typing import Any, Dict, List

import jmespath

from jour_cli.shared.note_document import NoteDocument
from jour_cli.shared.note_formats import DEFAULT_NOTE_FORMATS, NoteFormatRegistry
from jour_cli.storage.note_store import Note


def query_notes(
    notes: List[Note],
    expression: str,
    formats: NoteFormatRegistry = DEFAULT_NOTE_FORMATS,
) -> str:
    """Apply a JMESPath expression to structured notes and serialize its result."""
    records: List[Dict[str, Any]] = []
    for note in notes:
        document = NoteDocument.from_content(note.content)
        data = document.structured_data(formats)
        record = dict(data) if isinstance(data, dict) else {}
        record.update(
            {
                "id": note.id,
                "type": document.note_type,
                "tags": note.tags,
                "kvp": note.kvp,
                "content": note.content,
                "body": document.body,
                "data": data,
            }
        )
        records.append(
            record
        )

    return json.dumps(jmespath.search(expression, records), ensure_ascii=False)
