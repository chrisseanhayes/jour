from contextlib import contextmanager
import glob
import logging
import os
import shlex
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Any, Callable, Iterator, List, Mapping, NoReturn, Optional, Protocol, TextIO, Tuple

import typer


class IO:
    """Isolated filesystem and path I/O operations."""

    def __init__(
        self,
        file_opener: Callable = open,
        path_expander: Optional[Callable[[str], str]] = None,
        working_directory: Optional[str] = None,
        os_module: Any = os,
        glob_module: Any = glob,
    ):
        self._os = os_module
        self._glob = glob_module
        self._open = file_opener
        self._path_expander = (
            path_expander if path_expander is not None else os_module.path.expanduser
        )
        self._working_directory = working_directory

    def expanduser(self, path: str) -> str:
        """Expand ~ to user home directory."""
        return self._path_expander(path)

    def path(self, path: str) -> str:
        """Return the absolute path."""
        return self._os.path.abspath(path)

    def realpath(self, path: str) -> str:
        """Resolve symlinks and return the canonical path."""
        return self._os.path.realpath(path)

    def get_git_root(self) -> Optional[str]:
        """Find the nearest parent directory containing a Git metadata entry."""
        current = self.path(self._working_directory or self._os.getcwd())
        while True:
            if self.exists(self.join(current, ".git")):
                return current
            parent = self.dirname(current)
            if parent == current:
                return None
            current = parent

    def basename(self, path: str) -> str:
        """Get the base name of a path."""
        return self._os.path.basename(path)

    def dirname(self, path: str) -> str:
        """Get the directory name of a path."""
        return self._os.path.dirname(path)

    def makedirs(self, path: str, exist_ok: bool = True) -> None:
        """Create directory if it doesn't exist."""
        return self._os.makedirs(path, exist_ok=exist_ok)

    def exists(self, path: str) -> bool:
        """Check if file or directory exists."""
        return self._os.path.exists(path)

    def join(self, *args: str) -> str:
        """Join path components."""
        return self._os.path.join(*args)

    def splitext(self, path: str) -> Tuple[str, str]:
        """Split filename and extension."""
        return self._os.path.splitext(path)

    def read_file(self, filepath: str) -> str:
        """Read file contents."""
        with self._open(filepath, "r") as f:
            return f.read()

    def write_file(self, filepath: str, content: str) -> None:
        """Write content to file."""
        with self._open(filepath, "w") as f:
            f.write(content)

    def append_file(self, filepath: str, content: str) -> None:
        """Append content to a file."""
        with self._open(filepath, "a") as f:
            f.write(content)

    def list_files(self, pattern: str, storage: str) -> List[str]:
        """List files matching pattern in storage directory."""
        return sorted(self._glob.glob(self._os.path.join(storage, pattern)), reverse=True)

    def remove_file(self, filepath: str) -> None:
        """Remove file."""
        self._os.remove(filepath)


class SQLite:
    """Isolated SQLite database operations."""

    def __init__(
        self,
        connection_factory: Optional[Callable[[str], sqlite3.Connection]] = None,
    ):
        self._connection_factory = (
            connection_factory if connection_factory is not None else sqlite3.connect
        )

    @property
    def connection_factory(self) -> Callable[[str], sqlite3.Connection]:
        """Return the underlying connection factory callable."""
        return self._connection_factory

    def connect(self, database_path: str, **kwargs: Any) -> sqlite3.Connection:
        """Establish and return a SQLite database connection."""
        return self._connection_factory(database_path, **kwargs)

    @contextmanager
    def connection(self, database_path: str, **kwargs: Any) -> Iterator[sqlite3.Connection]:
        """Yield an open connection and close it on exit."""
        conn = self.connect(database_path, **kwargs)
        try:
            yield conn
        finally:
            conn.close()


