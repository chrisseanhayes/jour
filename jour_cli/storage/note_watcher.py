import logging
import time
from typing import Callable

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileSystemMovedEvent,
)
from watchdog.observers import Observer

from jour_cli.shared.note_document import NoteDocument
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore


class _NoteChangeHandler(FileSystemEventHandler):
    def __init__(self, note_store: FileSystemNoteStore, logger: logging.Logger):
        self.note_store = note_store
        self.logger = logger

    def on_created(self, event: FileSystemEvent) -> None:
        self._enqueue(event.src_path, event.is_directory, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        self._enqueue(event.src_path, event.is_directory, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._enqueue(event.src_path, event.is_directory, "deleted")

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        if event.is_directory:
            return
        self._enqueue(event.src_path, False, "moved from")
        self._enqueue(event.dest_path, False, "moved to")

    def _enqueue(self, filepath: str, is_directory: bool, event_type: str) -> None:
        if is_directory or not filepath.endswith(f".{self.note_store.extension}"):
            return
        self.logger.info("Filesystem event %s: %s", event_type, filepath)
        self.note_store.tag_index.enqueue_note_change(filepath)


class GlobalNoteWatcher:
    """Watch a filesystem note store and durably apply changes to its index."""

    def __init__(
        self,
        note_store: FileSystemNoteStore,
        observer_factory: Callable[[], Observer] = Observer,
        sleep: Callable[[float], None] = time.sleep,
        debounce_seconds: float = 1.0,
    ):
        self.note_store = note_store
        self._observer_factory = observer_factory
        self._sleep = sleep
        self.debounce_seconds = debounce_seconds
        self.logger = note_store.dependencies.logger

    def reconcile(self) -> None:
        """Queue current files and indexed files missing from disk."""
        dependencies = self.note_store.dependencies
        current_paths = dependencies.list_files(
            f"*.{self.note_store.extension}", self.note_store.storage
        )
        for filepath in current_paths:
            self.note_store.tag_index.enqueue_note_change(filepath)

        current_files = {
            dependencies.basename(filepath)
            for filepath in current_paths
        }
        indexed_filenames = self.note_store.tag_index.indexed_filenames()
        missing_files = [
            filename for filename in indexed_filenames if filename not in current_files
        ]
        for filename in missing_files:
            self.note_store.tag_index.enqueue_note_change(
                dependencies.join(self.note_store.storage, filename)
            )
        self.logger.info(
            "Startup reconciliation queued %d current and %d missing note(s)",
            len(current_paths),
            len(missing_files),
        )

    def process_pending_changes(self, debounce_seconds: float = 0) -> None:
        """Apply quiet queued changes; leave failures queued for a later retry."""
        dependencies = self.note_store.dependencies
        for filepath, revision in self.note_store.tag_index.pending_note_changes(
            debounce_seconds
        ):
            self.logger.info("Processing queued note change: %s", filepath)
            try:
                if dependencies.exists(filepath):
                    content = dependencies.read_file(filepath)
                    document = NoteDocument.from_content(content)
                    self.note_store.tag_index.index_note(
                        filepath, document.tags, document.kvp
                    )
                    self.logger.info("Indexed note: %s", filepath)
                else:
                    self.note_store.tag_index.delete_note(
                        dependencies.basename(filepath)
                    )
                    self.logger.info("Removed deleted note from index: %s", filepath)
                self.note_store.tag_index.complete_note_change(filepath, revision)
            except Exception:
                self.logger.exception(
                    "Failed to process queued note change: %s", filepath
                )
                raise

    def run(self) -> None:
        """Watch the note directory until interrupted."""
        dependencies = self.note_store.dependencies
        dependencies.makedirs(self.note_store.storage, exist_ok=True)
        observer = self._observer_factory()
        handler = _NoteChangeHandler(self.note_store, self.logger)
        observer.schedule(handler, self.note_store.storage, recursive=False)
        observer.start()
        self.logger.info(
            "Watching %s for *.%s changes (debounce %.1f seconds)",
            self.note_store.storage,
            self.note_store.extension,
            self.debounce_seconds,
        )
        try:
            self.reconcile()
            while True:
                self.process_pending_changes(self.debounce_seconds)
                self._sleep(0.5)
        finally:
            observer.stop()
            observer.join()
