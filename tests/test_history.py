import os
import unittest
from datetime import datetime
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from jour_cli.cmd import cli
from jour_cli.history import get_history_path, log_command, read_history
from jour_cli.shared.dependencies import Dependencies


class HistoryUnitTests(unittest.TestCase):
    def test_get_history_path_creates_logs_directory(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/mock/home"
        dependencies.join.side_effect = os.path.join

        path = get_history_path(dependencies)

        self.assertEqual(path, os.path.join("/mock/home", ".jour", "logs", "history"))
        dependencies.makedirs.assert_called_once_with(
            os.path.join("/mock/home", ".jour", "logs"),
            exist_ok=True,
        )

    def test_log_command_without_args_writes_timestamp_and_command(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/mock/home"
        dependencies.join.side_effect = os.path.join
        dependencies.now.return_value = datetime(2026, 10, 10, 14, 30, 0)

        log_command("notes list", dependencies=dependencies)

        dependencies.append_file.assert_called_once_with(
            os.path.join("/mock/home", ".jour", "logs", "history"),
            "[2026-10-10 14:30:00] notes list\n",
        )

    def test_log_command_with_args_formats_non_none_arguments(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/mock/home"
        dependencies.join.side_effect = os.path.join
        dependencies.now.return_value = datetime(2026, 10, 10, 14, 30, 0)

        args = SimpleNamespace(note="my note", tag="test,smoke", file=None)
        log_command("notes make", args=args, dependencies=dependencies)

        dependencies.append_file.assert_called_once_with(
            os.path.join("/mock/home", ".jour", "logs", "history"),
            "[2026-10-10 14:30:00] notes make note=my note, tag=test,smoke\n",
        )

    def test_read_history_creates_file_if_not_existing(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/mock/home"
        dependencies.join.side_effect = os.path.join
        dependencies.exists.return_value = False

        history = read_history(dependencies)

        self.assertEqual(history, [])
        dependencies.write_file.assert_called_once_with(
            os.path.join("/mock/home", ".jour", "logs", "history"), ""
        )

    def test_read_history_limits_results(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/mock/home"
        dependencies.join.side_effect = os.path.join
        dependencies.exists.return_value = True

        log_content = "\n".join([f"line {i}" for i in range(1, 31)]) + "\n"
        dependencies.read_file.return_value = log_content

        # Default limit is 20
        default_history = read_history(dependencies)
        self.assertEqual(len(default_history), 20)
        self.assertEqual(default_history[0], "line 11")
        self.assertEqual(default_history[-1], "line 30")

        # Explicit limit 1
        one_entry = read_history(dependencies, limit=1)
        self.assertEqual(one_entry, ["line 30"])

        # Explicit limit 5
        five_entries = read_history(dependencies, limit=5)
        self.assertEqual(len(five_entries), 5)
        self.assertEqual(five_entries[0], "line 26")
        self.assertEqual(five_entries[-1], "line 30")

        # Limit 0
        zero_entries = read_history(dependencies, limit=0)
        self.assertEqual(zero_entries, [])

        # Limit None (all lines)
        all_entries = read_history(dependencies, limit=None)
        self.assertEqual(len(all_entries), 30)

    def test_cli_history_command_writes_lines_to_stdout(self):
        runner = CliRunner()
        mock_lines = [
            "[2026-10-10 12:00:00] notes make",
            "[2026-10-10 12:01:00] notes list",
            "[2026-10-10 12:02:00] tags list",
        ]
        with patch.object(cli.app_factory, "log_command") as log_cmd:
            with patch.object(cli.app_factory, "read_history", return_value=mock_lines) as read_hist:
                with patch.object(cli.app_factory.dependencies, "write_stdout") as stdout:
                    result = runner.invoke(cli.app, ["history", "-n", "3"])

        self.assertEqual(result.exit_code, 0, result.output)
        log_cmd.assert_called_once()
        self.assertEqual(log_cmd.call_args.args[0], "history")
        read_hist.assert_called_once_with(limit=3)
        self.assertEqual(
            [call.args[0] for call in stdout.call_args_list],
            mock_lines,
        )

    def test_cli_history_default_limit_is_20(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "log_command"):
            with patch.object(cli.app_factory, "read_history", return_value=[]) as read_hist:
                with patch.object(cli.app_factory.dependencies, "write_stdout"):
                    result = runner.invoke(cli.app, ["history"])

        self.assertEqual(result.exit_code, 0, result.output)
        read_hist.assert_called_once_with(limit=20)


if __name__ == "__main__":
    unittest.main()
