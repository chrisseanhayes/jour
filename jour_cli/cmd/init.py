from jour_cli.app_factory import AppFactory


def init_local_journal(args, app_factory: AppFactory):
    dependencies = app_factory.dependencies
    try:
        config = app_factory.initialize_local_journal()
    except ValueError as error:
        dependencies.write_stderr(f"Error: {error}")
        dependencies.exit(1)
        return

    dependencies.write_stdout(
        f"Initialized local Jour in {config['storage']['path']}."
    )
    dependencies.write_stderr(
        "Add .jour/ to this repository's .gitignore to keep journal files "
        "out of commits."
    )
