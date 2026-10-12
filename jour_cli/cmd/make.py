from jour_cli.app_factory import AppFactory
from jour_cli.shared.note_content import (
    _build_note_content,
    _extract_hashtags,
)
from jour_cli.shared.note_input import _resolve_note_input
from jour_cli.shared.note_lifecycle import NoteLifecycle, NoteLifecycleState


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
    note_type = getattr(args, "note_type", "markdown")
    if should_open_editor and note_type == "json":
        note_body = "{}"
    content = _build_note_content(layout, date_str, tags, note_body, note_type)
    lifecycle = NoteLifecycle.draft(content).validate(app_factory.note_formats)
    if lifecycle.state == NoteLifecycleState.REJECTED:
        dependencies.write_stderr(f"Error: Invalid note: {lifecycle.error}")
        dependencies.exit(1)
    note_id = note_store.create(content, tags)
    lifecycle.mark_saved()

    if should_open_editor:
        note_store.edit(note_id, app_factory.get_editor(config))
        edited_content = note_store.get(note_id)
        if edited_content is None:
            dependencies.write_stdout("No note created.")
        else:
            edited_lifecycle = NoteLifecycle.draft(edited_content).validate(
                app_factory.note_formats
            )
            if edited_lifecycle.state == NoteLifecycleState.REJECTED:
                if not note_store.delete(note_id):
                    dependencies.write_stderr(
                        f"Error: Invalid note: {edited_lifecycle.error}. "
                        f"Note {note_id} could not be removed."
                    )
                else:
                    dependencies.write_stderr(
                        f"Error: Invalid note: {edited_lifecycle.error}"
                    )
                dependencies.exit(1)
            document = edited_lifecycle.document
            if document is None:
                raise RuntimeError("Validated note lifecycle is missing its document.")
            if not document.body:
                edited_lifecycle = edited_lifecycle.discard()
                if note_store.delete(note_id):
                    dependencies.write_stdout("No note created.")
                else:
                    dependencies.write_stderr(
                        f"Error: Note {note_id} could not be removed."
                    )
                    dependencies.exit(1)
            else:
                edited_lifecycle.mark_saved()
