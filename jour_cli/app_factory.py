from typing import Any, Callable, Dict

from jour_cli.history import log_command, read_history
from jour_cli.shared.dependencies import Dependencies, DependenciesFactory
from jour_cli.shared.editor import Editor
from jour_cli.storage.factory import NoteStoreFactory
from jour_cli.storage.note_store import NoteStore


Config = Dict[str, Any]
ConfigLoader = Callable[[Dependencies], Config]
EditorFactory = Callable[[Config, Dependencies], Editor]


class AppFactory:
    """Creates and provides the services used by command handlers."""

    def __init__(
        self,
        dependencies_factory: DependenciesFactory,
        config_loader: ConfigLoader,
        note_store_factory: NoteStoreFactory,
        editor_factory: EditorFactory,
    ):
        self.dependencies = dependencies_factory.create()
        self._config_loader = config_loader
        self._note_store_factory = note_store_factory
        self._editor_factory = editor_factory

    def get_config(self) -> Config:
        return self._config_loader(self.dependencies)

    def get_note_store(self, config: Config) -> NoteStore:
        return self._note_store_factory(config, self.dependencies)

    def get_editor(self, config: Config) -> Editor:
        return self._editor_factory(config, self.dependencies)

    def log_command(self, command: str, args=None) -> None:
        log_command(command, args=args, dependencies=self.dependencies)

    def read_history(self, limit: int = 20) -> list:
        return read_history(dependencies=self.dependencies, limit=limit)
