import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from jour_cli.app_factory import AppFactory
from jour_cli.cmd.edit import edit_note
from jour_cli.cmd.make import make_note
from jour_cli.cmd import cli
from jour_cli.shared.dependencies import Dependencies, DependenciesFactory
from jour_cli.shared.editor import Editor, get_editor
from jour_cli.shared.jmespath_query import query_notes
from jour_cli.shared.note_content import (
    _build_note_content,
    _parse_json_note_data,
)
from jour_cli.storage.note_store import Note, NoteStore
from typer.testing import CliRunner


class JsonNoteTests(unittest.TestCase):
    def setUp(self):
        self.dependencies = Mock(spec=Dependencies)
        self.dependencies.get_git_root.return_value = None
        self.dependencies.exit.side_effect = SystemExit
        self.dependencies_factory = Mock(spec=DependenciesFactory)
        self.dependencies_factory.create.return_value = self.dependencies

    def create_app_factory(self, note_store, editor=None):
        return AppFactory(
            self.dependencies_factory,
            lambda _dependencies: {"front_matter": {"layout": "default"}},
            lambda _config, _dependencies: note_store,
            lambda _config, _dependencies: editor or get_editor,
        )

    def test_builds_json_type_into_front_matter(self):
        content = _build_note_content(
            "default", "date", ["work"], '{"project": "jour"}', "json"
        )

        self.assertIn("type: json", content)
        self.assertEqual(_parse_json_note_data(content), {"project": "jour"})

    def test_json_note_requires_an_object(self):
        for body in ("[1, 2]", "null", "NaN", "{invalid}"):
            with self.subTest(body=body):
                content = _build_note_content("default", "date", [], body, "json")
                with self.assertRaises(ValueError):
                    _parse_json_note_data(content)

    def test_markdown_note_has_no_structured_data(self):
        content = _build_note_content("default", "date", [], "body")

        self.assertIsNone(_parse_json_note_data(content))

    def test_jmespath_records_include_type_and_parsed_data(self):
        content = _build_note_content(
            "default", "date", ["work"], '{"project": "jour"}', "json"
        )

        result = query_notes(
            [Note("note-id", content, ["work"])],
            "[].{type: type, project: data.project}",
        )

        self.assertEqual(json.loads(result), [{"type": "json", "project": "jour"}])

    def test_jmespath_filter_searches_across_all_json_notes(self):
        notes = [
            Note(
                "jour-note",
                _build_note_content(
                    "default", "date", [], '{"project": "jour"}', "json"
                ),
                [],
            ),
            Note(
                "other-note",
                _build_note_content(
                    "default", "date", [], '{"project": "other"}', "json"
                ),
                [],
            ),
            Note("markdown-note", "Plain text note", []),
        ]

        result = query_notes(
            notes,
            "[?data.project == 'jour'].{id: id, project: data.project}",
        )

        self.assertEqual(
            json.loads(result),
            [{"id": "jour-note", "project": "jour"}],
        )

    def test_jmespath_can_query_json_document_fields_at_record_root(self):
        note = Note(
            "contact-note",
            _build_note_content(
                "default",
                "date",
                [],
                '{\n"contact-id": 1234,\n"contact-name": "Chris Hayes"\n}',
                "json",
            ),
            [],
        )

        result = query_notes(
            [note],
            '[?"contact-id" == `1234`]."contact-name"',
        )

        self.assertEqual(json.loads(result), ["Chris Hayes"])

    def test_make_rejects_invalid_json_before_saving(self):
        note_store = Mock(spec=NoteStore)
        app_factory = self.create_app_factory(note_store)

        with self.assertRaises(SystemExit):
            make_note(
                SimpleNamespace(
                    note="{invalid}", file=None, tag=None, note_type="json"
                ),
                app_factory,
            )

        note_store.create.assert_not_called()
        self.dependencies.write_stderr.assert_called_once()
        self.dependencies.exit.assert_called_once_with(1)

    def test_cli_accepts_json_type_option(self):
        with patch.object(cli, "run_cmd") as run_cmd:
            result = CliRunner().invoke(
                cli.app,
                ["make", "--type", "json", "--note", '{"project": "jour"}'],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(run_cmd.call_args.kwargs["note_type"], "json")

    def test_make_saves_valid_json_note(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        note_store = Mock(spec=NoteStore)
        app_factory = self.create_app_factory(note_store)

        make_note(
            SimpleNamespace(
                note='{"project": "jour"}',
                file=None,
                tag="work",
                note_type="json",
            ),
            app_factory,
        )

        saved_content = note_store.create.call_args.args[0]
        self.assertIn("type: json", saved_content)
        self.assertEqual(_parse_json_note_data(saved_content), {"project": "jour"})

    def test_make_json_editor_starts_with_an_object_template(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        self.dependencies.stdin_is_interactive.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.create.return_value = "note-id"
        note_store.get.return_value = '---\ntype: json\n---\n\n{"project": "jour"}'
        editor = Mock(spec=Editor)
        app_factory = self.create_app_factory(note_store, editor=editor)

        make_note(
            SimpleNamespace(note=None, file=None, tag=None, note_type="json"),
            app_factory,
        )

        self.assertEqual(_parse_json_note_data(note_store.create.call_args.args[0]), {})
        note_store.edit.assert_called_once_with("note-id", editor)

    def test_edit_restores_existing_content_after_invalid_json(self):
        original_content = '---\ntype: json\n---\n\n{"project": "jour"}'
        note_store = Mock(spec=NoteStore)
        note_store.get.side_effect = [
            original_content,
            "---\ntype: json\n---\n\n{invalid}",
        ]
        note_store.edit.return_value = True
        note_store.update.return_value = True
        editor = Mock(spec=Editor)
        app_factory = self.create_app_factory(note_store, editor=editor)

        with self.assertRaises(SystemExit):
            edit_note(SimpleNamespace(hash="note-id"), app_factory)

        note_store.update.assert_called_once_with("note-id", original_content)
        self.dependencies.write_stderr.assert_called_once()
        self.dependencies.exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
