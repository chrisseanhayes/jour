import re
from typing import Optional

from jour_cli.app_factory import AppFactory


_REBUILD_HISTORY_PATTERN = re.compile(r"^\[([^\]]+)\]\s+rebuild(?:\s|$)")


def cmd_index_status(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    history = app_factory.read_history(limit=None)
    last_rebuild: Optional[str] = None
    for line in history:
        match = _REBUILD_HISTORY_PATTERN.match(line)
        if match:
            last_rebuild = match.group(1)

    dependencies = app_factory.dependencies
    if last_rebuild is None:
        dependencies.write_stdout("Last rebuilt: Never")
    else:
        dependencies.write_stdout(f"Last rebuilt: {last_rebuild}")
    dependencies.write_stdout(
        f"Deleted notes: {note_store.deleted_note_count()}"
    )
