from jour_cli.app_factory import AppFactory
from jour_cli.shared.note_content import _has_note_body


def cmd_prune(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    note_store = app_factory.get_note_store(config)

    deleted_count = 0
    failed_ids = []
    for note in note_store.list():
        if _has_note_body(note.content):
            continue
        if note_store.delete(note.id):
            deleted_count += 1
        else:
            failed_ids.append(note.id)

    if failed_ids:
        for note_id in failed_ids:
            dependencies.write_stderr(
                f"Error: Empty note {note_id} could not be deleted."
            )
        dependencies.exit(1)
        return

    if deleted_count:
        dependencies.write_stdout(f"Pruned {deleted_count} empty note(s).")
    else:
        dependencies.write_stdout("No empty notes found.")
