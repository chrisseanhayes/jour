import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.app_factory import AppFactory
from jour_cli.cmd.notes._edit import cmd_notes_edit
from jour_cli.cmd.notes._make import cmd_notes_make
from jour_cli.shared.dependencies import Dependencies
from jour_cli.shared.dependencies import DependenciesFactory
from jour_cli.shared.editor import CommandEditor, Editor, get_editor
from jour_cli.shared.note_content import (
    _extract_hashtags,
    _has_note_body,
    _parse_note_content,
)
from jour_cli.shared.note_input import _resolve_note_input
from jour_cli.storage import NoteStore


class ResolveNoteInputTests(unittest.TestCase):
    def setUp(self):
        self.dependencies = Mock(spec=Dependencies)
        self.dependencies_factory = Mock(spec=DependenciesFactory)
        self.dependencies_factory.create.return_value = self.dependencies
        self.dependencies.stdin_is_interactive.return_value = False
        self.dependencies.split_command.side_effect = lambda command: [command]

    def test_extract_hashtags_matches_whole_words_and_hyphenated_tags(self):
        self.assertEqual(
            _extract_hashtags(
                "Use (#helloworld), #this-great-day and #code! "
                "not embedded#no or ##heading or #two--parts."
            ),
            ["helloworld", "this-great-day", "code"],
        )

    def test_parse_note_content_includes_body_hashtags_with_front_matter_tags(self):
        content = """---
tags: ['existing']
---

Body with #new-tag and #existing.
"""

        tags, body = _parse_note_content(content)

        self.assertEqual(tags, ["existing", "new-tag"])
        self.assertIn("#new-tag", body)

    def test_front_matter_does_not_count_as_note_body(self):
        self.assertFalse(_has_note_body("---\ntags: ['tag']\n---\n\n  \n"))
        self.assertTrue(_has_note_body("---\ntags: ['tag']\n---\n\nBody"))

    def create_app_factory(self, config, note_store, editor_factory=None):
        return AppFactory(
            self.dependencies_factory,
            lambda _dependencies: config,
            lambda _config, _dependencies: note_store,
            editor_factory or get_editor,
        )

    def test_explicit_empty_note_does_not_request_editor_or_read_stdin(self):
        self.dependencies.stdin_is_interactive.return_value = True

        result = _resolve_note_input(
            SimpleNamespace(note="", file=None),
            self.dependencies,
        )

        self.assertEqual(result, ("", False))
        self.dependencies.stdin_is_interactive.assert_not_called()
        self.dependencies.stdin_read.assert_not_called()

    def test_empty_file_does_not_request_editor(self):
        self.dependencies.read_file.return_value = ""
        self.dependencies.stdin_is_interactive.return_value = True

        result = _resolve_note_input(
            SimpleNamespace(note=None, file="empty.txt"),
            self.dependencies,
        )

        self.assertEqual(result, ("", False))
        self.dependencies.read_file.assert_called_once_with("empty.txt")
        self.dependencies.stdin_is_interactive.assert_not_called()

    def test_missing_input_on_interactive_stdin_requests_editor(self):
        self.dependencies.stdin_is_interactive.return_value = True

        result = _resolve_note_input(
            SimpleNamespace(note=None, file=None),
            self.dependencies,
        )

        self.assertEqual(result, ("", True))
        self.dependencies.stdin_is_interactive.assert_called_once_with()
        self.dependencies.stdin_read.assert_not_called()

    def test_empty_piped_stdin_does_not_request_editor(self):
        self.dependencies.stdin_is_interactive.return_value = False
        self.dependencies.stdin_read.return_value = ""

        result = _resolve_note_input(
            SimpleNamespace(note=None, file=None),
            self.dependencies,
        )

        self.assertEqual(result, ("", False))
        self.dependencies.stdin_read.assert_called_once_with()

    def test_command_editor_passes_command_arguments_and_note_path(self):
        editor_dependencies = Mock(spec=Dependencies)
        editor = CommandEditor(
            ["editor", "--wait"],
            editor_dependencies,
        )

        editor.open("/notes/note-id.jmd")

        editor_dependencies.run_command.assert_called_once_with(
            ["editor", "--wait", "/notes/note-id.jmd"]
        )

    def test_make_with_explicit_empty_note_does_not_launch_editor(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        self.dependencies.stdin_is_interactive.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.create.return_value = "note-id"
        app_factory = self.create_app_factory(
            {"front_matter": {"layout": "default"}},
            note_store,
        )

        cmd_notes_make(
            SimpleNamespace(note="", file=None, tag=None),
            app_factory,
        )

        note_store.edit.assert_not_called()

    def test_make_with_empty_value_does_not_save_and_reports_no_note(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        note_store = Mock(spec=NoteStore)
        app_factory = self.create_app_factory(
            {"front_matter": {"layout": "default"}},
            note_store,
        )

        cmd_notes_make(
            SimpleNamespace(note=" \n ", file=None, tag="tag"),
            app_factory,
        )

        note_store.create.assert_not_called()
        self.dependencies.write_stdout.assert_called_once_with("No note created.")

    def test_make_deletes_editor_output_with_empty_body(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        self.dependencies.stdin_is_interactive.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.create.return_value = "note-id"
        note_store.get.return_value = "---\ntags: ['tag']\n---\n\n"
        note_store.delete.return_value = True
        editor = Mock(spec=Editor)
        app_factory = self.create_app_factory(
            {"front_matter": {"layout": "default"}},
            note_store,
            editor_factory=lambda _config, _dependencies: editor,
        )

        cmd_notes_make(
            SimpleNamespace(note=None, file=None, tag=None),
            app_factory,
        )

        note_store.edit.assert_called_once()
        note_store.delete.assert_called_once_with("note-id")
        self.dependencies.write_stdout.assert_called_once_with("No note created.")

    def test_make_without_input_launches_configured_editor(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        self.dependencies.stdin_is_interactive.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.create.return_value = "note-id"
        note_store.get.return_value = "---\n---\n\nA note"
        app_factory = self.create_app_factory(
            {
                "front_matter": {"layout": "default"},
                "editor": {"command": "configured-editor"},
            },
            note_store,
        )

        cmd_notes_make(
            SimpleNamespace(note=None, file=None, tag=None),
            app_factory,
        )

        args, _ = note_store.edit.call_args
        self.assertEqual(args[0], "note-id")
        self.assertIsInstance(args[1], CommandEditor)
        self.assertEqual(args[1].command, ["configured-editor"])

    def test_make_uses_injected_editor(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        self.dependencies.stdin_is_interactive.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.create.return_value = "note-id"
        note_store.get.return_value = "---\n---\n\nA note"
        editor = Mock(spec=Editor)
        app_factory = self.create_app_factory(
            {"front_matter": {"layout": "default"}},
            note_store,
            editor_factory=lambda _config, _dependencies: editor,
        )

        cmd_notes_make(
            SimpleNamespace(note=None, file=None, tag=None),
            app_factory,
        )

        note_store.edit.assert_called_once_with("note-id", editor)

    def test_editing_to_empty_confirms_and_deletes_note(self):
        self.dependencies.confirm.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.get.side_effect = [
            "---\ntags: ['tag']\n---\n\nOriginal body",
            "---\ntags: ['tag']\n---\n\n",
        ]
        note_store.edit.return_value = True
        note_store.delete.return_value = True
        app_factory = self.create_app_factory(
            {},
            note_store,
            editor_factory=lambda _config, _dependencies: Mock(spec=Editor),
        )

        cmd_notes_edit(SimpleNamespace(hash="note-id"), app_factory)

        self.dependencies.confirm.assert_called_once_with(
            "Note note-id is empty. Delete it?", default=False
        )
        note_store.delete.assert_called_once_with("note-id")
        note_store.update.assert_not_called()
        self.dependencies.write_stdout.assert_called_once_with(
            "Note note-id deleted."
        )

    def test_declining_empty_note_deletion_restores_previous_content(self):
        self.dependencies.confirm.return_value = False
        note_store = Mock(spec=NoteStore)
        original_content = "---\ntags: ['tag']\n---\n\nOriginal body"
        note_store.get.side_effect = [
            original_content,
            "---\ntags: ['tag']\n---\n\n",
        ]
        note_store.edit.return_value = True
        app_factory = self.create_app_factory(
            {},
            note_store,
            editor_factory=lambda _config, _dependencies: Mock(spec=Editor),
        )

        cmd_notes_edit(SimpleNamespace(hash="note-id"), app_factory)

        note_store.delete.assert_not_called()
        note_store.update.assert_called_once_with("note-id", original_content)

    def test_make_indexes_hashtags_in_note_body(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        note_store = Mock(spec=NoteStore)
        app_factory = self.create_app_factory(
            {"front_matter": {"layout": "default"}},
            note_store,
        )

        cmd_notes_make(
            SimpleNamespace(
                note="Use #helloworld, #this-great-day and #code!",
                file=None,
                tag="manual",
            ),
            app_factory,
        )

        self.assertEqual(
            note_store.create.call_args.args[1],
            ["manual", "helloworld", "this-great-day", "code"],
        )


if __name__ == "__main__":
    unittest.main()
