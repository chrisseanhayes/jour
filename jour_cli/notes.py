import os
import sys
import glob
import shlex
import subprocess
import uuid
from datetime import datetime
from typing import Callable, Optional
from jour_cli.config import load_config, get_storage_path, _default_editor
from jour_cli.db import index_note, delete_note, get_note_filepath
from jour_cli.logging import read_history


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
        self._read_history = read_history
    
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


def cmd_notes_make(
    args,
    file_ops: Optional[FileOperations] = None,
):
    config = load_config()
    storage = get_storage_path(config)
    
    if file_ops is None:
        file_ops = FileOperations()
    
    file_ops.makedirs(storage, exist_ok=True)

    timestamp = file_ops._datetime.now().strftime("%Y%m%d%H%M%S")
    uid = file_ops._uuid.uuid4().hex[:8]
    ext = config.get("storage", {}).get("extension", "jmd")
    filepath = file_ops.join(storage, f"{timestamp}_{uid}.{ext}")

    date_str = file_ops._datetime.now().strftime("%Y-%m-%d %H:%M")
    layout = config.get("front_matter", {}).get("layout", "default")

    tags = []
    if getattr(args, "tag", None):
        tags = [t.strip() for t in args.tag.split(",") if t.strip()]

    # Priority: --note flag > file argument > piped stdin > open editor
    note_body = getattr(args, "note", None)
    if not note_body:
        file_arg = getattr(args, "file", None)
        if file_arg:
            note_body = file_ops.read_file(file_arg)
        elif not file_ops._sys_stdin.isatty():
            note_body = file_ops.stdin_read()
            
    if note_body is None:
        note_body = ""

    content = f"""---
layout: {layout}
title: "{date_str}"
date: {date_str}
tags: {tags}
---

{note_body}
"""
    file_ops.write_file(filepath, content)

    index_note(filepath, tags)

    if not note_body:
        editor_cmd = config.get("editor", {}).get("command") or _default_editor()
        file_ops.run_command(editor_cmd + [filepath])


def cmd_notes_list(
    args,
    file_ops: Optional[FileOperations] = None,
):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    if file_ops is None:
        file_ops = FileOperations()
    
    files = file_ops.list_files(f"*.{ext}", storage)
    
    for f_path in files:
        basename = file_ops.splitext(file_ops.basename(f_path))[0]
        
        try:
            with file_ops._open(f_path, "r") as f:
                content = f.read()
        except:
            continue
            
        parts = content.split("---", 2)
        tags = []
        body = ""
        if len(parts) >= 3:
            front_matter = parts[1]
            body = parts[2].strip()
            for line in front_matter.split("\n"):
                if line.startswith("tags: "):
                    tags_str = line[len("tags: "):].strip()
                    import ast
                    try:
                        tags = ast.literal_eval(tags_str)
                    except:
                        pass
        else:
            body = content.strip()
            
        body_preview = body.replace("\n", " ")
        if len(body_preview) > 40:
            body_preview = body_preview[:37] + "..."
            
        tags_display = f"[{', '.join(tags)}]" if tags else "[]"
        print(f"{basename} {tags_display} {body_preview}")


def cmd_notes_cat(
    args,
    file_ops: Optional[FileOperations] = None,
):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    if file_ops is None:
        file_ops = FileOperations()
    
    filepath = file_ops.join(storage, f"{args.hash}.{ext}")
    if file_ops.exists(filepath):
        with file_ops._open(filepath, "r") as f:
            print(f.read(), end="")
    else:
        print(f"Error: Note {args.hash} not found.", file=sys.stderr)
        sys.exit(1)


def cmd_notes_delete(
    args,
    file_ops: Optional[FileOperations] = None,
):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    if file_ops is None:
        file_ops = FileOperations()
    
    filename = f"{args.hash}.{ext}"
    filepath = file_ops.join(storage, filename)
    if file_ops.exists(filepath):
        file_ops.remove_file(filepath)
        delete_note(filename)
        print(f"Note {args.hash} deleted.")
    else:
        print(f"Error: Note {args.hash} not found.", file=sys.stderr)
        sys.exit(1)


def cmd_notes_edit(
    args,
    file_ops: Optional[FileOperations] = None,
):
    config = load_config()
    
    if file_ops is None:
        file_ops = FileOperations()
    
    # Get the filename from hash (hash is the basename without extension)
    filename = args.hash
    
    # If no hash provided, get the last edited note from history
    if not filename:
        history = file_ops.get_history(limit=1)
        if history and len(history) > 0:
            last_cmd = history[0]
            # Extract the hash from the command (last argument before editor path)
            parts = file_ops._shlex.split(last_cmd)
            if len(parts) >= 2:
                filename = parts[-1]
    
    # Append extension if not present
    ext = config.get("storage", {}).get("extension", "jmd")
    if not filename.endswith(ext):
        filename = f"{filename}.{ext}"
    
    # Look up the filepath in the database
    filepath = get_note_filepath(filename)
    
    if filepath is None:
        print(f"Error: Note with hash {args.hash} not found.", file=sys.stderr)
        sys.exit(1)
    
    # Check if file exists on disk
    if not file_ops.exists(filepath):
        print(f"Error: File for hash {args.hash} could not be found on disk.", file=sys.stderr)
        sys.exit(1)
    
    # Get editor command from config or use default
    editor_cmd = config.get("editor", {}).get("command") or _default_editor()
    
    try:
        file_ops.run_command(editor_cmd + [filepath])
    except Exception as e:
        print(f"Error: Failed to launch editor: {e}", file=sys.stderr)
        sys.exit(1)
