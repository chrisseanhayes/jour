import logging

from jour_cli.app_factory import AppFactory
from jour_cli.storage.filesystem_note_store import FileSystemNoteStore
from jour_cli.storage.note_watcher import GlobalNoteWatcher


def cmd_watch(args, app_factory: AppFactory):
    app_factory.set_global_mode(True)
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    if not isinstance(note_store, FileSystemNoteStore):
        raise TypeError("The global watch command requires filesystem note storage.")

    dependencies = app_factory.dependencies
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    dependencies.write_stdout(
        f"Watching global Jour notes in {note_store.storage}. Press Ctrl-C to stop."
    )
    try:
        GlobalNoteWatcher(note_store).run()
    except KeyboardInterrupt:
        dependencies.write_stdout("Stopped watching global Jour notes.")
