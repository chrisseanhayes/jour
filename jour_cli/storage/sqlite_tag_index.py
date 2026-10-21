from contextlib import contextmanager
import json
import sqlite3
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

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

CREATE TABLE IF NOT EXISTS kvp_values (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    key     TEXT    NOT NULL,
    value   TEXT    NOT NULL,
    PRIMARY KEY (note_id, key)
);

CREATE INDEX IF NOT EXISTS idx_kvp_key_value ON kvp_values(key, value);

CREATE TABLE IF NOT EXISTS pending_note_changes (
    filepath TEXT PRIMARY KEY,
    revision INTEGER NOT NULL,
    queued_at REAL NOT NULL
);
"""


class SQLiteTagIndex:
    """SQLite persistence for filesystem note tags and key/value metadata."""

    def __init__(
        self,
        database_path: str,
        dependencies: Dependencies,
        connection_factory: Optional[Callable[[str], sqlite3.Connection]] = None,
    ):
        self.dependencies = dependencies
        self.database_path = database_path
        self.connection_factory = (
            connection_factory
            if connection_factory is not None
            else dependencies.sqlite.connect
        )
        database_directory = self.dependencies.dirname(self.database_path)
        if database_directory:
            self.dependencies.makedirs(database_directory, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(_SCHEMA)
            columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(pending_note_changes)"
                ).fetchall()
            }
            if "queued_at" not in columns:
                conn.execute(
                    "ALTER TABLE pending_note_changes "
                    "ADD COLUMN queued_at REAL NOT NULL DEFAULT 0"
                )

    def index_note(
        self,
        filepath: str,
        tags: List[str],
        kvp: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._get_conn() as conn:
            self._index_note(conn, filepath, tags, kvp or {})

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

    def tags_by_note(self) -> Dict[str, List[str]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT n.filename, t.tag
                FROM notes n
                JOIN tags t ON t.note_id = n.id
                ORDER BY n.filename DESC, t.id ASC
                """
            ).fetchall()
        tags_by_note: Dict[str, List[str]] = {}
        for row in rows:
            tags_by_note.setdefault(row["filename"], []).append(row["tag"])
        return tags_by_note

    def kvp_by_note(self) -> Dict[str, Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT n.filename, k.key, k.value
                FROM notes n
                JOIN kvp_values k ON k.note_id = n.id
                ORDER BY n.filename DESC, k.key ASC
                """
            ).fetchall()
        kvp_by_note: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            kvp_by_note.setdefault(row["filename"], {})[row["key"]] = json.loads(
                row["value"]
            )
        return kvp_by_note

    def delete_note(self, filename: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM notes WHERE filename = ?", (filename,))

    def rebuild(
        self, notes: List[Tuple[str, List[str], Dict[str, Any]]]
    ) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM notes")
            for filepath, tags, kvp in notes:
                self._index_note(conn, filepath, tags, kvp)

    def indexed_filenames(self) -> List[str]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT filename FROM notes").fetchall()
        return [row["filename"] for row in rows]

    def enqueue_note_change(self, filepath: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO pending_note_changes (filepath, revision, queued_at)
                VALUES (?, 1, ?)
                ON CONFLICT(filepath) DO UPDATE
                SET revision = pending_note_changes.revision + 1,
                    queued_at = excluded.queued_at
                """,
                (filepath, time.time()),
            )

    def pending_note_changes(
        self, debounce_seconds: float = 0
    ) -> List[Tuple[str, int]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT filepath, revision
                FROM pending_note_changes
                WHERE queued_at <= ?
                ORDER BY filepath
                """,
                (time.time() - debounce_seconds,),
            ).fetchall()
        return [(row["filepath"], row["revision"]) for row in rows]

    def complete_note_change(self, filepath: str, revision: int) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM pending_note_changes WHERE filepath = ? AND revision = ?",
                (filepath, revision),
            )

    @contextmanager
    def _get_conn(self) -> Iterator[sqlite3.Connection]:
        conn = self.connection_factory(self.database_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            # Originally, each CLI call ended soon after opening this connection,
            # so the process reclaimed it on exit. The long-running watcher opens
            # many connections over its lifetime, making that an ongoing leak:
            # `with conn` commits but does not close. Yield so this context manager
            # can close every connection promptly.
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _index_note(
        self,
        conn: sqlite3.Connection,
        filepath: str,
        tags: List[str],
        kvp: Dict[str, Any],
    ) -> None:
        filename = self.dependencies.basename(filepath)
        created_at = filename.split("_")[0]
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
        conn.execute("DELETE FROM kvp_values WHERE note_id = ?", (note_id,))
        conn.executemany(
            "INSERT INTO kvp_values (note_id, key, value) VALUES (?, ?, ?)",
            [
                (
                    note_id,
                    key,
                    json.dumps(value, ensure_ascii=False, allow_nan=False),
                )
                for key, value in kvp.items()
            ],
        )
