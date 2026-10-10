import typer
from typing import Optional
from jour_cli.notes import (
    cmd_notes_make,
    cmd_notes_list,
    cmd_notes_cat,
    cmd_notes_delete,
    cmd_notes_edit,
)
from jour_cli.tags import cmd_tags_list, cmd_tags_show
from jour_cli.search import cmd_search
from jour_cli.logging import log_command

app = typer.Typer()
notes_app = typer.Typer()
tags_app = typer.Typer()
app.add_typer(notes_app, name="notes")
app.add_typer(tags_app, name="tags")


@notes_app.command("make")
def notes_make(
    note: Optional[str] = typer.Option(None, "-n", "--note", help="Note body text"),
    tag: Optional[str] = typer.Option(None, "-t", "--tag", help="Comma-delimited tags"),
    file: Optional[str] = typer.Argument(None, help="Optional file to read note from"),
):
    """Create a new note."""
    args = type('Args', (), {'note': note, 'tag': tag, 'file': file})()
    cmd_notes_make(args=args)
    log_command("notes make", args=args)


@notes_app.command("list")
def notes_list():
    """List all notes."""
    args = type('Args', (), {})()
    cmd_notes_list(args=args)
    log_command("notes list", args=args)


@notes_app.command("cat")
def notes_cat(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """View a note by hash."""
    args = type('Args', (), {'hash': hash})()
    cmd_notes_cat(args=args)
    log_command("notes cat", args=args)


@notes_app.command("delete")
def notes_delete(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Delete a note by hash."""
    args = type('Args', (), {'hash': hash})()
    cmd_notes_delete(args=args)
    log_command("notes delete", args=args)


@notes_app.command("edit")
def notes_edit(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Edit a note by hash."""
    args = type('Args', (), {'hash': hash})()
    cmd_notes_edit(args=args)
    log_command("notes edit", args=args)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search notes."""
    args = type('Args', (), {'query': query})()
    cmd_search(args=args)
    log_command("search", args=args)


@app.command()
def history(
    count: int = typer.Option(20, "-n", "--count", help="Number of entries to show (default: 20)"),
):
    """Show command history."""
    from jour_cli.logging import read_history
    args = type('Args', (), {'count': count})()
    read_history(limit=count)
    log_command("history", args=args)


@tags_app.command("list")
def tags_list():
    """List all tags."""
    args = type('Args', (), {})()
    cmd_tags_list(args=args)
    log_command("tags list", args=args)


@tags_app.command("show")
def tags_show(
    tag: str = typer.Argument(..., help="Tag name"),
):
    """Show notes for a specific tag."""
    args = type('Args', (), {'tag': tag})()
    cmd_tags_show(args=args)
    log_command("tags show", args=args)


def main():
    app()


if __name__ == "__main__":
    main()
