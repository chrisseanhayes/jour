import sys
from typing import Optional

from jour_cli.config import get_storage_path, load_config

from ..shared.file_ops import FileOperations


def cmd_notes_cat(
    args,
    file_ops: Optional[FileOperations] = FileOperations(),
):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    filepath = file_ops.join(storage, f"{args.hash}.{ext}")
    if file_ops.exists(filepath):
        with file_ops._open(filepath, "r") as f:
            print(f.read(), end="")
    else:
        print(f"Error: Note {args.hash} not found.", file=sys.stderr)
        sys.exit(1)
