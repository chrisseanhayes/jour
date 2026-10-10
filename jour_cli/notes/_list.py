from typing import Optional
from jour_cli.config import load_config, get_storage_path
from ..shared.file_ops import FileOperations, _parse_note_content, _get_body_preview


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
            content = file_ops.read_file(f_path)
        except:
            continue
            
        tags, body = _parse_note_content(content)
        body_preview = _get_body_preview(body)
            
        tags_display = f"[{', '.join(tags)}]" if tags else "[]"
        print(f"{basename} {tags_display} {body_preview}")
