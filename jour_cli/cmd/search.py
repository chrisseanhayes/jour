from jour_cli.app_factory import AppFactory


def cmd_search(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    for match in note_store.search(args.query):
        app_factory.dependencies.write_stdout(match)
