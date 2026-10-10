import typer
from datetime import datetime
from typing import Optional, List
from jour_cli.notes import cmd_notes_make, cmd_notes_list, cmd_notes_cat, cmd_notes_delete, cmd_notes_edit
from jour_cli.tags import cmd_tags_list, cmd_tags_show
from jour_cli.search import cmd_search
from jour_cli.logging import log_command, read_history

app = typer.Typer(help="Minimal CLI Journal")

@app.command()
def notes(
    ctx: typer.Context,
):
    """Manage journal notes."""
    pass

@app.command("notes", "make")
def notes_make(
    note: Optional[str] = typer.Option(None, "-n", "--note", help="Note body text"),
    tag: Optional[str] = typer.Option(None, "-t", "--tag", help="Comma-delimited tags"),
    file: Optional[str] = typer.Argument(None, help="Optional file to read note from"),
):
    """Create a new note."""
    args = type('Args', (), {
        'note': note,
        'tag': tag,
        'file': file
    })()
    log_command("notes make", args)
    cmd_notes_make(args)

@app.command("notes", "list")
def notes_list():
    """List all notes."""
    args = type('Args', (), {})()
    log_command("notes list", args)
    cmd_notes_list(args)

@app.command("notes", "cat")
def notes_cat(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """View a note by hash."""
    args = type('Args', (), {'hash': hash})()
    log_command("notes cat", args)
    cmd_notes_cat(args)

@app.command("notes", "delete")
def notes_delete(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Delete a note by hash."""
    args = type('Args', (), {'hash': hash})()
    log_command("notes delete", args)
    cmd_notes_delete(args)

@app.command("notes", "edit")
def notes_edit(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Edit a note by hash."""
    args = type('Args', (), {'hash': hash})()
    log_command("notes edit", args)
    cmd_notes_edit(args)

@app.command()
def tags(
    ctx: typer.Context,
):
    """Manage tags."""
    pass

@app.command("tags", "list")
def tags_list():
    """List all tags."""
    args = type('Args', (), {})()
    log_command("tags list", args)
    cmd_tags_list(args)

@app.command("tags", "show")
def tags_show(
    tag: str = typer.Argument(..., help="Tag name"),
):
    """Show a specific tag."""
    args = type('Args', (), {'tag': tag})()
    log_command("tags show", args)
    cmd_tags_show(args)

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search notes."""
    args = type('Args', (), {'query': query})()
    log_command("search", args)
    cmd_search(args)

@app.command()
def history(
    count: int = typer.Option(20, "-n", "--count", help="Number of entries to show (default: 20)"),
):
    """Show command history."""
    history_entries = read_history(count)
    for entry in history_entries:
        print(entry)

if __name__ == "__main__":
    app()
