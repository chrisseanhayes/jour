import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from jour_cli.app_factory import AppFactory
from jour_cli.cmd import cli
from jour_cli.cmd.make import make_note
from jour_cli.cmd.tags import cmd_tags_list, cmd_tags_show
from jour_cli.shared.dependencies import Dependencies
from jour_cli.shared.editor import get_editor
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


class TagsHandlerTests(unittest.TestCase):
    def setUp(self):
        self.note_store = Mock()
        self.dependencies = Mock()
        self.dependencies.exit.side_effect = SystemExit
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_config.return_value = {"storage": {"extension": "jmd"}}
        self.app_factory.get_note_store.return_value = self.note_store

    def test_cmd_tags_list_writes_formatted_tags_and_counts(self):
        self.note_store.tag_counts.return_value = [
            ("cnt_multi", 3),
            ("cnt_single", 1),
        ]

        cmd_tags_list(SimpleNamespace(), self.app_factory)

        self.assertEqual(
            [call.args[0] for call in self.dependencies.write_stdout.call_args_list],
            ["cnt_multi: 3", "cnt_single: 1"],
        )

    def test_cmd_tags_show_writes_matching_note_ids(self):
        self.note_store.notes_for_tag.return_value = [
            "20261021120000_11111111",
            "20261021120100_22222222",
        ]

        cmd_tags_show(SimpleNamespace(tag="shared_tag"), self.app_factory)

        self.note_store.notes_for_tag.assert_called_once_with("shared_tag")
        self.assertEqual(
            [call.args[0] for call in self.dependencies.write_stdout.call_args_list],
            ["20261021120000_11111111", "20261021120100_22222222"],
        )

    def test_cmd_tags_show_outputs_nothing_for_empty_results(self):
        self.note_store.notes_for_tag.return_value = []

        cmd_tags_show(SimpleNamespace(tag="nonexistent"), self.app_factory)

        self.note_store.notes_for_tag.assert_called_once_with("nonexistent")
        self.dependencies.write_stdout.assert_not_called()

    def test_cli_tags_list_invokes_run_cmd(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            result = runner.invoke(cli.app, ["tags", "list"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_cmd.assert_called_once_with(("tags", "list"), cmd_tags_list)

    def test_cli_tags_show_invokes_run_cmd(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            result = runner.invoke(cli.app, ["tags", "show", "project"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_cmd.assert_called_once_with(
            ("tags", "show"),
            cmd_tags_show,
            positional=("tag",),
            tag="project",
        )


class TagStorageIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.notes_path = os.path.join(self.temp_dir.name, "notes")
        self.database_path = os.path.join(self.temp_dir.name, "jour.db")
        self.dependencies = Dependencies()
        self.tag_index = SQLiteTagIndex(
            self.database_path,
            self.dependencies,
            sqlite3.connect,
        )
        self.note_store = FileSystemNoteStore(
            self.notes_path,
            dependencies=self.dependencies,
            tag_index=self.tag_index,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_note_single_tag_count(self):
        self.note_store.create(
            "---\ntags:\n  - cnt_single\n---\n\ncount test one",
            ["cnt_single"],
        )
        self.assertEqual(self.note_store.tag_counts(), [("cnt_single", 1)])

    def test_tag_count_increments_across_multiple_notes(self):
        self.note_store.create(
            "---\ntags:\n  - cnt_multi\n---\n\ncount test two",
            ["cnt_multi"],
        )
        self.note_store.create(
            "---\ntags:\n  - cnt_multi\n---\n\ncount test three",
            ["cnt_multi"],
        )
        self.note_store.create(
            "---\ntags:\n  - cnt_multi\n---\n\ncount test four",
            ["cnt_multi"],
        )
        self.assertEqual(self.note_store.tag_counts(), [("cnt_multi", 3)])

    def test_tags_show_returns_filename_for_tag(self):
        note_id = self.note_store.create(
            "---\ntags:\n  - show_test\n---\n\nshow test note",
            ["show_test"],
        )
        self.assertEqual(self.note_store.notes_for_tag("show_test"), [note_id])

    def test_tags_show_returns_multiple_notes_for_shared_tag(self):
        note1 = self.note_store.create(
            "---\ntags:\n  - shared_tag\n---\n\nshared note one",
            ["shared_tag"],
        )
        note2 = self.note_store.create(
            "---\ntags:\n  - shared_tag\n---\n\nshared note two",
            ["shared_tag"],
        )
        notes = self.note_store.notes_for_tag("shared_tag")
        self.assertEqual(len(notes), 2)
        self.assertIn(note1, notes)
        self.assertIn(note2, notes)

    def test_tags_show_empty_for_nonexistent_tag(self):
        notes = self.note_store.notes_for_tag("__tag_that_does_not_exist__")
        self.assertEqual(notes, [])

    def test_multiple_tags_on_one_note_each_queryable(self):
        note_id = self.note_store.create(
            "---\ntags:\n  - mt_alpha\n  - mt_beta\n  - mt_gamma\n---\n\nmulti tag note",
            ["mt_alpha", "mt_beta", "mt_gamma"],
        )
        self.assertEqual(self.note_store.notes_for_tag("mt_alpha"), [note_id])
        self.assertEqual(self.note_store.notes_for_tag("mt_beta"), [note_id])
        self.assertEqual(self.note_store.notes_for_tag("mt_gamma"), [note_id])

    def test_untagged_note_does_not_pollute_tag_index(self):
        self.note_store.create("no tags here", [])
        self.assertEqual(self.note_store.tag_counts(), [])
        self.assertEqual(
            self.note_store.notes_for_tag("__tag_that_does_not_exist__"), []
        )

    def test_tags_list_orders_by_count_descending(self):
        # 3 notes with cnt_multi, 1 note with cnt_single
        for i in range(3):
            self.note_store.create(
                f"---\ntags:\n  - cnt_multi\n---\n\nnote {i}",
                ["cnt_multi"],
            )
        self.note_store.create(
            "---\ntags:\n  - cnt_single\n---\n\nsingle note",
            ["cnt_single"],
        )

        counts = self.note_store.tag_counts()
        self.assertEqual(counts[0], ("cnt_multi", 3))
        self.assertEqual(counts[1], ("cnt_single", 1))

    def test_tag_whitespace_normalized_on_creation(self):
        config = {
            "storage": {"path": self.notes_path, "extension": "jmd"},
            "database": {"path": self.database_path},
        }
        app_factory = AppFactory(
            Mock(create=lambda: self.dependencies),
            lambda _deps: config,
            lambda _cfg, _deps: self.note_store,
            get_editor,
        )
        args = SimpleNamespace(
            note="whitespace tag note",
            tag="  ws_tag  ",
            file=None,
            note_type="markdown",
        )
        make_note(args, app_factory)

        self.assertEqual(len(self.note_store.notes_for_tag("ws_tag")), 1)
        self.assertEqual(self.note_store.tag_counts(), [("ws_tag", 1)])

    def test_index_note_is_idempotent_no_duplicates(self):
        note_id = self.note_store.create(
            "---\ntags:\n  - idem_tag\n---\n\nidempotent note",
            ["idem_tag"],
        )
        note_path = os.path.join(self.notes_path, f"{note_id}.jmd")

        # Re-index the same note
        self.tag_index.index_note(note_path, ["idem_tag"])

        self.assertEqual(self.note_store.tag_counts(), [("idem_tag", 1)])
        self.assertEqual(self.note_store.notes_for_tag("idem_tag"), [note_id])


if __name__ == "__main__":
    unittest.main()