class AdHoc:
    """Isolated ad-hoc runtime dependencies (process, clock, streams, shell, env)."""

    def __init__(
        self,
        clock: Optional[Callable[[], datetime]] = None,
        uuid_factory: Optional[Callable[[], uuid.UUID]] = None,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        stderr: Optional[TextIO] = None,
        exit_process: Callable[[int], NoReturn] = sys.exit,
        platform_name: Optional[str] = None,
        environment: Optional[Mapping[str, str]] = None,
        logger: Optional[logging.Logger] = None,
        shlex_module: Any = shlex,
        subprocess_module: Any = subprocess,
    ):
        self._clock = clock if clock is not None else datetime.now
        self._uuid_factory = uuid_factory if uuid_factory is not None else uuid.uuid4
        self._sys_stdin = stdin if stdin is not None else sys.stdin
        self._sys_stdout = stdout if stdout is not None else sys.stdout
        self._sys_stderr = stderr if stderr is not None else sys.stderr
        self._exit_process = exit_process
        self._platform = platform_name if platform_name is not None else sys.platform
        self._environment = environment if environment is not None else os.environ
        self._shlex = shlex_module
        self._subprocess = subprocess_module
        self.logger = logger if logger is not None else logging.getLogger("jour")

    def now(self) -> datetime:
        """Return the current time from the configured clock."""
        return self._clock()

    def new_uuid_hex(self) -> str:
        """Return a unique identifier from the configured UUID factory."""
        return self._uuid_factory().hex

    def get_environment_variable(self, name: str) -> Optional[str]:
        """Read an environment variable."""
        return self._environment.get(name)

    def is_macos(self) -> bool:
        """Return whether the configured runtime platform is macOS."""
        return self._platform == "darwin"

    def split_command(self, command: str) -> List[str]:
        """Split a command string using shell-like quoting rules."""
        return self._shlex.split(command)

    def stdin_is_interactive(self) -> bool:
        """Return whether standard input is connected to a terminal."""
        return self._sys_stdin.isatty()

    def run_command(self, cmd: List[str], *, capture_output: bool = False) -> Any:
        """Run a command, optionally capturing its text output."""
        if capture_output:
            return self._subprocess.run(cmd, capture_output=True, text=True)
        return self._subprocess.run(cmd)

    def stdin_read(self) -> str:
        """Read from stdin."""
        return self._sys_stdin.read()

    def write_stdout(self, text: str, end: str = "\n") -> None:
        """Write text to standard output."""
        self._sys_stdout.write(f"{text}{end}")

    def write_stderr(self, text: str, end: str = "\n") -> None:
        """Write text to standard error."""
        self._sys_stderr.write(f"{text}{end}")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """Prompt the user for confirmation."""
        return typer.confirm(prompt, default=default)

    def exit(self, code: int) -> NoReturn:
        """Terminate the process with the given exit code."""
        self._exit_process(code)

    def get_history(self, dependencies: Any, limit: int = 20) -> list:
        """Get command history."""
        from jour_cli.history import read_history

        return read_history(limit=limit, dependencies=dependencies)


