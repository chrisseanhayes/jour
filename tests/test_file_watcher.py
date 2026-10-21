import os
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml

from jour_cli.cmd.watch import cmd_watch
from jour_cli.shared.dependencies import Dependencies
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.note_watcher import GlobalNoteWatcher
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


class FileWatcherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.notes_path = os.path.join(self.directory.name, "notes")
        self.database_path = os.path.join(self.directory.name, "jour.db")
        self.logger = Mock()
        self.dependencies = Dependencies(logger=self.logger)
        self.tag_index = SQLiteTagIndex(
            self.database_path, self.dependencies, sqlite3.connect
        )
        self.note_store = FileSystemNoteStore(
            self.notes_path,
            dependencies=self.dependencies,
            tag_index=self.tag_index,
        )

    def test_pending_changes_are_durable_and_revision_safe(self):
        filepath = os.path.join(self.notes_path, "note.jmd")
        self.tag_index.enqueue_note_change(filepath)
        first_revision = self.tag_index.pending_note_changes()[0][1]
        self.tag_index.enqueue_note_change(filepath)

        reopened_index = SQLiteTagIndex(
            self.database_path, self.dependencies, sqlite3.connect
        )
        pending = reopened_index.pending_note_changes()
        self.assertEqual(pending, [(filepath, first_revision + 1)])

        reopened_index.complete_note_change(filepath, first_revision)
        self.assertEqual(reopened_index.pending_note_changes(), pending)
        reopened_index.complete_note_change(filepath, first_revision + 1)
        self.assertEqual(reopened_index.pending_note_changes(), [])

    def test_restart_processes_a_change_left_in_the_durable_queue(self):
        os.makedirs(self.notes_path, exist_ok=True)
        filepath = os.path.join(self.notes_path, "external-note.jmd")
        with open(filepath, "w") as note_file:
            note_file.write("---\ntags: [recovered-tag]\n---\n\nRecovered note")
        self.tag_index.enqueue_note_change(filepath)

        reopened_index = SQLiteTagIndex(
            self.database_path, self.dependencies, sqlite3.connect
        )
        reopened_store = FileSystemNoteStore(
            self.notes_path,
            dependencies=self.dependencies,
            tag_index=reopened_index,
        )
        GlobalNoteWatcher(reopened_store).process_pending_changes()

        self.assertEqual(
            reopened_store.notes_for_tag("recovered-tag"), ["external-note"]
        )
        self.assertEqual(reopened_index.pending_note_changes(), [])

    def test_watcher_waits_until_the_note_is_quiet_before_indexing(self):
        os.makedirs(self.notes_path, exist_ok=True)
        filepath = os.path.join(self.notes_path, "debounced-note.jmd")
        with open(filepath, "w") as note_file:
            note_file.write("---\ntags: [debounced-tag]\n---\n\nDebounced note")
        self.tag_index.enqueue_note_change(filepath)
        watcher = GlobalNoteWatcher(self.note_store)

        watcher.process_pending_changes(debounce_seconds=3600)
        self.assertEqual(self.tag_index.notes_for_tag("debounced-tag"), [])
        self.assertEqual(len(self.tag_index.pending_note_changes()), 1)

        watcher.process_pending_changes()
        self.assertEqual(
            self.note_store.notes_for_tag("debounced-tag"), ["debounced-note"]
        )
        self.assertEqual(self.tag_index.pending_note_changes(), [])
        self.assertTrue(
            any(
                call.args[0] == "Processing queued note change: %s"
                for call in self.logger.info.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.args[0] == "Indexed note: %s"
                for call in self.logger.info.call_args_list
            )
        )

    def test_reconcile_and_process_index_changes_and_deletions(self):
        deleted_id = self.note_store.create("Old note", ["deleted-tag"])
        retained_id = self.note_store.create("Old content", ["old-tag"])
        deleted_path = os.path.join(self.notes_path, f"{deleted_id}.jmd")
        retained_path = os.path.join(self.notes_path, f"{retained_id}.jmd")
        os.remove(deleted_path)
        with open(retained_path, "w") as note_file:
            note_file.write("---\ntags: [new-tag]\n---\n\nUpdated note")
        new_path = os.path.join(self.notes_path, "external-note.jmd")
        with open(new_path, "w") as note_file:
            note_file.write("---\ntags: [external-tag]\n---\n\nExternal note")

        watcher = GlobalNoteWatcher(self.note_store)
        watcher.reconcile()
        watcher.process_pending_changes()

        self.assertEqual(self.note_store.notes_for_tag("deleted-tag"), [])
        self.assertEqual(self.note_store.notes_for_tag("old-tag"), [])
        self.assertEqual(self.note_store.notes_for_tag("new-tag"), [retained_id])
        self.assertEqual(
            self.note_store.notes_for_tag("external-tag"), ["external-note"]
        )
        self.assertEqual(self.tag_index.pending_note_changes(), [])

    def test_failed_processing_keeps_change_queued(self):
        filepath = os.path.join(self.notes_path, "broken.jmd")
        os.makedirs(self.notes_path, exist_ok=True)
        with open(filepath, "w") as note_file:
            note_file.write("---\ntags: [broken\n---\n")
        self.tag_index.enqueue_note_change(filepath)

        with self.assertRaises(yaml.YAMLError):
            GlobalNoteWatcher(self.note_store).process_pending_changes()

        self.assertEqual(
            [item[0] for item in self.tag_index.pending_note_changes()], [filepath]
        )
        self.logger.exception.assert_called_once_with(
            "Failed to process queued note change: %s", filepath
        )

    def test_watch_command_forces_global_scope_and_starts_watcher(self):
        app_factory = Mock()
        app_factory.get_config.return_value = {}
        note_store = Mock(spec=FileSystemNoteStore)
        note_store.storage = "/home/test/.jour"
        app_factory.get_note_store.return_value = note_store
        with patch("jour_cli.cmd.watch.GlobalNoteWatcher") as watcher_class:
            watcher_class.return_value.run.side_effect = KeyboardInterrupt

            cmd_watch(None, app_factory)

        app_factory.set_global_mode.assert_called_once_with(True)
        watcher_class.assert_called_once_with(note_store)
        watcher_class.return_value.run.assert_called_once_with()
        app_factory.dependencies.write_stdout.assert_any_call(
            "Stopped watching global Jour notes."
        )


if __name__ == "__main__":
    unittest.main()
