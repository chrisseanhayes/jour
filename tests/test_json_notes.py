import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from jour_cli import NoteFormat, NoteFormatRegistry, create_default_note_formats
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
from jour_cli.shared.note_document import NoteDocument
from jour_cli.shared.note_lifecycle import NoteLifecycle, NoteLifecycleState
from jour_cli.storage.note_store import Note, NoteStore
from typer.testing import CliRunner


class JsonNoteTests(unittest.TestCase):
    def test_format_extension_api_is_exported_from_package(self):
        class TextNoteFormat:
            name = "text"

            def parse_body(self, body):
                return body

        registry = create_default_note_formats()
        self.assertIsInstance(registry, NoteFormatRegistry)
        registry.register(TextNoteFormat())
        self.assertEqual(registry.validate("text", "hello"), "hello")
        self.assertTrue(hasattr(NoteFormat, "parse_body"))

    def setUp(self):
        self.dependencies = Mock(spec=Dependencies)
        self.dependencies.get_git_root.return_value = None
        self.dependencies.exit.side_effect = SystemExit
        self.dependencies_factory = Mock(spec=DependenciesFactory)
        self.dependencies_factory.create.return_value = self.dependencies

    def create_app_factory(self, note_store, editor=None, note_formats=None):
        return AppFactory(
            self.dependencies_factory,
            lambda _dependencies: {"front_matter": {"layout": "default"}},
            lambda _config, _dependencies: note_store,
            lambda _config, _dependencies: editor or get_editor,
            note_formats=note_formats,
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

    def test_note_document_parses_common_and_type_specific_state(self):
        content = (
            "---\ntype: json\ntags:\n- work\nkvp:\n  project: jour\n"
            "custom-field: preserved\n---\n\n{\"active\": true}"
        )

        document = NoteDocument.from_content(content)

        self.assertEqual(document.note_type, "json")
        self.assertEqual(document.front_matter["custom-field"], "preserved")
        self.assertEqual(document.tags, ["work"])
        self.assertEqual(document.kvp, {"project": "jour"})
        self.assertEqual(document.body, '{"active": true}')
        self.assertEqual(document.validate_body(), {"active": True})
        self.assertEqual(document.content, content)

    def test_note_document_metadata_transitions_preserve_other_fields(self):
        content = "---\nlayout: daily\ncustom-field: retained\n---\n\nBody"
        document = NoteDocument.from_content(content)

        archived = document.add_tag("jour-archive")
        updated = archived.set_kvp("project", "jour")
        restored = updated.remove_tag("jour-archive")

        self.assertEqual(restored.tags, [])
        self.assertEqual(restored.kvp, {"project": "jour"})
        self.assertIn("layout: daily", restored.content)
        self.assertIn("custom-field: retained", restored.content)
        self.assertTrue(restored.content.endswith("\n\nBody"))

    def test_note_lifecycle_enforces_draft_validation_and_save_transitions(self):
        draft = NoteLifecycle.draft(
            _build_note_content("default", "date", [], '{"ok": true}', "json")
        )
        validated = draft.validate()
        saved = validated.mark_saved()

        self.assertEqual(draft.state, NoteLifecycleState.DRAFT)
        self.assertEqual(validated.state, NoteLifecycleState.VALIDATED)
        self.assertEqual(saved.state, NoteLifecycleState.SAVED)
        self.assertEqual(validated.document.validate_body(), {"ok": True})
        with self.assertRaisesRegex(ValueError, "expected draft"):
            saved.validate()

    def test_note_lifecycle_rejects_invalid_drafts_and_allows_discard(self):
        rejected = NoteLifecycle.draft(
            _build_note_content("default", "date", [], "{invalid}", "json")
        ).validate()
        discarded = rejected.discard()

        self.assertEqual(rejected.state, NoteLifecycleState.REJECTED)
        self.assertIsNotNone(rejected.error)
        self.assertEqual(discarded.state, NoteLifecycleState.DISCARDED)
        with self.assertRaisesRegex(ValueError, "Cannot discard"):
            discarded.discard()

    def test_registered_custom_format_validates_and_exposes_structured_data(self):
        class KeyValueNoteFormat:
            name = "pairs"

            def parse_body(self, body):
                key, value = body.split("=", 1)
                return {key: value}

        formats = create_default_note_formats()
        formats.register(KeyValueNoteFormat())
        content = _build_note_content(
            "default", "date", [], "project=jour", "pairs"
        )
        lifecycle = NoteLifecycle.draft(content).validate(formats)

        self.assertEqual(lifecycle.state, NoteLifecycleState.VALIDATED)
        self.assertEqual(lifecycle.document.validate_body(formats), {"project": "jour"})
        result = query_notes(
            [Note("note-id", content, [])],
            "[].data.project",
            formats,
        )
        self.assertEqual(json.loads(result), ["jour"])

    def test_custom_format_can_expose_non_object_structured_data(self):
        class ListNoteFormat:
            name = "items"

            def parse_body(self, body):
                return body.split(",")

        formats = create_default_note_formats()
        formats.register(ListNoteFormat())
        content = _build_note_content("default", "date", [], "one,two", "items")

        result = query_notes([Note("note-id", content, [])], "[].data[0]", formats)

        self.assertEqual(json.loads(result), ["one"])

    def test_format_registry_rejects_non_json_serializable_parser_results(self):
        class InvalidNoteFormat:
            name = "invalid"

            def parse_body(self, body):
                return {"not-json": object()}

        formats = create_default_note_formats()
        formats.register(InvalidNoteFormat())
        content = _build_note_content("default", "date", [], "body", "invalid")

        with self.assertRaisesRegex(ValueError, "not JSON-serializable"):
            NoteDocument.from_content(content).validate_body(formats)

    def test_default_note_format_registries_are_independent(self):
        class CustomNoteFormat:
            name = "custom"

            def parse_body(self, body):
                return body

        first = create_default_note_formats()
        second = create_default_note_formats()
        first.register(CustomNoteFormat())

        self.assertEqual(first.validate("custom", "body"), "body")
        with self.assertRaisesRegex(ValueError, "Unsupported note type: custom"):
            second.validate("custom", "body")

    def test_unregistered_note_type_is_rejected_for_validation(self):
        content = _build_note_content("default", "date", [], "body", "custom")

        lifecycle = NoteLifecycle.draft(content).validate()

        self.assertEqual(lifecycle.state, NoteLifecycleState.REJECTED)
        self.assertEqual(lifecycle.error, "Unsupported note type: custom")

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

    def test_cli_accepts_a_registered_format_name_as_type(self):
        with patch.object(cli, "run_cmd") as run_cmd:
            result = CliRunner().invoke(
                cli.app,
                ["make", "--type", "pairs", "--note", "project=jour"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(run_cmd.call_args.kwargs["note_type"], "pairs")

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

    def test_make_accepts_registered_custom_format(self):
        class KeyValueNoteFormat:
            name = "pairs"

            def parse_body(self, body):
                key, value = body.split("=", 1)
                return {key: value}

        self.dependencies.now.return_value.strftime.return_value = "date"
        note_store = Mock(spec=NoteStore)
        formats = create_default_note_formats()
        formats.register(KeyValueNoteFormat())
        app_factory = self.create_app_factory(note_store, note_formats=formats)

        make_note(
            SimpleNamespace(
                note="project=jour",
                file=None,
                tag=None,
                note_type="pairs",
            ),
            app_factory,
        )

        note_store.create.assert_called_once()

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

    def test_make_rejects_and_removes_invalid_json_after_editor(self):
        self.dependencies.now.return_value.strftime.return_value = "date"
        self.dependencies.stdin_is_interactive.return_value = True
        note_store = Mock(spec=NoteStore)
        note_store.create.return_value = "note-id"
        note_store.get.return_value = "---\ntype: json\n---\n\n{invalid}"
        note_store.delete.return_value = True
        app_factory = self.create_app_factory(note_store, editor=Mock(spec=Editor))

        with self.assertRaises(SystemExit):
            make_note(
                SimpleNamespace(note=None, file=None, tag=None, note_type="json"),
                app_factory,
            )

        note_store.delete.assert_called_once_with("note-id")
        self.dependencies.exit.assert_called_once_with(1)

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
