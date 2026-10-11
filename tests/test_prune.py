import unittest
from unittest.mock import Mock

from jour_cli.cmd.prune import cmd_prune
from jour_cli.storage.note_store import Note


class PruneTests(unittest.TestCase):
    def setUp(self):
        self.dependencies = Mock()
        self.note_store = Mock()
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_config.return_value = {}
        self.app_factory.get_note_store.return_value = self.note_store

    def test_prunes_all_empty_notes_and_keeps_notes_with_bodies(self):
        self.note_store.list.return_value = [
            Note("empty", "---\ntags: [tag]\n---\n\n  \n", ["tag"]),
            Note("active", "---\ntags: [tag]\n---\n\nA body", ["tag"]),
            Note("archived-empty", "---\ntags: [jour-archive]\n---\n\n", ["jour-archive"]),
        ]
        self.note_store.delete.return_value = True

        cmd_prune(None, self.app_factory)

        self.assertEqual(
            [call.args[0] for call in self.note_store.delete.call_args_list],
            ["empty", "archived-empty"],
        )
        self.dependencies.write_stdout.assert_called_once_with(
            "Pruned 2 empty note(s)."
        )

    def test_reports_when_no_empty_notes_exist(self):
        self.note_store.list.return_value = [Note("active", "A body", [])]

        cmd_prune(None, self.app_factory)

        self.note_store.delete.assert_not_called()
        self.dependencies.write_stdout.assert_called_once_with(
            "No empty notes found."
        )

    def test_reports_deletion_failures_and_continues_pruning(self):
        self.note_store.list.return_value = [
            Note("failed", "---\n---\n\n", []),
            Note("deleted", "", []),
        ]
        self.note_store.delete.side_effect = [False, True]

        cmd_prune(None, self.app_factory)

        self.assertEqual(self.note_store.delete.call_count, 2)
        self.dependencies.write_stderr.assert_called_once_with(
            "Error: Empty note failed could not be deleted."
        )
        self.dependencies.exit.assert_called_once_with(1)
        self.dependencies.write_stdout.assert_not_called()


if __name__ == "__main__":
    unittest.main()
