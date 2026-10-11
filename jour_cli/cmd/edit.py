from jour_cli.app_factory import AppFactory
from jour_cli.shared.note_content import _has_note_body, _parse_json_note_data
from jour_cli.shared.note_input import _resolve_filename_from_history


def edit_note(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    note_store = app_factory.get_note_store(config)
    note_id = _resolve_filename_from_history(args, dependencies)
    editor = app_factory.get_editor(config)

    try:
        original_content = note_store.get(note_id)
        if not note_store.edit(note_id, editor):
            dependencies.write_stderr(
                f"Error: Note with hash {args.hash} not found."
            )
            dependencies.write_stderr(
                "Hint: If this note was deleted outside Jour, run `jour rebuild` to "
                "refresh the tag index."
            )
            dependencies.exit(1)

        edited_content = note_store.get(note_id)
        if edited_content is None:
            dependencies.write_stderr(f"Error: Note {note_id} not found.")
            dependencies.write_stderr(
                "Hint: If this note was deleted outside Jour, run `jour rebuild` to "
                "refresh the tag index."
            )
            dependencies.exit(1)
        try:
            _parse_json_note_data(edited_content)
        except ValueError as error:
            if original_content is None or not note_store.update(
                note_id, original_content
            ):
                dependencies.write_stderr(
                    f"Error: Invalid JSON note: {error}. "
                    f"Note {note_id} could not be restored."
                )
            else:
                dependencies.write_stderr(f"Error: Invalid JSON note: {error}")
            dependencies.exit(1)
        if not _has_note_body(edited_content):
            if dependencies.confirm(
                f"Note {note_id} is empty. Delete it?", default=False
            ):
                if note_store.delete(note_id):
                    dependencies.write_stdout(f"Note {note_id} deleted.")
                else:
                    dependencies.write_stderr(
                        f"Error: Note {note_id} could not be deleted."
                    )
                    dependencies.exit(1)
            elif original_content is not None and not note_store.update(
                note_id, original_content
            ):
                dependencies.write_stderr(
                    f"Error: Note {note_id} could not be restored."
                )
                dependencies.exit(1)
    except Exception as e:
        dependencies.write_stderr(f"Error: Failed to edit note: {e}")
        dependencies.exit(1)
