import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from jour_cli.cmd import cli
from jour_cli.cmd.cat import cat_note


class CatNoteTests(unittest.TestCase):
    def setUp(self):
        self.note_store = Mock()
        self.dependencies = Mock()
        self.dependencies.exit.side_effect = SystemExit
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_config.return_value = {"storage": {"extension": "jmd"}}
        self.app_factory.get_note_store.return_value = self.note_store

    def test_cat_existing_note_writes_content_to_stdout(self):
        note_content = "---\ntags:\n  - cattest\n---\n\ncat test body 1"
        self.note_store.get.return_value = note_content

        cat_note(SimpleNamespace(hash="note-hash-1"), self.app_factory)

        self.note_store.get.assert_called_once_with("note-hash-1")
        self.dependencies.write_stdout.assert_called_once_with(
            note_content, end=""
        )
        self.dependencies.write_stderr.assert_not_called()
        self.dependencies.exit.assert_not_called()

    def test_cat_missing_note_writes_error_and_exits(self):
        self.note_store.get.return_value = None

        with self.assertRaises(SystemExit):
            cat_note(SimpleNamespace(hash="invalid_hash_12345"), self.app_factory)

        self.note_store.get.assert_called_once_with("invalid_hash_12345")
        self.dependencies.write_stdout.assert_not_called()
        self.dependencies.write_stderr.assert_any_call(
            "Error: Note invalid_hash_12345 not found."
        )
        self.dependencies.write_stderr.assert_any_call(
            "Hint: If this note was deleted outside Jour, run `jour rebuild` to "
            "refresh the note index."
        )
        self.dependencies.exit.assert_called_once_with(1)

    def test_cli_notes_cat_success(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            result = runner.invoke(cli.app, ["notes", "cat", "abc12345"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_cmd.assert_called_once_with(
            ("notes", "cat"),
            cat_note,
            positional=("hash",),
            hash="abc12345",
        )

    def test_cli_cat_alias_success(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            result = runner.invoke(cli.app, ["cat", "abc12345"])

        self.assertEqual(result.exit_code, 0, result.output)
        run_cmd.assert_called_once_with(
            ("notes", "cat"),
            cat_note,
            positional=("hash",),
            hash="abc12345",
        )


if __name__ == "__main__":
    unittest.main()
