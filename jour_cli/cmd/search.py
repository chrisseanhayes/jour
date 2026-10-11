from jour_cli.app_factory import AppFactory
from jour_cli.shared.jmespath_query import query_notes


def cmd_search(args, app_factory: AppFactory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    matches = note_store.search(args.query)
    jmespath_query = getattr(args, "jmespath_query", None)
    if jmespath_query is not None:
        notes = note_store.list()
        matching_ids = {
            match.partition(":")[0].rsplit(".", 1)[0] for match in matches
        }
        matching_notes = [
            note for note in notes if note.id in matching_ids
        ]
        app_factory.dependencies.write_stdout(
            query_notes(matching_notes, jmespath_query)
        )
        return

    for match in matches:
        app_factory.dependencies.write_stdout(match)
