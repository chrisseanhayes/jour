import unittest
from importlib.metadata import version as package_version
from unittest.mock import patch

from typer.testing import CliRunner

from jour_cli.cmd import cli
from jour_cli.cmd.cli import CommandState


class CliScopeTests(unittest.TestCase):
    def test_command_aliases_normalize_to_same_invocation(self):
        runner = CliRunner()
        with patch.object(cli, "run_cmd") as run_cmd:
            direct = runner.invoke(cli.app, ["make", "--note", "hello"])
            grouped = runner.invoke(cli.app, ["notes", "make", "--note", "hello"])

        self.assertEqual(direct.exit_code, 0, direct.output)
        self.assertEqual(grouped.exit_code, 0, grouped.output)
        self.assertEqual(run_cmd.call_args_list[0], run_cmd.call_args_list[1])
        self.assertEqual(run_cmd.call_args_list[0].args[0], ("notes", "make"))

    def test_command_state_exposes_parsed_arguments(self):
        state = CommandState.from_arguments(("history",), {"count": 5})

        self.assertEqual(state.name, "history")
        self.assertEqual(state.path, ("history",))
        self.assertEqual(state.positional_arguments, {})
        self.assertEqual(state.options, {"count": 5})
        self.assertEqual(state.to_args().count, 5)

    def test_command_state_separates_positionals_and_options(self):
        state = CommandState.from_arguments(
            ("notes", "archive"),
            {"hash": "note-id", "undo": True},
            positional_names=("hash",),
        )

        self.assertEqual(state.name, "notes archive")
        self.assertEqual(state.positional_arguments, {"hash": "note-id"})
        self.assertEqual(state.options, {"undo": True})
        self.assertEqual(state.to_args().hash, "note-id")
        self.assertTrue(state.to_args().undo)

    def test_cli_command_state_marks_file_as_positional_and_type_as_option(self):
        with patch.object(cli, "run_cmd") as run_cmd:
            result = CliRunner().invoke(
                cli.app,
                ["make", "--type", "json", "notes.json"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(run_cmd.call_args.args[0], ("notes", "make"))
        self.assertEqual(run_cmd.call_args.kwargs["positional"], ("file",))
        self.assertEqual(run_cmd.call_args.kwargs["file"], "notes.json")
        self.assertEqual(run_cmd.call_args.kwargs["note_type"], "json")

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

    def test_global_mode_is_supported_for_git_commands(self):
        runner = CliRunner()
        for command, handler in (
            (["-g", "git", "init"], "cmd_git_init"),
            (["-g", "git", "commit"], "cmd_git_commit"),
        ):
            with self.subTest(command=command):
                with patch.object(
                    cli.app_factory, "set_global_mode"
                ) as set_global_mode:
                    with patch.object(cli.app_factory, "log_command"):
                        with patch.object(cli, handler) as command_handler:
                            result = runner.invoke(cli.app, command)

                self.assertEqual(result.exit_code, 0, result.output)
                set_global_mode.assert_called_once_with(True)
                command_handler.assert_called_once()

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

    def test_add_kvp_command_is_registered(self):
        runner = CliRunner()
        with patch.object(cli.app_factory, "log_command"):
            with patch.object(cli, "add_kvp") as add_kvp:
                result = runner.invoke(
                    cli.app,
                    ["add-kvp", "-k", "project", "-v", "jour", "note-id"],
                )

        self.assertEqual(result.exit_code, 0, result.output)
        add_kvp.assert_called_once()
        args = add_kvp.call_args.kwargs["args"]
        self.assertEqual(args.key, "project")
        self.assertEqual(args.value, "jour")
        self.assertEqual(args.hash, "note-id")

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
