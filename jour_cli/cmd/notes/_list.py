from jour_cli.app_factory import AppFactory
from ...shared.note_content import _get_body_preview, _parse_note_content


def cmd_notes_list(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)

    for note in note_store.list():
        if "jour-archive" in note.tags and not args.show_archived:
            continue

        _, body = _parse_note_content(note.content)
        body_preview = _get_body_preview(body)

        tags_display = f"[{', '.join(note.tags)}]" if note.tags else "[]"
        app_factory.dependencies.write_stdout(
            f"{note.id} {tags_display} {body_preview}"
        )
