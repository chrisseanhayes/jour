import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.cmd.index import cmd_index_status


class IndexStatusTests(unittest.TestCase):
    def setUp(self):
        self.dependencies = Mock()
        self.note_store = Mock()
        self.note_store.deleted_note_count.return_value = 2
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_config.return_value = {}
        self.app_factory.get_note_store.return_value = self.note_store

    def test_status_reports_latest_rebuild_and_deleted_note_count(self):
        self.app_factory.read_history.return_value = [
            "[2026-10-10 09:00:00] rebuild",
            "[2026-10-10 09:01:00] tags list",
            "[2026-10-11 08:30:00] rebuild",
        ]

        cmd_index_status(SimpleNamespace(status=True), self.app_factory)

        self.app_factory.read_history.assert_called_once_with(limit=None)
        self.assertEqual(
            [call.args[0] for call in self.dependencies.write_stdout.call_args_list],
            ["Last rebuilt: 2026-10-11 08:30:00", "Deleted notes: 2"],
        )

    def test_status_reports_when_index_has_never_been_rebuilt(self):
        self.app_factory.read_history.return_value = [
            "[2026-10-11 08:30:00] tags list",
        ]

        cmd_index_status(SimpleNamespace(status=True), self.app_factory)

        self.assertEqual(
            [call.args[0] for call in self.dependencies.write_stdout.call_args_list],
            ["Last rebuilt: Never", "Deleted notes: 2"],
        )


if __name__ == "__main__":
    unittest.main()
