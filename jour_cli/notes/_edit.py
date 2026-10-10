from typing import Optional
import sys
from jour_cli.config import load_config, get_storage_path, _default_editor
from jour_cli.db import get_note_filepath
from ..shared.file_ops import FileOperations, _resolve_filename_from_history


def cmd_notes_edit(
    args,
    file_ops: Optional[FileOperations] = FileOperations(),
):
    config = load_config()
    
    filename = _resolve_filename_from_history(args, file_ops)
    
    ext = config.get("storage", {}).get("extension", "jmd")
    if not filename.endswith(ext):
        filename = f"{filename}.{ext}"
    
    filepath = get_note_filepath(filename)
    
    if filepath is None:
        print(f"Error: Note with hash {args.hash} not found.", file=sys.stderr)
        sys.exit(1)
    
    if not file_ops.exists(filepath):
        print(f"Error: File for hash {args.hash} could not be found on disk.", file=sys.stderr)
        sys.exit(1)
    
    editor_cmd = config.get("editor", {}).get("command") or _default_editor()
    
    try:
        file_ops.run_command(editor_cmd + [filepath])
    except Exception as e:
        print(f"Error: Failed to launch editor: {e}", file=sys.stderr)
        sys.exit(1)
