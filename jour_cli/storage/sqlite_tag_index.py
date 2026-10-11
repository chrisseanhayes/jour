import sqlite3
from typing import Callable, List, Optional, Tuple

from jour_cli.shared.dependencies import Dependencies


_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    filename   TEXT    NOT NULL UNIQUE,
    filepath   TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag     TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tags_tag     ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_note_id ON tags(note_id);
"""


class SQLiteTagIndex:
    """SQLite persistence for filesystem note tags."""

    def __init__(
        self,
        database_path: str,
        dependencies: Dependencies,
        connection_factory: Callable[[str], sqlite3.Connection],
    ):
        self.dependencies = dependencies
        self.database_path = database_path
        self.connection_factory = connection_factory
        database_directory = self.dependencies.dirname(self.database_path)
        if database_directory:
            self.dependencies.makedirs(database_directory, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(_SCHEMA)

    def index_note(self, filepath: str, tags: List[str]) -> None:
        filename = self.dependencies.basename(filepath)
        created_at = filename.split("_")[0]
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO notes (filename, filepath, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET filepath = excluded.filepath
                """,
                (filename, filepath, created_at),
            )
            row = conn.execute(
                "SELECT id FROM notes WHERE filename = ?", (filename,)
            ).fetchone()
            note_id = row["id"]
            conn.execute("DELETE FROM tags WHERE note_id = ?", (note_id,))
            conn.executemany(
                "INSERT INTO tags (note_id, tag) VALUES (?, ?)",
                [(note_id, tag) for tag in tags],
            )

    def tag_counts(self) -> List[Tuple[str, int]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT tag, COUNT(*) AS count
                FROM tags
                GROUP BY tag
                ORDER BY count DESC, tag ASC
                """
            ).fetchall()
        return [(row["tag"], row["count"]) for row in rows]

    def notes_for_tag(self, tag: str) -> List[str]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT n.filename
                FROM notes n
                JOIN tags t ON t.note_id = n.id
                WHERE t.tag = ?
                ORDER BY n.filename DESC
                """,
                (tag,),
            ).fetchall()
        return [row["filename"] for row in rows]

    def delete_note(self, filename: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM notes WHERE filename = ?", (filename,))

    def _get_conn(self) -> sqlite3.Connection:
        conn = self.connection_factory(self.database_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
