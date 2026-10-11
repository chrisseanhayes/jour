import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.cmd.notes._list import cmd_notes_list
from jour_cli.storage.note_store import Note


class NotesListTests(unittest.TestCase):
    def setUp(self):
        self.archived_note = Note("archived", "archived body", ["jour-archive"])
        self.active_note = Note("active", "active body", ["archive"])
        self.note_store = Mock()
        self.note_store.list.return_value = [self.archived_note, self.active_note]
        self.app_factory = Mock()
        self.app_factory.get_note_store.return_value = self.note_store

    def test_archived_notes_are_hidden_by_default(self):
        cmd_notes_list(SimpleNamespace(show_archived=False), self.app_factory)

        output = [
            call.args[0]
            for call in self.app_factory.dependencies.write_stdout.call_args_list
        ]
        self.assertEqual(len(output), 1)
        self.assertIn("active", output[0])
        self.assertIn("[archive]", output[0])
        self.assertNotIn("archived body", output[0])

    def test_show_archived_includes_archived_notes(self):
        cmd_notes_list(SimpleNamespace(show_archived=True), self.app_factory)

        output = [
            call.args[0]
            for call in self.app_factory.dependencies.write_stdout.call_args_list
        ]
        self.assertEqual(len(output), 2)
        self.assertIn("archived", output[0])
        self.assertIn("active", output[1])


if __name__ == "__main__":
    unittest.main()
