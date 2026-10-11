from jour_cli.app_factory import AppFactory
from jour_cli.shared.note_content import (
    _build_note_content,
    _extract_hashtags,
    _has_note_body,
)
from jour_cli.shared.note_input import _resolve_note_input


def make_note(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    note_store = app_factory.get_note_store(config)

    front_matter = config.get("front_matter", {})
    date_str = dependencies.now().strftime(
        front_matter.get("date_format", "%Y-%m-%d %H:%M")
    )
    layout = front_matter.get("layout", "default")

    tags = []
    if getattr(args, "tag", None):
        tags = [t.strip() for t in args.tag.split(",") if t.strip()]

    note_body, should_open_editor = _resolve_note_input(args, dependencies)
    if not should_open_editor and not note_body.strip():
        dependencies.write_stdout("No note created.")
        return

    tags = list(dict.fromkeys(tags + _extract_hashtags(note_body)))
    content = _build_note_content(layout, date_str, tags, note_body)
    note_id = note_store.create(content, tags)

    if should_open_editor:
        note_store.edit(note_id, app_factory.get_editor(config))
        edited_content = note_store.get(note_id)
        if edited_content is None:
            dependencies.write_stdout("No note created.")
        elif not _has_note_body(edited_content):
            if note_store.delete(note_id):
                dependencies.write_stdout("No note created.")
            else:
                dependencies.write_stderr(
                    f"Error: Note {note_id} could not be removed."
                )
                dependencies.exit(1)
