from dataclasses import dataclass
from importlib.metadata import version as package_version
import sqlite3
from types import MappingProxyType, SimpleNamespace
from typing import Any, Callable, Mapping, Optional, Tuple

import typer

from jour_cli.app_factory import AppFactory
from jour_cli.config import load_config
from jour_cli.shared.dependencies import DefaultDependenciesFactory
from jour_cli.shared.editor import get_editor
from jour_cli.storage.factory import FileSystemNoteStoreFactory
from jour_cli.cmd.archive import archive_note
from jour_cli.cmd.add_kvp import add_kvp
from jour_cli.cmd.cat import cat_note
from jour_cli.cmd.delete import delete_note
from jour_cli.cmd.edit import edit_note
from jour_cli.cmd.init import init_local_journal
from jour_cli.cmd.list import list_notes
from jour_cli.cmd.make import make_note
from jour_cli.cmd.tags import cmd_tags_list, cmd_tags_show
from jour_cli.cmd.prune import cmd_prune
from jour_cli.cmd.rebuild import cmd_rebuild
from jour_cli.cmd.index import cmd_index_status
from jour_cli.cmd.git import cmd_git_commit, cmd_git_init
from jour_cli.cmd.watch import cmd_watch

app = typer.Typer()
notes_app = typer.Typer()
tags_app = typer.Typer()
git_app = typer.Typer()
app_factory = AppFactory(
    DefaultDependenciesFactory(),
    load_config,
    FileSystemNoteStoreFactory(sqlite3.connect),
    get_editor,
)
app.add_typer(notes_app, name="notes")
app.add_typer(tags_app, name="tags")
app.add_typer(git_app, name="git")


@dataclass(frozen=True)
class CommandState:
    """Normalized command path, positional values, and options for one invocation."""

    path: Tuple[str, ...]
    positional_arguments: Mapping[str, Any]
    options: Mapping[str, Any]

    @classmethod
    def from_arguments(
        cls,
        path: Tuple[str, ...],
        arguments: Mapping[str, Any],
        positional_names: Tuple[str, ...] = (),
    ) -> "CommandState":
        positional = {
            name: arguments[name] for name in positional_names if name in arguments
        }
        options = {
            name: value for name, value in arguments.items() if name not in positional
        }
        return cls(
            path=path,
            positional_arguments=MappingProxyType(positional),
            options=MappingProxyType(options),
        )

    @property
    def name(self) -> str:
        return " ".join(self.path)

    def to_args(self) -> SimpleNamespace:
        return SimpleNamespace(**self.positional_arguments, **self.options)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"jour {package_version('jour-cli')}")
        raise typer.Exit()


@app.callback()
def configure_app(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit",
    ),
    global_mode: bool = typer.Option(
        False, "-g", "--global", help="Use the global journal instead of repo-local data"
    ),
):
    """Configure Jour's storage scope."""
    app_factory.set_global_mode(global_mode)


def run_cmd(
    command_path: Tuple[str, ...],
    cmd_func: Callable[..., Any],
    *,
    positional: Tuple[str, ...] = (),
    **arguments: Any,
) -> Any:
    """Construct argument object, log command, and execute target function."""
    command_state = CommandState.from_arguments(
        command_path, arguments, positional_names=positional
    )
    args = command_state.to_args()
    app_factory.log_command(command_state.name, args=args)
    return cmd_func(args=args, app_factory=app_factory)


@notes_app.command("make")
def notes_make(
    note: Optional[str] = typer.Option(None, "-n", "--note", help="Note body text"),
    tag: Optional[str] = typer.Option(None, "-t", "--tag", help="Comma-delimited tags"),
    file: Optional[str] = typer.Argument(None, help="Optional file to read note from"),
    note_type: str = typer.Option(
        "markdown",
        "--type",
        help="Registered note format (built-in: markdown, json)",
    ),
):
    """Create a new note."""
    run_cmd(
        ("notes", "make"),
        make_note,
        positional=("file",),
        note=note,
        tag=tag,
        file=file,
        note_type=note_type,
    )


