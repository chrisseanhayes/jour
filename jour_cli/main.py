from typing import Any, Callable, Optional

import typer

from jour_cli.logging import log_command, read_history
from jour_cli.notes import (
    cmd_notes_cat,
    cmd_notes_delete,
    cmd_notes_edit,
    cmd_notes_list,
    cmd_notes_make,
)
from jour_cli.search import cmd_search
from jour_cli.tags import cmd_tags_list, cmd_tags_show

app = typer.Typer()
notes_app = typer.Typer()
tags_app = typer.Typer()
app.add_typer(notes_app, name="notes")
app.add_typer(tags_app, name="tags")


def run_cmd(cmd_name: str, cmd_func: Callable[..., Any], **kwargs: Any) -> Any:
    """Construct argument object, log command, and execute target function."""
    args = type('Args', (), kwargs)()
    log_command(cmd_name, args=args)
    return cmd_func(args=args)


@notes_app.command("make")
def notes_make(
    note: Optional[str] = typer.Option(None, "-n", "--note", help="Note body text"),
    tag: Optional[str] = typer.Option(None, "-t", "--tag", help="Comma-delimited tags"),
    file: Optional[str] = typer.Argument(None, help="Optional file to read note from"),
):
    """Create a new note."""
    run_cmd("notes make", cmd_notes_make, note=note, tag=tag, file=file)


@notes_app.command("list")
def notes_list():
    """List all notes."""
    run_cmd("notes list", cmd_notes_list)


@notes_app.command("cat")
def notes_cat(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """View a note by hash."""
    run_cmd("notes cat", cmd_notes_cat, hash=hash)


@notes_app.command("delete")
def notes_delete(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Delete a note by hash."""
    run_cmd("notes delete", cmd_notes_delete, hash=hash)


@notes_app.command("edit")
def notes_edit(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Edit a note by hash."""
    run_cmd("notes edit", cmd_notes_edit, hash=hash)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search notes."""
    run_cmd("search", cmd_search, query=query)


@app.command()
def history(
    count: int = typer.Option(20, "-n", "--count", help="Number of entries to show (default: 20)"),
):
    """Show command history."""
    args = type('Args', (), {'count': count})()
    log_command("history", args=args)
    read_history(limit=count)


@tags_app.command("list")
def tags_list():
    """List all tags."""
    run_cmd("tags list", cmd_tags_list)


@tags_app.command("show")
def tags_show(
    tag: str = typer.Argument(..., help="Tag name"),
):
    """Show notes for a specific tag."""
    run_cmd("tags show", cmd_tags_show, tag=tag)


def main():
    app()


if __name__ == "__main__":
    main()