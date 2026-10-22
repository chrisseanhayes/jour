import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from jour_cli.cmd import cli
from jour_cli.cmd.delete import delete_note
from jour_cli.shared.dependencies import Dependencies
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


class DeleteNoteTests(unittest.TestCase):
    def setUp(self):
        self.note_store = Mock()
        self.dependencies = Mock()
        self.dependencies.exit.side_effect = SystemExit
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_config.return_value = {"storage": {"extension": "jmd"}}
        self.app_factory.get_note_store.return_value = self.note_store

    def test_delete_existing_note_writes_success_message(self):
        self.note_store.delete.return_value = True

        delete_note(SimpleNamespace(hash="note-hash-1"), self.app_factory)

        self.note_store.delete.assert_called_once_with("note-hash-1")
        self.dependencies.write_stdout.assert_called_once_with(
            "Note note-hash-1 deleted."
        )
        self.dependencies.write_stderr.assert_not_called()
        self.dependencies.exit.assert_not_called()

    def test_delete_missing_note_writes_error_and_exits(self):
        self.note_store.delete.return_value = False

        with self.assertRaises(SystemExit):
            delete_note(SimpleNamespace(hash="invalid_hash_12345"), self.app_factory)

        self.note_store.delete.assert_called_once_with("invalid_hash_12345")
        self.dependencies.write_stdout.assert_not_called()
        self.dependencies.write_stderr.assert_called_once_with(
            "Error: Note invalid_hash_12345 not found."
        )
        self.dependencies.exit.assert_called_once_with(1)

    def test_delete_removes_file_and_cleans_tag_index(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = os.path.join(directory, "notes")
            database_path = os.path.join(directory, "jour.db")
            dependencies = Dependencies()
            tag_index = SQLiteTagIndex(
                database_path,
                dependencies,
                sqlite3.connect,
            )
            note_store = FileSystemNoteStore(
                notes_path,
                dependencies=dependencies,
                tag_index=tag_index,
            )

            # Create note with tags
            note_id = note_store.create(
                "---\ntags:\n  - deletetag\n---\n\ndelete test body 1",
                ["deletetag"],
            )
            note_file = os.path.join(notes_path, f"{note_id}.jmd")
            self.assertTrue(os.path.exists(note_file))
            self.assertEqual(note_store.notes_for_tag("deletetag"), [note_id])
            self.assertEqual(note_store.tag_counts(), [("deletetag", 1)])

            # Perform delete
            deleted = note_store.delete(note_id)
            self.assertTrue(deleted)

            # File is removed from disk
            self.assertFalse(os.path.exists(note_file))

            # Note is no longer retrieved
            self.assertIsNone(note_store.get(note_id))

            # Tag is removed from index
            self.assertEqual(note_store.notes_for_tag("deletetag"), [])
            self.assertEqual(note_store.tag_counts(), [])

            # Deleting again returns False
            self.assertFalse(note_store.delete(note_id))

    def test_cli_notes_delete_invokes_run_cmd(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            result = runner.invoke(cli.app, ["notes", "delete", "abc12345"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_cmd.assert_called_once_with(
            ("notes", "delete"),
            delete_note,
            positional=("hash",),
            hash="abc12345",
        )

    def test_cli_delete_alias_invokes_run_cmd(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            result = runner.invoke(cli.app, ["delete", "abc12345"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_cmd.assert_called_once_with(
            ("notes", "delete"),
            delete_note,
            positional=("hash",),
            hash="abc12345",
        )


if __name__ == "__main__":
    unittest.main()
