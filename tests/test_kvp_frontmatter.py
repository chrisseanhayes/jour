import json
import os
import sqlite3
import tempfile
import unittest

from jour_cli.shared.dependencies import Dependencies
from jour_cli.shared.jmespath_query import query_notes
from jour_cli.shared.note_content import _add_front_matter_kvp, _parse_note_kvp
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.sqlite_tag_index import SQLiteTagIndex


class KvpFrontMatterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.notes_path = os.path.join(self.temporary_directory.name, "notes")
        self.database_path = os.path.join(self.temporary_directory.name, "jour.db")
        self.dependencies = Dependencies()
        self.tag_index = SQLiteTagIndex(
            self.database_path,
            self.dependencies,
            sqlite3.connect,
        )
        self.note_store = FileSystemNoteStore(
            self.notes_path,
            dependencies=self.dependencies,
            tag_index=self.tag_index,
        )

    def test_parses_json_compatible_front_matter_mapping(self):
        content = (
            "---\nkvp:\n  name: Jour\n  count: 3\n  enabled: true\n"
            "---\n\nNote body"
        )

        self.assertEqual(
            _parse_note_kvp(content),
            {"name": "Jour", "count": 3, "enabled": True},
        )

    def test_absent_kvp_is_empty_and_invalid_kvp_is_rejected(self):
        self.assertEqual(_parse_note_kvp("Plain note"), {})
        for kvp in ("value", "{1: value}", "{key: .nan}", "{key: !!set {a: null}}"):
            with self.subTest(kvp=kvp):
                content = f"---\nkvp: {kvp}\n---\n\nNote body"
                with self.assertRaises(ValueError):
                    _parse_note_kvp(content)

    def test_add_front_matter_kvp_preserves_existing_metadata_and_body(self):
        content = (
            "---\nlayout: daily\ntags:\n  - work\nkvp:\n  existing: 3\n"
            "---\n\nNote body"
        )

        updated = _add_front_matter_kvp(content, "project", "jour")

        self.assertEqual(
            _parse_note_kvp(updated),
            {"existing": 3, "project": "jour"},
        )
        self.assertIn("layout: daily", updated)
        self.assertIn("- work", updated)
        self.assertTrue(updated.endswith("\n\nNote body"))

    def test_add_front_matter_kvp_replaces_existing_key_and_handles_plain_notes(self):
        updated = _add_front_matter_kvp(
            "---\nkvp:\n  project: old\n---\n\nNote body",
            "project",
            "jour",
        )
        self.assertEqual(_parse_note_kvp(updated), {"project": "jour"})

        plain_note = _add_front_matter_kvp("Note body", "project", "jour")
        self.assertEqual(_parse_note_kvp(plain_note), {"project": "jour"})
        self.assertTrue(plain_note.endswith("Note body"))

    def test_add_kvp_command_updates_persisted_and_queryable_metadata(self):
        from types import SimpleNamespace

        from jour_cli.cmd.add_kvp import add_kvp

        note_id = self.note_store.create("Note body", [])
        app_factory = SimpleNamespace(
            get_config=lambda: {},
            dependencies=self.dependencies,
            get_note_store=lambda _config: self.note_store,
        )

        add_kvp(
            SimpleNamespace(hash=note_id, key="project", value="jour"),
            app_factory,
        )

        note = self.note_store.list()[0]
        self.assertEqual(note.kvp, {"project": "jour"})
        self.assertEqual(
            json.loads(
                query_notes([note], "[?kvp.project == 'jour'].id")
            ),
            [note_id],
        )

    def test_kvp_is_persisted_and_exposed_to_jmespath(self):
        content = (
            "---\nkvp:\n  key1: value1\n  key2: 2\n---\n\nNote body"
        )
        note_id = self.note_store.create(content, [])

        note = self.note_store.list()[0]
        self.assertEqual(note.id, note_id)
        self.assertEqual(note.kvp, {"key1": "value1", "key2": 2})
        result = query_notes(
            [note],
            "[?kvp.key1 == 'value1'].{id: id, value: kvp.key2}",
        )
        self.assertEqual(
            json.loads(result),
            [{"id": note_id, "value": 2}],
        )

        with sqlite3.connect(self.database_path) as connection:
            rows = connection.execute(
                "SELECT key, value FROM kvp_values ORDER BY key"
            ).fetchall()
        self.assertEqual(rows, [("key1", '"value1"'), ("key2", "2")])

    def test_update_and_rebuild_refresh_persisted_kvp(self):
        note_id = self.note_store.create(
            "---\nkvp:\n  old: value\n---\n\nNote body",
            [],
        )
        updated = "---\nkvp:\n  new: 4\n---\n\nUpdated body"
        self.assertTrue(self.note_store.update(note_id, updated))
        self.assertEqual(self.note_store.list()[0].kvp, {"new": 4})

        filepath = os.path.join(self.notes_path, f"{note_id}.jmd")
        with open(filepath, "w", encoding="utf-8") as note_file:
            note_file.write("---\nkvp:\n  rebuilt: true\n---\n\nRebuilt body")
        self.note_store.rebuild_tag_index()

        self.assertEqual(self.note_store.list()[0].kvp, {"rebuilt": True})
        self.assertTrue(self.note_store.delete(note_id))
        self.assertEqual(self.tag_index.kvp_by_note(), {})

    def test_invalid_kvp_update_does_not_replace_the_note(self):
        note_id = self.note_store.create(
            "---\nkvp:\n  valid: value\n---\n\nOriginal body",
            [],
        )

        with self.assertRaises(ValueError):
            self.note_store.update(
                note_id,
                "---\nkvp: not-a-mapping\n---\n\nInvalid replacement",
            )

        self.assertEqual(
            self.note_store.get(note_id),
            "---\nkvp:\n  valid: value\n---\n\nOriginal body",
        )


if __name__ == "__main__":
    unittest.main()
