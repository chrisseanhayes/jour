import os
import sqlite3

DB_PATH = os.path.join(os.path.expanduser("~/.jour"), "jour.db")

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

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create schema if it doesn't exist. Safe to call on every startup."""
    with _get_conn() as conn:
        conn.executescript(_SCHEMA)

def index_note(filepath, tags):
    """Insert or update a note record and replace its tag associations."""
    filename = os.path.basename(filepath)
    # Extract the timestamp prefix (everything before the first underscore)
    created_at = filename.split("_")[0]
    with _get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
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

def get_tag_counts():
    """Return list of (tag, count) ordered by count descending."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT tag, COUNT(*) AS count FROM tags GROUP BY tag ORDER BY count DESC"
        ).fetchall()
    return [(row["tag"], row["count"]) for row in rows]

def get_notes_for_tag(tag):
    """Return filenames of notes that carry the given tag, newest first."""
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT n.filename
            FROM   notes n
            JOIN   tags  t ON t.note_id = n.id
            WHERE  t.tag = ?
            ORDER  BY n.filename DESC
            """,
            (tag,),
        ).fetchall()
    return [row["filename"] for row in rows]

def delete_note(filename):
    """Delete a note record and associated tags."""
    with _get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM notes WHERE filename = ?", (filename,))