@notes_app.command("list")
def notes_list(
    show_archived: bool = typer.Option(
        False, "--show-archived", help="Include notes tagged 'jour-archive'"
    ),
    jmespath_query: Optional[str] = typer.Option(
        None, "-q", "--query", help="Apply a JMESPath query and output JSON"
    ),
):
    """List notes, excluding those tagged 'jour-archive' by default."""
    run_cmd(
        ("notes", "list"),
        list_notes,
        show_archived=show_archived,
        jmespath_query=jmespath_query,
    )


@notes_app.command("archive")
def notes_archive(
    hash: str = typer.Argument(..., help="Note hash"),
    undo: bool = typer.Option(
        False, "--undo", help="Remove the 'jour-archive' tag from the note"
    ),
):
    """Archive a note, or use --undo to remove its archive tag."""
    run_cmd(
        ("notes", "archive"),
        archive_note,
        positional=("hash",),
        hash=hash,
        undo=undo,
    )


@notes_app.command("cat")
def notes_cat(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """View a note by hash."""
    run_cmd(("notes", "cat"), cat_note, positional=("hash",), hash=hash)


@notes_app.command("delete")
def notes_delete(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Delete a note by hash."""
    run_cmd(("notes", "delete"), delete_note, positional=("hash",), hash=hash)


@notes_app.command("edit")
def notes_edit(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Edit a note by hash."""
    run_cmd(("notes", "edit"), edit_note, positional=("hash",), hash=hash)


@app.command("add-kvp")
def add_note_kvp(
    key: str = typer.Option(..., "-k", "--key", help="KVP key"),
    value: str = typer.Option(..., "-v", "--value", help="KVP value"),
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Add or replace a string key/value pair on a note."""
    run_cmd(
        ("add-kvp",),
        add_kvp,
        positional=("hash",),
        key=key,
        value=value,
        hash=hash,
    )


# Keep the original grouped commands available while exposing the common
# note operations directly at the top level.
app.command("make")(notes_make)
app.command("list")(notes_list)
app.command("archive")(notes_archive)
app.command("cat")(notes_cat)
app.command("delete")(notes_delete)
app.command("edit")(notes_edit)


@app.command()
def init():
    """Initialize repo-local Jour storage in the current Git repository."""
    run_cmd(("init",), init_local_journal)


@git_app.command("init")
def git_init():
    """Initialize Git tracking for the active Jour note files."""
    run_cmd(("git", "init"), cmd_git_init)


@git_app.command("commit")
def git_commit(
    message: str = typer.Option(
        "Update notes", "-m", "--message", help="Commit message"
    ),
):
    """Commit changes to Jour note files only."""
    run_cmd(("git", "commit"), cmd_git_commit, message=message)


@app.command()
def history(
    count: int = typer.Option(20, "-n", "--count", help="Number of entries to show (default: 20)"),
):
    """Show command history."""
    command_state = CommandState.from_arguments(
        ("history",), {"count": count}
    )
    app_factory.log_command(command_state.name, args=command_state.to_args())
    lines = app_factory.read_history(limit=count)
    for line in lines:
        app_factory.dependencies.write_stdout(line)


@app.command()
def prune():
    """Delete all notes with empty bodies."""
    run_cmd(("prune",), cmd_prune)


@app.command()
def rebuild():
    """Rebuild the note index from the current notes."""
    run_cmd(("rebuild",), cmd_rebuild)


@app.command()
def watch():
    """Watch global notes and keep their metadata index up to date."""
    run_cmd(("watch",), cmd_watch)


@app.command()
def index(
    status: bool = typer.Option(
        False, "--status", help="Show the last rebuild time and deleted note count"
    ),
):
    """Inspect the note index."""
    if not status:
        raise typer.BadParameter("Use --status to inspect the index.")
    run_cmd(("index",), cmd_index_status, status=status)


@tags_app.command("list")
def tags_list():
    """List all tags."""
    run_cmd(("tags", "list"), cmd_tags_list)


@tags_app.command("show")
def tags_show(
    tag: str = typer.Argument(..., help="Tag name"),
):
    """Show notes for a specific tag."""
    run_cmd(("tags", "show"), cmd_tags_show, positional=("tag",), tag=tag)


def main():
    app()


if __name__ == "__main__":
    main()
