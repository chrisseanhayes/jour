import os
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from jour_cli.cmd.rebuild import cmd_rebuild
from jour_cli.shared.dependencies import Dependencies
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


class RebuildTests(unittest.TestCase):
    def test_rebuild_removes_deleted_notes_and_refreshes_existing_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = os.path.join(directory, "notes")
            dependencies = Dependencies()
            tag_index = SQLiteTagIndex(
                os.path.join(directory, "jour.db"),
                dependencies,
                sqlite3.connect,
            )
            note_store = FileSystemNoteStore(
                notes_path,
                dependencies=dependencies,
                tag_index=tag_index,
            )
            deleted_note_id = note_store.create("Deleted note", ["deleted-tag"])
            retained_note_id = note_store.create("Original note", ["old-tag"])
            os.remove(os.path.join(notes_path, f"{deleted_note_id}.jmd"))
            with open(os.path.join(notes_path, f"{retained_note_id}.jmd"), "w") as note:
                note.write("---\ntags: [new-tag]\n---\n\nUpdated note")

            rebuilt_count = note_store.rebuild_tag_index()

            self.assertEqual(rebuilt_count, 1)
            self.assertEqual(note_store.tag_counts(), [("new-tag", 1)])
            self.assertEqual(note_store.notes_for_tag("deleted-tag"), [])
            self.assertEqual(note_store.notes_for_tag("old-tag"), [])
            self.assertEqual(note_store.notes_for_tag("new-tag"), [retained_note_id])

    def test_rebuild_command_reports_rebuilt_note_count(self):
        dependencies = Mock()
        note_store = Mock()
        note_store.rebuild_tag_index.return_value = 3
        app_factory = Mock()
        app_factory.dependencies = dependencies
        app_factory.get_config.return_value = {}
        app_factory.get_note_store.return_value = note_store

        cmd_rebuild(None, app_factory)

        note_store.rebuild_tag_index.assert_called_once_with()
        dependencies.write_stdout.assert_called_once_with(
            "Rebuilt note index for 3 note(s)."
        )

    def test_deleted_note_count_compares_indexed_notes_to_note_files(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = os.path.join(directory, "notes")
            dependencies = Dependencies()
            tag_index = SQLiteTagIndex(
                os.path.join(directory, "jour.db"),
                dependencies,
                sqlite3.connect,
            )
            note_store = FileSystemNoteStore(
                notes_path,
                dependencies=dependencies,
                tag_index=tag_index,
            )
            deleted_note_id = note_store.create("Deleted note", ["deleted-tag"])
            note_store.create("Current note", ["current-tag"])
            os.remove(os.path.join(notes_path, f"{deleted_note_id}.jmd"))

            self.assertEqual(note_store.deleted_note_count(), 1)


if __name__ == "__main__":
    unittest.main()
