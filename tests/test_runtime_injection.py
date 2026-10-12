import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, Mock
from uuid import UUID

from jour_cli.app_factory import AppFactory
from jour_cli.cmd.make import make_note
from jour_cli.config import StorageScope, _default_editor, load_config
from jour_cli.history import log_command, read_history
from jour_cli.shared.dependencies import Dependencies, DependenciesFactory
from jour_cli.shared.editor import Editor, get_editor
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.factory import FileSystemNoteStoreFactory, build_note_store
from jour_cli.storage.note_store import NoteStore, TagIndex
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


class RuntimeInjectionTests(unittest.TestCase):
    def dependencies_factory(self, dependencies):
        factory = Mock(spec=DependenciesFactory)
        factory.create.return_value = dependencies
        return factory

    def test_dependencies_accept_clock_uuid_stdin_platform_and_environment(self):
        timestamp = datetime(2026, 10, 10, 16, 38)
        dependencies = Dependencies(
            clock=lambda: timestamp,
            uuid_factory=lambda: UUID("12345678-1234-5678-1234-567812345678"),
            stdin=StringIO("input"),
            platform_name="darwin",
            environment={"VISUAL": "custom-editor"},
            path_expander=lambda path: path.replace("~", "/home/test", 1),
        )

        self.assertEqual(dependencies.now(), timestamp)
        self.assertEqual(dependencies.new_uuid_hex(), "12345678123456781234567812345678")
        self.assertFalse(dependencies.stdin_is_interactive())
        self.assertTrue(dependencies.is_macos())
        self.assertEqual(_default_editor(dependencies), "custom-editor")
        self.assertEqual(dependencies.expanduser("~/.jour"), "/home/test/.jour")

    def test_stdout_and_stderr_are_injected(self):
        stdout = StringIO()
        stderr = StringIO()
        dependencies = Dependencies(
            stdout=stdout,
            stderr=stderr,
        )

        dependencies.write_stdout("note contents", end="")
        dependencies.write_stderr("note not found")

        self.assertEqual(stdout.getvalue(), "note contents")
        self.assertEqual(stderr.getvalue(), "note not found\n")

    def test_process_exit_is_injected_with_status_code(self):
        exit_process = Mock(side_effect=SystemExit)
        dependencies = Dependencies(exit_process=exit_process)

        with self.assertRaises(SystemExit):
            dependencies.exit(1)

        exit_process.assert_called_once_with(1)

    def test_config_file_access_uses_injected_dependencies(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/home/test"
        dependencies.join.side_effect = os.path.join
        dependencies.exists.return_value = True
        dependencies.read_file.return_value = "storage:\n  extension: md\n"

        config = load_config(dependencies)

        self.assertEqual(config["storage"]["extension"], "md")
        self.assertEqual(config["database"]["path"], "~/.jour/jour.db")
        dependencies.makedirs.assert_called_once_with(
            "/home/test/.jour", exist_ok=True
        )
        dependencies.read_file.assert_called_once_with(
            "/home/test/.jour/.jourconfig"
        )

    def test_history_file_and_timestamp_use_injected_dependencies(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/home/test"
        dependencies.join.side_effect = os.path.join
        dependencies.now.return_value = datetime(2026, 10, 10, 16, 38, 40)
        dependencies.exists.return_value = True
        dependencies.read_file.return_value = "earlier\nlatest\n"

        log_command("tags list", dependencies=dependencies)
        history = read_history(limit=1, dependencies=dependencies)

        dependencies.append_file.assert_called_once_with(
            "/home/test/.jour/logs/history",
            "[2026-10-10 16:38:40] tags list\n",
        )
        self.assertEqual(history, ["latest"])

    def test_app_factory_injects_database_connection_factory(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/tmp/jour.db"
        dependencies.dirname.return_value = "/tmp"
        dependencies.join.side_effect = os.path.join
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection_factory = Mock(return_value=connection)
        config = {
            "storage": {"path": "/tmp/notes", "extension": "jmd"},
            "database": {"path": "/tmp/jour.db"},
        }
        app_factory = AppFactory(
            self.dependencies_factory(dependencies),
            lambda _dependencies: config,
            FileSystemNoteStoreFactory(connection_factory),
            get_editor,
        )

        app_factory.get_note_store(config)

        connection_factory.assert_called_once_with("/tmp/jour.db")
        dependencies.makedirs.assert_called_once_with("/tmp", exist_ok=True)
        connection.executescript.assert_called_once()

    def test_app_factory_resolves_location_once_until_invocation_mode_changes(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.get_git_root.return_value = None
        dependencies.expanduser.side_effect = lambda path: path.replace(
            "~", "/home/test", 1
        )
        config = {
            "storage": {"path": "~/.jour"},
            "database": {"path": "~/.jour/jour.db"},
        }
        config_loader = Mock(return_value=config)
        app_factory = AppFactory(
            self.dependencies_factory(dependencies),
            config_loader,
            lambda _config, _dependencies: Mock(spec=NoteStore),
            get_editor,
        )

        first_context = app_factory.get_location_context()
        self.assertIs(app_factory.get_location_context(), first_context)
        self.assertEqual(first_context.scope, StorageScope.GLOBAL)
        config_loader.assert_called_once_with(dependencies)

        app_factory.set_global_mode(True)
        second_context = app_factory.get_location_context()

        self.assertIsNot(second_context, first_context)
        self.assertEqual(second_context.scope, StorageScope.GLOBAL)
        self.assertEqual(config_loader.call_count, 2)

    def test_app_factory_injects_tag_index_factory(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.expanduser.return_value = "/tmp/notes"
        dependencies.join.side_effect = os.path.join
        tag_index = Mock(spec=TagIndex)
        config = {"storage": {"path": "/tmp/notes", "extension": "jmd"}}
        app_factory = AppFactory(
            self.dependencies_factory(dependencies),
            lambda _dependencies: config,
            lambda current_config, current_dependencies: build_note_store(
                current_config,
                current_dependencies,
                lambda _config, _dependencies: tag_index,
            ),
            get_editor,
        )

        note_store = app_factory.get_note_store(config)

        self.assertIs(note_store.tag_index, tag_index)
        dependencies.makedirs.assert_not_called()

    def test_filesystem_store_uses_injected_clock_uuid_and_file_operations(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.get_git_root.return_value = None
        dependencies.now.return_value = datetime(2026, 10, 10, 16, 38, 40)
        dependencies.new_uuid_hex.return_value = "12345678abcdef00"
        dependencies.join.side_effect = os.path.join
        dependencies.basename.side_effect = os.path.basename
        tag_index = Mock(spec=TagIndex)
        note_store = FileSystemNoteStore(
            "/tmp/notes",
            dependencies=dependencies,
            tag_index=tag_index,
        )

        note_id = note_store.create("body", ["tag"])

        self.assertEqual(note_id, "20261010163840_12345678")
        dependencies.makedirs.assert_called_once_with("/tmp/notes", exist_ok=True)
        dependencies.write_file.assert_called_once_with(
            "/tmp/notes/20261010163840_12345678.jmd", "body"
        )
        tag_index.index_note.assert_called_once_with(
            "/tmp/notes/20261010163840_12345678.jmd", ["tag"], {}
        )

    def test_tag_queries_refresh_hashtags_saved_after_editor_returns(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = os.path.join(directory, "notes")
            database_path = os.path.join(directory, "jour.db")
            dependencies = Dependencies()
            tag_index = SQLiteTagIndex(
                database_path,
                dependencies,
                sqlite3.connect,
            )
            note_store = FileSystemNoteStore(
                notes_path,
                dependencies=dependencies,
                tag_index=tag_index,
            )
            note_id = note_store.create("---\ntags: []\n---\n\n", [])
            note_path = os.path.join(notes_path, f"{note_id}.jmd")

            # The editor may save after notes make/edit has already returned.
            with open(note_path, "w") as note_file:
                note_file.write("---\ntags: []\n---\n\nLater #saved-tag")

            self.assertEqual(note_store.notes_for_tag("saved-tag"), [note_id])
            self.assertEqual(note_store.tag_counts(), [("saved-tag", 1)])
            self.assertEqual(note_store.list()[0].tags, ["saved-tag"])

    def test_note_list_includes_body_hashtags_from_tag_index(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = os.path.join(directory, "notes")
            database_path = os.path.join(directory, "jour.db")
            dependencies = Dependencies()
            tag_index = SQLiteTagIndex(
                database_path,
                dependencies,
                sqlite3.connect,
            )
            note_store = FileSystemNoteStore(
                notes_path,
                dependencies=dependencies,
                tag_index=tag_index,
            )
            note_id = note_store.create(
                "---\ntags:\n  - front-matter-tag\n  - another-front-matter-tag\n"
                "---\n\nBody with #body-tag",
                [],
            )

            note = note_store.list()[0]
            self.assertEqual(note.id, note_id)
            self.assertEqual(
                note.tags,
                [
                    "front-matter-tag",
                    "another-front-matter-tag",
                    "body-tag",
                ],
            )

    def test_edit_indexes_hashtags_from_saved_note_content(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = os.path.join(directory, "notes")
            database_path = os.path.join(directory, "jour.db")
            dependencies = Dependencies()
            tag_index = SQLiteTagIndex(
                database_path,
                dependencies,
                sqlite3.connect,
            )
            note_store = FileSystemNoteStore(
                notes_path,
                dependencies=dependencies,
                tag_index=tag_index,
            )
            note_id = note_store.create("---\ntags: []\n---\n\n", [])
            editor = Mock(spec=Editor)
            editor.open.side_effect = lambda filepath: dependencies.write_file(
                filepath,
                "---\ntags:\n  - edited-front-matter-tag\n"
                "  - another-edited-tag\n---\n\nEdited with #edited-tag",
            )

            self.assertTrue(note_store.edit(note_id, editor))

            self.assertEqual(
                note_store.list()[0].tags,
                [
                    "edited-front-matter-tag",
                    "another-edited-tag",
                    "edited-tag",
                ],
            )
            self.assertEqual(
                tag_index.notes_for_tag("edited-front-matter-tag"),
                [f"{note_id}.jmd"],
            )

    def test_note_creation_uses_injected_clock_and_configured_date_format(self):
        dependencies = Mock(spec=Dependencies)
        dependencies.get_git_root.return_value = None
        dependencies.now.return_value = datetime(2026, 10, 10, 16, 38, 40)
        dependencies.stdin_is_interactive.return_value = False
        note_store = Mock(spec=NoteStore)
        app_factory = AppFactory(
            self.dependencies_factory(dependencies),
            lambda _dependencies: {
                "front_matter": {
                    "layout": "daily",
                    "date_format": "%Y/%m/%d",
                }
            },
            lambda _config, _dependencies: note_store,
            get_editor,
        )

        make_note(
            type("Args", (), {"note": "body", "file": None, "tag": None})(),
            app_factory,
        )

        content = note_store.create.call_args.args[0]
        self.assertIn('title: "2026/10/10"', content)
        self.assertIn("date: 2026/10/10", content)


if __name__ == "__main__":
    unittest.main()
