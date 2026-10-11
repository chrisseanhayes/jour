from abc import ABC, abstractmethod
from typing import List

from jour_cli.config import _default_editor
from jour_cli.shared.dependencies import Dependencies


class Editor(ABC):
    """Interface for opening a note in an editor."""

    @abstractmethod
    def open(self, filepath: str) -> None:
        """Open the given note path for editing."""


class CommandEditor(Editor):
    """Editor that launches a configured command with the note path."""

    def __init__(self, command: List[str], dependencies: Dependencies):
        if not command:
            raise ValueError("Editor command must not be empty.")
        self.command = command
        self.dependencies = dependencies

    def open(self, filepath: str) -> None:
        self.dependencies.run_command(self.command + [filepath])


def get_editor(
    config: dict,
    dependencies: Dependencies,
) -> Editor:
    """Build an editor from configuration and environment defaults."""
    command = config.get("editor", {}).get("command") or _default_editor(dependencies)
    if isinstance(command, str):
        command = dependencies.split_command(command)
    elif not isinstance(command, list) or not all(
        isinstance(part, str) for part in command
    ):
        raise ValueError("Editor command must be a string or a list of strings.")
    return CommandEditor(command, dependencies)
