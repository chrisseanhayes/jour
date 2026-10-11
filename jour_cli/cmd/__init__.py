"""CLI command handlers and application wiring."""

from jour_cli.cmd.archive import archive_note
from jour_cli.cmd.cat import cat_note
from jour_cli.cmd.delete import delete_note
from jour_cli.cmd.edit import edit_note
from jour_cli.cmd.list import list_notes
from jour_cli.cmd.make import make_note
from jour_cli.cmd.tags import cmd_tags_list, cmd_tags_show

__all__ = [
    "archive_note",
    "cat_note",
    "delete_note",
    "edit_note",
    "list_notes",
    "make_note",
    "cmd_tags_list",
    "cmd_tags_show",
]
