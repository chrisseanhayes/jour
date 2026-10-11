from jour_cli.app_factory import AppFactory
from jour_cli.shared.note_content import _add_front_matter_kvp


def add_kvp(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    note_store = app_factory.get_note_store(config)

    content = note_store.get(args.hash)
    if content is None:
        dependencies.write_stderr(f"Error: Note {args.hash} not found.")
        dependencies.exit(1)

    try:
        updated_content = _add_front_matter_kvp(content, args.key, args.value)
    except ValueError as error:
        dependencies.write_stderr(f"Error: Failed to add KVP to note: {error}")
        dependencies.exit(1)

    if not note_store.update(args.hash, updated_content):
        dependencies.write_stderr(f"Error: Note {args.hash} could not be updated.")
        dependencies.exit(1)

    dependencies.write_stdout(f"Added KVP '{args.key}' to note {args.hash}.")
