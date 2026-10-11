from jour_cli.app_factory import AppFactory


def cat_note(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    content = note_store.get(args.hash)
    if content is not None:
        app_factory.dependencies.write_stdout(content, end="")
    else:
        app_factory.dependencies.write_stderr(f"Error: Note {args.hash} not found.")
        app_factory.dependencies.exit(1)