class Dependencies:
    """Composite external runtime dependencies, segregating IO, SQLite, and AdHoc operations."""

    def __init__(
        self,
        io: Optional[IO] = None,
        sqlite: Optional[SQLite] = None,
        adhoc: Optional[AdHoc] = None,
        # Backwards compatibility / convenience parameters:
        clock: Optional[Callable[[], datetime]] = None,
        uuid_factory: Optional[Callable[[], uuid.UUID]] = None,
        file_opener: Callable = open,
        path_expander: Optional[Callable[[str], str]] = None,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        stderr: Optional[TextIO] = None,
        exit_process: Callable[[int], NoReturn] = sys.exit,
        platform_name: Optional[str] = None,
        environment: Optional[Mapping[str, str]] = None,
        working_directory: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        database_connection_factory: Optional[Callable[[str], sqlite3.Connection]] = None,
    ):
        self.io: IO = (
            io
            if io is not None
            else IO(
                file_opener=file_opener,
                path_expander=path_expander,
                working_directory=working_directory,
            )
        )
        self.sqlite: SQLite = (
            sqlite
            if sqlite is not None
            else SQLite(connection_factory=database_connection_factory)
        )
        self.adhoc: AdHoc = (
            adhoc
            if adhoc is not None
            else AdHoc(
                clock=clock,
                uuid_factory=uuid_factory,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                exit_process=exit_process,
                platform_name=platform_name,
                environment=environment,
                logger=logger,
            )
        )

    # --- Delegations to self.io ---

    def expanduser(self, path: str) -> str:
        """Expand ~ to user home directory."""
        return self.io.expanduser(path)

    def path(self, path: str) -> str:
        """Return the absolute path."""
        return self.io.path(path)

    def realpath(self, path: str) -> str:
        """Resolve symlinks and return the canonical path."""
        return self.io.realpath(path)

    def get_git_root(self) -> Optional[str]:
        """Find the nearest parent directory containing a Git metadata entry."""
        return self.io.get_git_root()

    def basename(self, path: str) -> str:
        """Get the base name of a path."""
        return self.io.basename(path)

    def dirname(self, path: str) -> str:
        """Get the directory name of a path."""
        return self.io.dirname(path)

    def makedirs(self, path: str, exist_ok: bool = True) -> None:
        """Create directory if it doesn't exist."""
        return self.io.makedirs(path, exist_ok=exist_ok)

    def exists(self, path: str) -> bool:
        """Check if file or directory exists."""
        return self.io.exists(path)

    def join(self, *args: str) -> str:
        """Join path components."""
        return self.io.join(*args)

    def splitext(self, path: str) -> Tuple[str, str]:
        """Split filename and extension."""
        return self.io.splitext(path)

    def read_file(self, filepath: str) -> str:
        """Read file contents."""
        return self.io.read_file(filepath)

    def write_file(self, filepath: str, content: str) -> None:
        """Write content to file."""
        return self.io.write_file(filepath, content)

    def append_file(self, filepath: str, content: str) -> None:
        """Append content to a file."""
        return self.io.append_file(filepath, content)

    def list_files(self, pattern: str, storage: str) -> List[str]:
        """List files matching pattern in storage directory."""
        return self.io.list_files(pattern, storage)

    def remove_file(self, filepath: str) -> None:
        """Remove file."""
        return self.io.remove_file(filepath)

    # --- Delegations to self.sqlite ---

    def connect_sqlite(self, database_path: str, **kwargs: Any) -> sqlite3.Connection:
        """Connect to SQLite database."""
        return self.sqlite.connect(database_path, **kwargs)

    # --- Delegations to self.adhoc ---

    def now(self) -> datetime:
        """Return the current time from the configured clock."""
        return self.adhoc.now()

    def new_uuid_hex(self) -> str:
        """Return a unique identifier from the configured UUID factory."""
        return self.adhoc.new_uuid_hex()

    def get_environment_variable(self, name: str) -> Optional[str]:
        """Read an environment variable."""
        return self.adhoc.get_environment_variable(name)

    def is_macos(self) -> bool:
        """Return whether the configured runtime platform is macOS."""
        return self.adhoc.is_macos()

    def split_command(self, command: str) -> List[str]:
        """Split a command string using shell-like quoting rules."""
        return self.adhoc.split_command(command)

    def stdin_is_interactive(self) -> bool:
        """Return whether standard input is connected to a terminal."""
        return self.adhoc.stdin_is_interactive()

    def run_command(self, cmd: List[str], *, capture_output: bool = False) -> Any:
        """Run a command, optionally capturing its text output."""
        return self.adhoc.run_command(cmd, capture_output=capture_output)

    def stdin_read(self) -> str:
        """Read from stdin."""
        return self.adhoc.stdin_read()

    def write_stdout(self, text: str, end: str = "\n") -> None:
        """Write text to standard output."""
        self.adhoc.write_stdout(text, end=end)

    def write_stderr(self, text: str, end: str = "\n") -> None:
        """Write text to standard error."""
        self.adhoc.write_stderr(text, end=end)

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """Prompt the user for confirmation."""
        return self.adhoc.confirm(prompt, default=default)

    def exit(self, code: int) -> NoReturn:
        """Terminate the process with the given exit code."""
        self.adhoc.exit(code)

    def get_history(self, limit: int = 20) -> list:
        """Get command history."""
        return self.adhoc.get_history(self, limit=limit)

    @property
    def logger(self) -> logging.Logger:
        return self.adhoc.logger

    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        self.adhoc.logger = value


class DependenciesFactory(Protocol):
    """Factory interface for creating runtime dependencies."""

    def create(self) -> Dependencies:
        """Create the dependency bundle used by an application."""


class DefaultDependenciesFactory:
    """Creates runtime dependencies backed by the host environment."""

    def __init__(
        self,
        io: Optional[IO] = None,
        sqlite: Optional[SQLite] = None,
        adhoc: Optional[AdHoc] = None,
    ):
        self._io = io
        self._sqlite = sqlite
        self._adhoc = adhoc

    def create(self) -> Dependencies:
        return Dependencies(io=self._io, sqlite=self._sqlite, adhoc=self._adhoc)
