from typing import Optional

from jour_cli.config import _default_editor, get_storage_path, load_config
from jour_cli.db import index_note

from ..shared.file_ops import FileOperations, _build_note_content, _resolve_note_body


def cmd_notes_make(
    args,
    file_ops: Optional[FileOperations] = FileOperations(),
):
    config = load_config()
    storage = get_storage_path(config)
    
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

    note_body = _resolve_note_body(args, file_ops)
    content = _build_note_content(layout, date_str, tags, note_body)
    
    file_ops.write_file(filepath, content)
    index_note(filepath, tags)

    if not note_body:
        editor_cmd = config.get("editor", {}).get("command") or _default_editor()
        if isinstance(editor_cmd, str):
            editor_cmd = [editor_cmd]
        file_ops.run_command(editor_cmd + [filepath])
