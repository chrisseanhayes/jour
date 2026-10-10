import os
import ast
import sys
import glob
import shlex
import subprocess
import uuid
from datetime import datetime


class FileOperations:
    """Interface for file operations with dependency injection."""
    
    def __init__(self):
        self._os = os
        self._glob = glob
        self._shlex = shlex
        self._subprocess = subprocess
        self._uuid = uuid
        self._datetime = datetime
        self._open = open
        self._sys_stdin = sys.stdin
    
    def expanduser(self, path: str) -> str:
        """Expand ~ to user home directory."""
        return self._os.path.expanduser(path)

    def path(self, path: str) -> str:
        """Return the absolute path."""
        return self._os.path.abspath(path)
    
    def basename(self, path: str) -> str:
        """Get the base name of a path."""
        return self._os.path.basename(path)
    
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
    
    def list_files(self, pattern: str, storage: str) -> list:
        """List files matching pattern in storage directory."""
        return sorted(self._glob.glob(self._os.path.join(storage, pattern)), reverse=True)
    
    def remove_file(self, filepath: str) -> None:
        """Remove file."""
        self._os.remove(filepath)
    
    def run_command(self, cmd: list) -> None:
        """Run shell command."""
        return self._subprocess.run(self._shlex.split(cmd[0]) if isinstance(cmd, list) else cmd)
    
    def stdin_read(self) -> str:
        """Read from stdin."""
        return self._sys_stdin.read()
    
    def get_history(self, limit: int = 20) -> list:
        """Get command history."""
        return self._read_history(limit=limit)


def _resolve_note_body(args, file_ops: FileOperations) -> str:
    """Resolve note body from --note flag, file argument, stdin, or empty string."""
    note_body = getattr(args, "note", None)
    if not note_body:
        file_arg = getattr(args, "file", None)
        if file_arg:
            note_body = file_ops.read_file(file_arg)
        elif not file_ops._sys_stdin.isatty():
            note_body = file_ops.stdin_read()
            
    return note_body if note_body is not None else ""


def _build_note_content(layout: str, date_str: str, tags: list, note_body: str) -> str:
    """Construct the markdown content with YAML front-matter."""
    return f"""---
layout: {layout}
title: "{date_str}"
date: {date_str}
tags: {tags}
---

{note_body}
"""


def _parse_note_content(content: str) -> tuple[list, str]:
    """Parse front-matter tags and body from note content."""
    parts = content.split("---", 2)
    tags = []
    body = ""
    if len(parts) >= 3:
        front_matter = parts[1]
        body = parts[2].strip()
        for line in front_matter.split("\n"):
            if line.startswith("tags: "):
                tags_str = line[len("tags: "):].strip()
                try:
                    tags = ast.literal_eval(tags_str)
                except:
                    pass
    else:
        body = content.strip()
    return tags, body


def _get_body_preview(body: str, max_length: int = 40) -> str:
    """Generate a single-line truncated preview of the note body."""
    body_preview = body.replace("\n", " ")
    if len(body_preview) > max_length:
        body_preview = body_preview[:max_length - 3] + "..."
    return body_preview


def _resolve_filename_from_history(args, file_ops: FileOperations) -> str:
    """Resolve filename from hash argument or command history if empty."""
    filename = args.hash
    if not filename:
        history = file_ops.get_history(limit=1)
        if history and len(history) > 0:
            last_cmd = history[0]
            parts = file_ops._shlex.split(last_cmd)
            if len(parts) >= 2:
                filename = parts[-1]
    return filename
