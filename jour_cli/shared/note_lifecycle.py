from dataclasses import dataclass
from enum import Enum
from typing import Optional

from jour_cli.shared.note_document import NoteDocument
from jour_cli.shared.note_formats import DEFAULT_NOTE_FORMATS, NoteFormatRegistry


class NoteLifecycleState(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    SAVED = "saved"
    REJECTED = "rejected"
    DISCARDED = "discarded"


@dataclass(frozen=True)
class NoteLifecycle:
    """A validated transition record for creating or editing a note."""

    state: NoteLifecycleState
    content: str
    document: Optional[NoteDocument] = None
    error: Optional[str] = None

    @classmethod
    def draft(cls, content: str) -> "NoteLifecycle":
        return cls(NoteLifecycleState.DRAFT, content)

    def validate(
        self, formats: NoteFormatRegistry = DEFAULT_NOTE_FORMATS
    ) -> "NoteLifecycle":
        self._require_state(NoteLifecycleState.DRAFT)
        try:
            document = NoteDocument.from_content(self.content)
            document.validate_body(formats)
        except ValueError as error:
            return NoteLifecycle(
                NoteLifecycleState.REJECTED,
                self.content,
                error=str(error),
            )
        return NoteLifecycle(
            NoteLifecycleState.VALIDATED,
            self.content,
            document=document,
        )

    def mark_saved(self) -> "NoteLifecycle":
        self._require_state(NoteLifecycleState.VALIDATED)
        return NoteLifecycle(
            NoteLifecycleState.SAVED,
            self.content,
            document=self.document,
        )

    def discard(self) -> "NoteLifecycle":
        if self.state not in (
            NoteLifecycleState.DRAFT,
            NoteLifecycleState.VALIDATED,
            NoteLifecycleState.REJECTED,
        ):
            raise ValueError(f"Cannot discard a note in {self.state.value} state.")
        return NoteLifecycle(
            NoteLifecycleState.DISCARDED,
            self.content,
            document=self.document,
            error=self.error,
        )

    def _require_state(self, expected: NoteLifecycleState) -> None:
        if self.state != expected:
            raise ValueError(
                f"Cannot transition from {self.state.value}; "
                f"expected {expected.value}."
            )
