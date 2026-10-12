from jour_cli.app_factory import AppFactory


def cmd_git_init(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    storage_config = config.get("storage", {})
    storage = dependencies.expanduser(storage_config.get("path", "~/.jour"))
    extension = storage_config.get("extension", "jmd").lstrip(".")

    dependencies.makedirs(storage, exist_ok=True)
    result = _run_git(dependencies, storage, ["init"])
    if result.returncode:
        _report_git_error(dependencies, result)
        dependencies.exit(result.returncode)

    git_dir = _run_git(dependencies, storage, ["rev-parse", "--absolute-git-dir"])
    if git_dir.returncode:
        _report_git_error(dependencies, git_dir)
        dependencies.exit(git_dir.returncode)

    exclude_path = dependencies.join(git_dir.stdout.strip(), "info", "exclude")
    existing_excludes = ""
    if dependencies.exists(exclude_path):
        existing_excludes = dependencies.read_file(exclude_path)
    exclude_rules = f"*\n!*.{extension}\n"
    if exclude_rules not in existing_excludes:
        separator = (
            "\n"
            if existing_excludes and not existing_excludes.endswith("\n")
            else ""
        )
        dependencies.append_file(exclude_path, f"{separator}{exclude_rules}")

    dependencies.write_stdout(f"Initialized note Git repository in {storage}.")


def cmd_git_commit(args, app_factory: AppFactory):
    config = app_factory.get_config()
    dependencies = app_factory.dependencies
    storage_config = config.get("storage", {})
    storage = dependencies.expanduser(storage_config.get("path", "~/.jour"))
    extension = storage_config.get("extension", "jmd").lstrip(".")

    root = _run_git(dependencies, storage, ["rev-parse", "--show-toplevel"])
    if root.returncode or dependencies.realpath(
        root.stdout.strip()
    ) != dependencies.realpath(storage):
        dependencies.write_stderr(
            f"Error: No Jour Git repository initialized in {storage}. "
            "Run 'jour git init' first."
        )
        dependencies.exit(1)

    note_pathspec = f"*.{extension}"
    add_result = _run_git(
        dependencies, storage, ["add", "--all", "--force", "--", note_pathspec]
    )
    if add_result.returncode:
        _report_git_error(dependencies, add_result)
        dependencies.exit(add_result.returncode)

    message = args.message
    result = _run_git(
        dependencies,
        storage,
        [
            "commit",
            "--only",
            "--message",
            message,
            "--",
            note_pathspec,
        ],
    )
    if result.returncode:
        _report_git_error(dependencies, result)
        dependencies.exit(result.returncode)

    if result.stdout:
        dependencies.write_stdout(result.stdout.rstrip("\n"))


def _run_git(dependencies, storage, arguments):
    try:
        return dependencies.run_command(
            ["git", "-C", storage, *arguments], capture_output=True
        )
    except FileNotFoundError:
        dependencies.write_stderr("Error: Git is not installed or not available on PATH.")
        dependencies.exit(1)


def _report_git_error(dependencies, result):
    if result.stderr:
        dependencies.write_stderr(result.stderr.rstrip("\n"))
