from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple

from jour_cli.shared.editor import Editor


@dataclass
class Note:
    id: str
    content: str
    tags: List[str]
    kvp: Dict[str, Any] = field(default_factory=dict)


class TagIndex(Protocol):
    """Index interface used by the filesystem note store."""

    def index_note(
        self, filepath: str, tags: List[str], kvp: Optional[Dict[str, Any]] = None
    ) -> None:
        """Index a note, its tags, and its key/value metadata."""

    def tag_counts(self) -> List[Tuple[str, int]]:
        """Return tag/count pairs."""

    def notes_for_tag(self, tag: str) -> List[str]:
        """Return filenames carrying a tag."""

    def tags_by_note(self) -> Dict[str, List[str]]:
        """Return tags grouped by note filename."""

    def kvp_by_note(self) -> Dict[str, Dict[str, Any]]:
        """Return key/value metadata grouped by note filename."""

    def delete_note(self, filename: str) -> None:
        """Remove a note from the index."""

    def rebuild(
        self, notes: List[Tuple[str, List[str], Dict[str, Any]]]
    ) -> None:
        """Replace the index with the supplied note files, tags, and key/value data."""

    def indexed_filenames(self) -> List[str]:
        """Return all filenames currently recorded in the index."""

    def enqueue_note_change(self, filepath: str) -> None:
        """Persist a filesystem change until the note index processes it."""

    def pending_note_changes(
        self, debounce_seconds: float = 0
    ) -> List[Tuple[str, int]]:
        """Return queued changes that have been quiet for the given duration."""

    def complete_note_change(self, filepath: str, revision: int) -> None:
        """Remove a queued change if it has not been superseded."""


class NoteStore(ABC):
    """Persistence interface used by commands to manage notes."""

    @abstractmethod
    def create(self, content: str, tags: List[str]) -> str:
        """Save a new note and return its identifier."""

    @abstractmethod
    def get(self, note_id: str) -> Optional[str]:
        """Retrieve a note's content by identifier."""

    @abstractmethod
    def list(self) -> List[Note]:
        """Return all notes, newest first."""

    @abstractmethod
    def update(self, note_id: str, content: str) -> bool:
        """Replace a note's content."""

    @abstractmethod
    def delete(self, note_id: str) -> bool:
        """Delete a note, returning whether it existed."""

    @abstractmethod
    def edit(self, note_id: str, editor: Editor) -> bool:
        """Open a note in an editor and persist any changes."""

    @abstractmethod
    def search(self, query: str) -> List[str]:
        """Return formatted search matches."""

    @abstractmethod
    def tag_counts(self) -> List[Tuple[str, int]]:
        """Return tag/count pairs."""

    @abstractmethod
    def notes_for_tag(self, tag: str) -> List[str]:
        """Return identifiers for notes carrying a tag."""

    @abstractmethod
    def rebuild_tag_index(self) -> int:
        """Rebuild tag and key/value indexes from the current note files."""

    @abstractmethod
    def deleted_note_count(self) -> int:
        """Return indexed notes whose files are no longer present."""
