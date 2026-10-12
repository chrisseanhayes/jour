import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.cmd.list import list_notes
from jour_cli.shared.note_formats import create_default_note_formats
from jour_cli.storage.note_store import Note


class NotesListTests(unittest.TestCase):
    def setUp(self):
        self.archived_note = Note("archived", "archived body", ["jour-archive"])
        self.active_note = Note("active", "active body", ["archive"])
        self.note_store = Mock()
        self.note_store.list.return_value = [self.archived_note, self.active_note]
        self.app_factory = Mock()
        self.app_factory.note_formats = create_default_note_formats()
        self.app_factory.get_note_store.return_value = self.note_store

    def test_archived_notes_are_hidden_by_default(self):
        list_notes(SimpleNamespace(show_archived=False), self.app_factory)

        output = [
            call.args[0]
            for call in self.app_factory.dependencies.write_stdout.call_args_list
        ]
        self.assertEqual(len(output), 1)
        self.assertIn("active", output[0])
        self.assertIn("[archive]", output[0])
        self.assertNotIn("archived body", output[0])

    def test_show_archived_includes_archived_notes(self):
        list_notes(SimpleNamespace(show_archived=True), self.app_factory)

        output = [
            call.args[0]
            for call in self.app_factory.dependencies.write_stdout.call_args_list
        ]
        self.assertEqual(len(output), 2)
        self.assertIn("archived", output[0])
        self.assertIn("active", output[1])

    def test_jmespath_query_receives_visible_structured_notes(self):
        list_notes(
            SimpleNamespace(
                show_archived=False,
                jmespath_query="[?contains(body, 'active')].{id: id, tags: tags}",
            ),
            self.app_factory,
        )

        output = self.app_factory.dependencies.write_stdout.call_args.args[0]
        self.assertEqual(json.loads(output), [{"id": "active", "tags": ["archive"]}])

    def test_invalid_jmespath_query_reports_error_without_traceback(self):
        self.app_factory.dependencies.exit.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            list_notes(
                SimpleNamespace(
                    show_archived=False,
                    jmespath_query="[?unknown-function(body)]",
                ),
                self.app_factory,
            )

        self.app_factory.dependencies.write_stdout.assert_not_called()
        error = self.app_factory.dependencies.write_stderr.call_args.args[0]
        self.assertIn("Error: Invalid JMESPath query:", error)
        self.assertNotIn("Traceback", error)
        self.app_factory.dependencies.exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
