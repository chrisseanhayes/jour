import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.cmd.notes._archive import cmd_notes_archive
from jour_cli.shared.note_content import (
    _add_front_matter_tag,
    _parse_note_content,
)


class NotesArchiveTests(unittest.TestCase):
    def setUp(self):
        self.note_store = Mock()
        self.dependencies = Mock()
        self.dependencies.exit.side_effect = SystemExit
        self.app_factory = Mock()
        self.app_factory.dependencies = self.dependencies
        self.app_factory.get_note_store.return_value = self.note_store

    def test_archive_adds_tag_and_preserves_existing_metadata(self):
        original_content = (
            "---\nlayout: journal\ntags:\n- personal\ntitle: Entry\n---\n\nNote body\n"
        )
        self.note_store.get.return_value = original_content
        self.note_store.update.return_value = True

        cmd_notes_archive(SimpleNamespace(hash="note-id"), self.app_factory)

        self.note_store.update.assert_called_once()
        note_id, archived_content = self.note_store.update.call_args.args
        self.assertEqual(note_id, "note-id")
        self.assertIn("layout: journal", archived_content)
        self.assertIn("title: Entry", archived_content)
        self.assertEqual(
            _parse_note_content(archived_content),
            (["personal", "jour-archive"], "Note body"),
        )
        self.dependencies.write_stdout.assert_called_once_with(
            "Note note-id archived."
        )

    def test_archive_adds_front_matter_when_note_has_none(self):
        archived = _add_front_matter_tag("Plain note body\n", "jour-archive")

        self.assertEqual(
            _parse_note_content(archived),
            (["jour-archive"], "Plain note body"),
        )

    def test_archive_of_already_archived_note_is_idempotent(self):
        self.note_store.get.return_value = (
            "---\ntags:\n- jour-archive\n---\n\nNote body"
        )

        cmd_notes_archive(SimpleNamespace(hash="note-id"), self.app_factory)

        self.note_store.update.assert_not_called()
        self.dependencies.write_stdout.assert_called_once_with(
            "Note note-id archived."
        )

    def test_archive_reports_failed_update(self):
        self.note_store.get.return_value = "Plain note body"
        self.note_store.update.return_value = False

        with self.assertRaises(SystemExit):
            cmd_notes_archive(SimpleNamespace(hash="note-id"), self.app_factory)

        self.dependencies.write_stderr.assert_called_once_with(
            "Error: Note note-id could not be archived."
        )
        self.dependencies.exit.assert_called_once_with(1)

    def test_undo_removes_archive_tag_and_preserves_other_tags(self):
        original_content = (
            "---\nlayout: journal\ntags:\n- personal\n- jour-archive\n"
            "title: Entry\n---\n\nNote body\n"
        )
        self.note_store.get.return_value = original_content
        self.note_store.update.return_value = True

        cmd_notes_archive(
            SimpleNamespace(hash="note-id", undo=True), self.app_factory
        )

        self.note_store.update.assert_called_once()
        note_id, updated_content = self.note_store.update.call_args.args
        self.assertEqual(note_id, "note-id")
        self.assertIn("layout: journal", updated_content)
        self.assertIn("title: Entry", updated_content)
        self.assertEqual(
            _parse_note_content(updated_content),
            (["personal"], "Note body"),
        )
        self.dependencies.write_stdout.assert_called_once_with(
            "Note note-id unarchived."
        )

    def test_undo_without_archive_tag_is_idempotent(self):
        self.note_store.get.return_value = "---\ntags:\n- personal\n---\n\nNote body"

        cmd_notes_archive(
            SimpleNamespace(hash="note-id", undo=True), self.app_factory
        )

        self.note_store.update.assert_not_called()
        self.dependencies.write_stdout.assert_called_once_with(
            "Note note-id unarchived."
        )

    def test_archive_reports_missing_note(self):
        self.note_store.get.return_value = None

        with self.assertRaises(SystemExit):
            cmd_notes_archive(SimpleNamespace(hash="missing"), self.app_factory)

        self.dependencies.write_stderr.assert_called_once_with(
            "Error: Note missing not found."
        )
        self.dependencies.exit.assert_called_once_with(1)
        self.note_store.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
