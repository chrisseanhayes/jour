from jour_cli.app_factory import AppFactory
from ...shared.note_content import _build_note_content, _extract_hashtags
from ...shared.note_input import _resolve_note_input


def cmd_notes_make(args, app_factory: AppFactory):
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
    tags = list(dict.fromkeys(tags + _extract_hashtags(note_body)))
    content = _build_note_content(layout, date_str, tags, note_body)
    note_id = note_store.create(content, tags)

    if should_open_editor:
        note_store.edit(note_id, app_factory.get_editor(config))
