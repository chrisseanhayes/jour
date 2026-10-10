from typing import Optional

from jour_cli.config import get_storage_path, load_config

from ..shared.file_ops import FileOperations, _get_body_preview, _parse_note_content


def cmd_notes_list(
    args,
    file_ops: Optional[FileOperations] = FileOperations(),
):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    files = file_ops.list_files(f"*.{ext}", storage)
    
    for f_path in files:
        basename = file_ops.splitext(file_ops.basename(f_path))[0]
        
        try:
            content = file_ops.read_file(f_path)
        except:
            continue
            
        tags, body = _parse_note_content(content)
        body_preview = _get_body_preview(body)
            
        tags_display = f"[{', '.join(tags)}]" if tags else "[]"
        print(f"{basename} {tags_display} {body_preview}")
