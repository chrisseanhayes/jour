import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from jour_cli.cmd.search import cmd_search
from jour_cli.storage.note_store import Note


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.matching_note = Note("matching", "needle in body", ["work"])
        self.other_note = Note("other", "unrelated body", [])
        self.note_store = Mock()
        self.note_store.search.return_value = [
            "matching.jmd:1:needle in body"
        ]
        self.note_store.list.return_value = [self.matching_note, self.other_note]
        self.app_factory = Mock()
        self.app_factory.get_note_store.return_value = self.note_store

    def test_search_without_jmespath_query_keeps_formatted_matches(self):
        cmd_search(SimpleNamespace(query="needle"), self.app_factory)

        self.app_factory.dependencies.write_stdout.assert_called_once_with(
            "matching.jmd:1:needle in body"
        )
        self.note_store.list.assert_not_called()

    def test_jmespath_query_receives_notes_with_search_matches(self):
        cmd_search(
            SimpleNamespace(
                query="needle",
                jmespath_query="[].{id: id, body: body, tags: tags}",
            ),
            self.app_factory,
        )

        output = self.app_factory.dependencies.write_stdout.call_args.args[0]
        self.assertEqual(
            json.loads(output),
            [{"id": "matching", "body": "needle in body", "tags": ["work"]}],
        )


if __name__ == "__main__":
    unittest.main()
