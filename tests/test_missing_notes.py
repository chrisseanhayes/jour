import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.cmd.cat import cat_note
from jour_cli.cmd.edit import edit_note


REBUILD_HINT = (
    "Hint: If this note was deleted outside Jour, run `jour rebuild` to "
    "refresh the tag index."
)


class MissingNoteTests(unittest.TestCase):
    def setUp(self):
        self.dependencies = Mock()
        self.dependencies.exit.side_effect = SystemExit
        self.note_store = Mock()
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_config.return_value = {}
        self.app_factory.get_note_store.return_value = self.note_store

    def test_cat_reports_rebuild_hint_for_missing_note(self):
        self.note_store.get.return_value = None

        with self.assertRaises(SystemExit):
            cat_note(SimpleNamespace(hash="missing"), self.app_factory)

        self.assertEqual(
            [call.args[0] for call in self.dependencies.write_stderr.call_args_list],
            ["Error: Note missing not found.", REBUILD_HINT],
        )
        self.dependencies.exit.assert_called_once_with(1)

    def test_edit_reports_rebuild_hint_for_missing_note(self):
        self.note_store.get.return_value = None
        self.note_store.edit.return_value = False

        with self.assertRaises(SystemExit):
            edit_note(SimpleNamespace(hash="missing"), self.app_factory)

        self.assertEqual(
            [call.args[0] for call in self.dependencies.write_stderr.call_args_list],
            ["Error: Note with hash missing not found.", REBUILD_HINT],
        )
        self.dependencies.exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
