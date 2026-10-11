from jour_cli.app_factory import AppFactory


def cmd_notes_delete(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    if note_store.delete(args.hash):
        app_factory.dependencies.write_stdout(f"Note {args.hash} deleted.")
    else:
        app_factory.dependencies.write_stderr(f"Error: Note {args.hash} not found.")
        app_factory.dependencies.exit(1)
