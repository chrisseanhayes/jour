from jour_cli.app_factory import AppFactory
from ...shared.note_input import _resolve_filename_from_history


def cmd_notes_edit(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    note_store = app_factory.get_note_store(config)
    note_id = _resolve_filename_from_history(args, dependencies)
    editor = app_factory.get_editor(config)

    try:
        if not note_store.edit(note_id, editor):
            dependencies.write_stderr(
                f"Error: Note with hash {args.hash} not found."
            )
            dependencies.exit(1)
    except Exception as e:
        dependencies.write_stderr(f"Error: Failed to launch editor: {e}")
        dependencies.exit(1)
