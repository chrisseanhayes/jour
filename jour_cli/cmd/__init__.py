"""CLI command handlers and application wiring."""

from jour_cli.cmd.notes import (
    cmd_notes_cat,
    cmd_notes_delete,
    cmd_notes_edit,
    cmd_notes_list,
    cmd_notes_make,
)
from jour_cli.cmd.search import cmd_search
from jour_cli.cmd.tags import cmd_tags_list, cmd_tags_show

__all__ = [
    "cmd_notes_cat",
    "cmd_notes_delete",
    "cmd_notes_edit",
    "cmd_notes_list",
    "cmd_notes_make",
    "cmd_search",
    "cmd_tags_list",
    "cmd_tags_show",
]
