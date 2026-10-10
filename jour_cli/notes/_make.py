from typing import Optional
from jour_cli.notes import FileOperations, _resolve_note_body, _build_note_content


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

    note_body = _resolve_note_body(args, file_ops)
    content = _build_note_content(layout, date_str, tags, note_body)
    
    file_ops.write_file(filepath, content)
    index_note(filepath, tags)

    if not note_body:
        editor_cmd = config.get("editor", {}).get("command") or _default_editor()
        file_ops.run_command(editor_cmd + [filepath])
