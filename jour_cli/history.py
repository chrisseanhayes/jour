from typing import Optional

from jour_cli.shared.dependencies import Dependencies


def get_history_path(dependencies: Dependencies) -> str:
    """Get the path to the history log file."""
    home_dir = dependencies.expanduser("~")
    logs_dir = dependencies.join(home_dir, ".jour", "logs")
    dependencies.makedirs(logs_dir, exist_ok=True)
    return dependencies.join(logs_dir, "history")


def log_command(
    command: str,
    args=None,
    *,
    dependencies: Dependencies,
) -> None:
    """Log a command with timestamp to the history file."""
    history_path = get_history_path(dependencies)
    timestamp = dependencies.now().strftime("%Y-%m-%d %H:%M:%S")

    if args:
        args_str = ", ".join(
            f"{key}={value}"
            for key, value in vars(args).items()
            if value is not None
        )
        log_line = f"[{timestamp}] {command} {args_str}\n"
    else:
        log_line = f"[{timestamp}] {command}\n"

    dependencies.append_file(history_path, log_line)


def read_history(
    dependencies: Dependencies,
    limit: Optional[int] = 20,
) -> list:
    """Read history, optionally returning only its last N lines."""
    history_path = get_history_path(dependencies)

    if not dependencies.exists(history_path):
        dependencies.write_file(history_path, "")
        return []

    lines = dependencies.read_file(history_path).splitlines(keepends=True)

    if limit is not None:
        lines = lines[-limit:] if limit else []
    return [line.rstrip("\n") for line in lines]
