from typing import Tuple

from jour_cli.shared.dependencies import Dependencies


def _resolve_note_input(args, dependencies: Dependencies) -> Tuple[str, bool]:
    """Resolve the body and whether an interactive editor should be opened."""
    note_body = getattr(args, "note", None)
    if note_body is not None:
        return note_body, False

    file_arg = getattr(args, "file", None)
    if file_arg is not None:
        return dependencies.read_file(file_arg), False

    if dependencies.stdin_is_interactive():
        return "", True

    return dependencies.stdin_read(), False


def _resolve_note_body(args, dependencies: Dependencies) -> str:
    """Resolve note body from --note flag, file argument, stdin, or empty string."""
    note_body, _ = _resolve_note_input(args, dependencies)
    return note_body


def _resolve_filename_from_history(args, dependencies: Dependencies) -> str:
    """Resolve filename from hash argument or command history if empty."""
    filename = args.hash
    if not filename:
        history = dependencies.get_history(limit=1)
        if history and len(history) > 0:
            last_cmd = history[0]
            parts = dependencies.split_command(last_cmd)
            if len(parts) >= 2:
                filename = parts[-1]
    return filename
