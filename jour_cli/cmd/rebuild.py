from jour_cli.app_factory import AppFactory


def cmd_rebuild(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    note_count = note_store.rebuild_tag_index()
    app_factory.dependencies.write_stdout(
        f"Rebuilt tag index for {note_count} note(s)."
    )
