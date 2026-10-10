import sys
from typing import Optional

from jour_cli.config import get_storage_path, load_config
from jour_cli.db import delete_note

from ..shared.file_ops import FileOperations


def cmd_notes_delete(
    args,
    file_ops: Optional[FileOperations] = FileOperations(),
):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    filename = f"{args.hash}.{ext}"
    filepath = file_ops.join(storage, filename)
    if file_ops.exists(filepath):
        file_ops.remove_file(filepath)
        delete_note(filename)
        print(f"Note {args.hash} deleted.")
    else:
        print(f"Error: Note {args.hash} not found.", file=sys.stderr)
        sys.exit(1)
