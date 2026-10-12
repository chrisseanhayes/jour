import glob
import os
import shlex
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Callable, Mapping, NoReturn, Optional, Protocol, TextIO

import typer


class Dependencies:
    """External runtime dependencies used by the CLI."""

    def __init__(
        self,
        clock: Optional[Callable[[], datetime]] = None,
        uuid_factory: Optional[Callable[[], uuid.UUID]] = None,
        file_opener=open,
        path_expander: Optional[Callable[[str], str]] = None,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        stderr: Optional[TextIO] = None,
        exit_process: Callable[[int], NoReturn] = sys.exit,
        platform_name: Optional[str] = None,
        environment: Optional[Mapping[str, str]] = None,
        working_directory: Optional[str] = None,
    ):
        self._os = os
        self._glob = glob
        self._shlex = shlex
        self._subprocess = subprocess
        self._clock = clock if clock is not None else datetime.now
        self._uuid_factory = uuid_factory if uuid_factory is not None else uuid.uuid4
        self._open = file_opener
        self._path_expander = (
            path_expander if path_expander is not None else os.path.expanduser
        )
        self._sys_stdin = stdin if stdin is not None else sys.stdin
        self._sys_stdout = stdout if stdout is not None else sys.stdout
        self._sys_stderr = stderr if stderr is not None else sys.stderr
        self._exit_process = exit_process
        self._platform = platform_name if platform_name is not None else sys.platform
        self._environment = environment if environment is not None else os.environ
        self._working_directory = working_directory

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

    def split_command(self, command: str) -> list:
        """Split a command string using shell-like quoting rules."""
        return self._shlex.split(command)

    def stdin_is_interactive(self) -> bool:
        """Return whether standard input is connected to a terminal."""
        return self._sys_stdin.isatty()

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

    def join(self, *args) -> str:
        """Join path components."""
        return self._os.path.join(*args)

    def splitext(self, path: str) -> tuple:
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

    def list_files(self, pattern: str, storage: str) -> list:
        """List files matching pattern in storage directory."""
        return sorted(self._glob.glob(self._os.path.join(storage, pattern)), reverse=True)

    def remove_file(self, filepath: str) -> None:
        """Remove file."""
        self._os.remove(filepath)

    def run_command(self, cmd: list, *, capture_output: bool = False):
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

    def get_history(self, limit: int = 20) -> list:
        """Get command history."""
        from jour_cli.history import read_history

        return read_history(limit=limit, dependencies=self)


class DependenciesFactory(Protocol):
    """Factory interface for creating runtime dependencies."""

    def create(self) -> Dependencies:
        """Create the dependency bundle used by an application."""


class DefaultDependenciesFactory:
    """Creates runtime dependencies backed by the host environment."""

    def create(self) -> Dependencies:
        return Dependencies()
