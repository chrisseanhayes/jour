from typing import List, Optional, Tuple

from jour_cli.shared.dependencies import Dependencies
from jour_cli.shared.editor import Editor
from jour_cli.shared.note_content import _parse_note_content
from jour_cli.storage.note_store import Note, NoteStore, TagIndex


class FileSystemNoteStore(NoteStore):
    """Filesystem-backed note store with a SQLite tag index."""

    def __init__(
        self,
        storage: str,
        extension: str = "jmd",
        *,
        dependencies: Dependencies,
        tag_index: TagIndex,
    ):
        self.storage = storage
        self.extension = extension.lstrip(".")
        self.dependencies = dependencies
        self.tag_index = tag_index

    def create(self, content: str, tags: List[str]) -> str:
        self.dependencies.makedirs(self.storage, exist_ok=True)
        timestamp = self.dependencies.now().strftime("%Y%m%d%H%M%S")
        uid = self.dependencies.new_uuid_hex()[:8]
        note_id = f"{timestamp}_{uid}"
        filepath = self._filepath(note_id)
        self.dependencies.write_file(filepath, content)
        self.tag_index.index_note(filepath, tags)
        return note_id

    def get(self, note_id: str) -> Optional[str]:
        filepath = self._filepath(note_id)
        if not self.dependencies.exists(filepath):
            return None
        return self.dependencies.read_file(filepath)

    def list(self) -> List[Note]:
        paths = self.dependencies.list_files(f"*.{self.extension}", self.storage)
        notes = []
        for filepath in paths:
            content = self.dependencies.read_file(filepath)
            tags, _ = _parse_note_content(content)
            note_id = self.dependencies.splitext(
                self.dependencies.basename(filepath)
            )[0]
            notes.append(Note(note_id, content, tags))
        return notes

    def update(self, note_id: str, content: str) -> bool:
        filepath = self._filepath(note_id)
        if not self.dependencies.exists(filepath):
            return False
        self.dependencies.write_file(filepath, content)
        tags, _ = _parse_note_content(content)
        self.tag_index.index_note(filepath, tags)
        return True

    def delete(self, note_id: str) -> bool:
        filepath = self._filepath(note_id)
        if not self.dependencies.exists(filepath):
            return False
        self.dependencies.remove_file(filepath)
        self.tag_index.delete_note(self.dependencies.basename(filepath))
        return True

    def edit(self, note_id: str, editor: Editor) -> bool:
        filepath = self._filepath(note_id)
        if not self.dependencies.exists(filepath):
            return False
        editor.open(filepath)
        content = self.dependencies.read_file(filepath)
        tags, _ = _parse_note_content(content)
        self.tag_index.index_note(filepath, tags)
        return True

    def search(self, query: str) -> List[str]:
        matches = []
        for note in self.list():
            for line_number, line in enumerate(note.content.splitlines(), start=1):
                if query in line:
                    matches.append(f"{note.id}.{self.extension}:{line_number}:{line}")
        return matches

    def tag_counts(self) -> List[Tuple[str, int]]:
        self._refresh_tag_index()
        return self.tag_index.tag_counts()

    def notes_for_tag(self, tag: str) -> List[str]:
        self._refresh_tag_index()
        return [
            self.dependencies.splitext(filename)[0]
            for filename in self.tag_index.notes_for_tag(tag)
        ]

    def _refresh_tag_index(self) -> None:
        for filepath in self.dependencies.list_files(
            f"*.{self.extension}", self.storage
        ):
            content = self.dependencies.read_file(filepath)
            tags, _ = _parse_note_content(content)
            self.tag_index.index_note(filepath, tags)

    def _filepath(self, note_id: str) -> str:
        if not note_id or self.dependencies.basename(note_id) != note_id:
            raise ValueError(f"Invalid note identifier: {note_id}")
        return self.dependencies.join(self.storage, f"{note_id}.{self.extension}")
