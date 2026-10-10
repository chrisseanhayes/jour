from typing import Optional
import sys
from jour_cli.config import load_config, get_storage_path
from ..shared.file_ops import FileOperations


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
