import unittest
from importlib.metadata import version as package_version
from unittest.mock import patch

from typer.testing import CliRunner

from jour_cli.cmd import cli


class CliScopeTests(unittest.TestCase):
    def test_version_option_displays_installed_version_without_configuring_app(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "set_global_mode") as set_global_mode:
            result = runner.invoke(cli.app, ["--version"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.output.strip(), f"jour {package_version('jour-cli')}")
        set_global_mode.assert_not_called()

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

    def test_rebuild_command_is_registered(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "log_command"):
            with patch.object(cli.app_factory, "get_config", return_value={}):
                with patch.object(cli.app_factory, "get_note_store") as get_note_store:
                    with patch.object(
                        cli.app_factory.dependencies, "write_stdout"
                    ) as stdout:
                        note_store = get_note_store.return_value
                        note_store.rebuild_tag_index.return_value = 0
                        result = runner.invoke(cli.app, ["rebuild"])

        self.assertEqual(result.exit_code, 0, result.output)
        note_store.rebuild_tag_index.assert_called_once_with()
        stdout.assert_called_once_with("Rebuilt note index for 0 note(s).")

    def test_index_status_command_is_registered(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "log_command"):
            with patch.object(cli.app_factory, "get_config", return_value={}):
                with patch.object(cli.app_factory, "get_note_store") as get_note_store:
                    get_note_store.return_value.deleted_note_count.return_value = 0
                    with patch.object(
                        cli.app_factory, "read_history", return_value=[]
                    ):
                        with patch.object(
                            cli.app_factory.dependencies, "write_stdout"
                        ) as stdout:
                            result = runner.invoke(cli.app, ["index", "--status"])

        self.assertEqual(result.exit_code, 0, result.output)
        get_note_store.return_value.deleted_note_count.assert_called_once_with()
        self.assertEqual(
            [call.args[0] for call in stdout.call_args_list],
            ["Last rebuilt: Never", "Deleted notes: 0"],
        )

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
