from typing import Optional
import sys
from jour_cli.config import load_config, get_storage_path
from jour_cli.db import delete_note
from jour_cli.shared import FileOperations


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
