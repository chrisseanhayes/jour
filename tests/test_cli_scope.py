import unittest
from unittest.mock import patch

from typer.testing import CliRunner

from jour_cli.cmd import cli


class CliScopeTests(unittest.TestCase):
    def test_global_flag_selects_global_scope_before_command_execution(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "set_global_mode") as set_global_mode:
            with patch.object(cli.app_factory, "log_command"):
                with patch.object(cli.app_factory, "read_history", return_value=[]):
                    result = runner.invoke(cli.app, ["-g", "history", "-n", "0"])

        self.assertEqual(result.exit_code, 0, result.output)
        set_global_mode.assert_called_once_with(True)

    def test_global_scope_is_not_selected_by_default(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "set_global_mode") as set_global_mode:
            with patch.object(cli.app_factory, "log_command"):
                with patch.object(cli.app_factory, "read_history", return_value=[]):
                    result = runner.invoke(cli.app, ["history", "-n", "0"])

        self.assertEqual(result.exit_code, 0, result.output)
        set_global_mode.assert_called_once_with(False)

    def test_init_initializes_local_journal(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "log_command"):
            with patch.object(cli.app_factory.dependencies, "write_stdout") as stdout:
                with patch.object(
                    cli.app_factory.dependencies, "write_stderr"
                ):
                    with patch.object(
                        cli.app_factory,
                        "initialize_local_journal",
                        return_value={"storage": {"path": "/repo/.jour"}},
                    ) as initialize_local_journal:
                        result = runner.invoke(cli.app, ["init"])

        self.assertEqual(result.exit_code, 0, result.exception)
        initialize_local_journal.assert_called_once_with()
        stdout.assert_called_once_with("Initialized local Jour in /repo/.jour.")

    def test_init_reports_error_when_not_in_a_git_repository(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "log_command"):
            with patch.object(cli.app_factory.dependencies, "write_stderr") as stderr:
                with patch.object(
                    cli.app_factory,
                    "initialize_local_journal",
                    side_effect=ValueError(
                        "jour init must be run inside a Git repository."
                    ),
                ):
                    result = runner.invoke(cli.app, ["init"])

        self.assertEqual(result.exit_code, 1)
        stderr.assert_called_once_with(
            "Error: jour init must be run inside a Git repository."
        )


if __name__ == "__main__":
    unittest.main()
