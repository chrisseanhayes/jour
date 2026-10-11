import sqlite3
from typing import Callable

from jour_cli.config import get_storage_path
from jour_cli.shared.dependencies import Dependencies
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.note_store import NoteStore, TagIndex
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


DatabaseConnectionFactory = Callable[[str], sqlite3.Connection]
TagIndexFactory = Callable[[dict, Dependencies], TagIndex]
NoteStoreFactory = Callable[[dict, Dependencies], NoteStore]


def build_note_store(
    config: dict,
    dependencies: Dependencies,
    tag_index_factory: TagIndexFactory,
) -> NoteStore:
    """Create the default filesystem note store."""
    storage_config = config.get("storage", {})
    tag_index = tag_index_factory(config, dependencies)
    return FileSystemNoteStore(
        get_storage_path(config, dependencies),
        storage_config.get("extension", "jmd"),
        dependencies=dependencies,
        tag_index=tag_index,
    )


class FileSystemNoteStoreFactory:
    """Creates the default filesystem store and its SQLite metadata index."""

    def __init__(
        self,
        database_connection_factory: DatabaseConnectionFactory,
    ):
        self._database_connection_factory = database_connection_factory

    def __call__(self, config: dict, dependencies: Dependencies) -> NoteStore:
        database_path = dependencies.expanduser(
            config.get("database", {}).get("path", "~/.jour/jour.db")
        )
        return build_note_store(
            config,
            dependencies,
            lambda _config, _dependencies: SQLiteTagIndex(
                database_path=database_path,
                dependencies=dependencies,
                connection_factory=self._database_connection_factory,
            ),
        )
