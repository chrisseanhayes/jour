from copy import deepcopy
import yaml

from jour_cli.shared.dependencies import Dependencies


def _default_editor(dependencies: Dependencies) -> str:
    # Respect user's preferred editor env vars first
    return (
        dependencies.get_environment_variable("VISUAL")
        or dependencies.get_environment_variable("EDITOR")
        or ("open -t" if dependencies.is_macos() else "xdg-open")
    )


DEFAULT_CONFIG = {
    "storage": {
        "path": "~/.jour",
        "extension": "jmd",
    },
    "database": {
        "path": "~/.jour/jour.db",
    },
    "editor": {
        "command": None,  # resolved at runtime via _default_editor()
    },
    "front_matter": {
        "layout": "default",
        "date_format": "%Y-%m-%d %H:%M",
    },
}


def deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(dependencies: Dependencies):
    jour_dir = dependencies.join(dependencies.expanduser("~"), ".jour")
    config_path = dependencies.join(jour_dir, ".jourconfig")
    dependencies.makedirs(jour_dir, exist_ok=True)
    config = deepcopy(DEFAULT_CONFIG)
    if dependencies.exists(config_path):
        user_config = yaml.safe_load(dependencies.read_file(config_path))
        if isinstance(user_config, dict):
            config = deep_merge(config, user_config)
    return config


def get_storage_path(config, dependencies: Dependencies):
    return dependencies.expanduser(config.get("storage", {}).get("path", "~/.jour"))


def resolve_storage_scope(config, dependencies: Dependencies, global_mode=False):
    """Select global or repository-local note and tag-index storage."""
    if global_mode:
        return config

    repo_root = dependencies.get_git_root()
    if repo_root is None:
        return config
    repo_root = dependencies.path(repo_root)

    jour_home = dependencies.join(dependencies.expanduser("~"), ".jour")
    ignore_path = dependencies.join(jour_home, ".jourignore")
    ignore_contents = ""
    ignored_repositories = []
    if dependencies.exists(ignore_path):
        ignore_contents = dependencies.read_file(ignore_path)
        ignored_repositories = [
            line.strip()
            for line in ignore_contents.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    if repo_root in ignored_repositories:
        return config

    local_storage = dependencies.join(repo_root, ".jour")
    if dependencies.exists(local_storage):
        return _with_storage_paths(config, local_storage, dependencies)

    if not dependencies.stdin_is_interactive():
        return config

    use_local = dependencies.confirm(
        "Git repository detected. Use local Jour data in ./.jour? "
        "(No will ignore this repository and use global data)",
        default=True,
    )
    if not use_local:
        dependencies.makedirs(jour_home, exist_ok=True)
        if repo_root not in ignored_repositories:
            separator = (
                "\n" if ignore_contents and not ignore_contents.endswith("\n") else ""
            )
            dependencies.append_file(ignore_path, f"{separator}{repo_root}\n")
        return config

    dependencies.makedirs(local_storage, exist_ok=True)
    dependencies.write_stderr(
        "Using repo-local data in .jour. Add .jour/ to this repository's "
        ".gitignore to keep journal files out of commits."
    )
    return _with_storage_paths(config, local_storage, dependencies)


def initialize_local_storage(config, dependencies: Dependencies):
    """Create repository-local storage and remove the repository from global ignore."""
    repo_root = dependencies.get_git_root()
    if repo_root is None:
        raise ValueError("jour init must be run inside a Git repository.")
    repo_root = dependencies.path(repo_root)

    jour_home = dependencies.join(dependencies.expanduser("~"), ".jour")
    ignore_path = dependencies.join(jour_home, ".jourignore")
    if dependencies.exists(ignore_path):
        ignore_lines = dependencies.read_file(ignore_path).splitlines(keepends=True)
        remaining_lines = [
            line
            for line in ignore_lines
            if line.strip() != repo_root
        ]
        if remaining_lines != ignore_lines:
            dependencies.write_file(ignore_path, "".join(remaining_lines))

    local_storage = dependencies.join(repo_root, ".jour")
    dependencies.makedirs(local_storage, exist_ok=True)
    return _with_storage_paths(config, local_storage, dependencies)


def _with_storage_paths(config, storage_path, dependencies):
    scoped_config = deepcopy(config)
    scoped_config.setdefault("storage", {})["path"] = storage_path
    scoped_config.setdefault("database", {})["path"] = dependencies.join(
        storage_path, "jour.db"
    )
    return scoped_config
