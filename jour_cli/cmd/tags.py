from jour_cli.app_factory import AppFactory


def cmd_tags_list(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    for tag, count in note_store.tag_counts():
        app_factory.dependencies.write_stdout(f"{tag}: {count}")


def cmd_tags_show(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    for note_id in note_store.notes_for_tag(args.tag):
        app_factory.dependencies.write_stdout(note_id)
