from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple

from jour_cli.shared.editor import Editor


@dataclass
class Note:
    id: str
    content: str
    tags: List[str]


class TagIndex(Protocol):
    """Index interface used by the filesystem note store."""

    def index_note(self, filepath: str, tags: List[str]) -> None:
        """Index a note and its tags."""

    def tag_counts(self) -> List[Tuple[str, int]]:
        """Return tag/count pairs."""

    def notes_for_tag(self, tag: str) -> List[str]:
        """Return filenames carrying a tag."""

    def tags_by_note(self) -> Dict[str, List[str]]:
        """Return tags grouped by note filename."""

    def delete_note(self, filename: str) -> None:
        """Remove a note from the index."""

    def rebuild(self, notes: List[Tuple[str, List[str]]]) -> None:
        """Replace the index with the supplied note files and their tags."""

    def indexed_filenames(self) -> List[str]:
        """Return all filenames currently recorded in the index."""


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
        """Rebuild the tag index from the current note files."""

    @abstractmethod
    def deleted_note_count(self) -> int:
        """Return indexed notes whose files are no longer present."""
