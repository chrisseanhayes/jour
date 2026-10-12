import jmespath

from jour_cli.app_factory import AppFactory
from jour_cli.shared.jmespath_query import query_notes
from jour_cli.shared.note_content import _get_body_preview
from jour_cli.shared.note_document import NoteDocument


def list_notes(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)

    notes = note_store.list()
    visible_notes = []
    for note in notes:
        if "jour-archive" in note.tags and not args.show_archived:
            continue
        visible_notes.append(note)

    query = getattr(args, "jmespath_query", None)
    if query is not None:
        try:
            result = query_notes(visible_notes, query, app_factory.note_formats)
        except jmespath.exceptions.JMESPathError as error:
            app_factory.dependencies.write_stderr(
                f"Error: Invalid JMESPath query: {error}"
            )
            app_factory.dependencies.exit(1)
            return
        app_factory.dependencies.write_stdout(result)
        return

    for note in visible_notes:
        document = NoteDocument.from_content(note.content)
        body_preview = _get_body_preview(document.body)

        tags_display = f"[{', '.join(note.tags)}]" if note.tags else "[]"
        app_factory.dependencies.write_stdout(
            f"{note.id} {tags_display} {body_preview}"
        )
