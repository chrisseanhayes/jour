from jour_cli.app_factory import AppFactory
from jour_cli.shared.note_document import NoteDocument


def archive_note(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    note_store = app_factory.get_note_store(config)

    content = note_store.get(args.hash)
    if content is None:
        dependencies.write_stderr(f"Error: Note {args.hash} not found.")
        dependencies.exit(1)

    undo = getattr(args, "undo", False)
    action = "unarchive" if undo else "archive"
    try:
        document = NoteDocument.from_content(content)
        if undo:
            updated_content = document.remove_tag("jour-archive").content
        else:
            updated_content = document.add_tag("jour-archive").content
    except ValueError as error:
        dependencies.write_stderr(f"Error: Failed to {action} note: {error}")
        dependencies.exit(1)

    if updated_content != content and not note_store.update(args.hash, updated_content):
        dependencies.write_stderr(f"Error: Note {args.hash} could not be {action}d.")
        dependencies.exit(1)

    dependencies.write_stdout(f"Note {args.hash} {action}d.")
