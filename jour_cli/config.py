from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Union

import yaml

from jour_cli.shared.dependencies import Dependencies


class StorageScope(str, Enum):
    GLOBAL = "global"
    REPO_LOCAL = "repo-local"


@dataclass(frozen=True)
class StorageContext:
    """Resolved journal location for one CLI invocation."""

    scope: StorageScope
    storage_path: str
    database_path: str
    config: dict


@dataclass(frozen=True)
class StoragePrompt:
    """Location detection result that needs an interactive scope choice."""

    config: dict
    global_context: StorageContext
    repo_root: str
    local_storage: str
    jour_home: str
    ignore_path: str
    ignore_contents: str
    ignored_repositories: tuple


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
    """Compatibility wrapper returning config for the resolved storage context."""
    return resolve_storage_context(config, dependencies, global_mode).config


def resolve_storage_context(config, dependencies: Dependencies, global_mode=False):
    """Resolve detected storage scope, handling any required interactive choice."""
    location = detect_storage_location(config, dependencies, global_mode)
    if isinstance(location, StorageContext):
        return location

    if not dependencies.stdin_is_interactive():
        return location.global_context

    use_local = dependencies.confirm(
        "Git repository detected. Use local Jour data in ./.jour? "
        "(No will ignore this repository and use global data)",
        default=True,
    )
    if not use_local:
        dependencies.makedirs(location.jour_home, exist_ok=True)
        if location.repo_root not in location.ignored_repositories:
            separator = (
                "\n"
                if location.ignore_contents
                and not location.ignore_contents.endswith("\n")
                else ""
            )
            dependencies.append_file(
                location.ignore_path, f"{separator}{location.repo_root}\n"
            )
        return location.global_context

    dependencies.makedirs(location.local_storage, exist_ok=True)
    dependencies.write_stderr(
        "Using repo-local data in .jour. Add .jour/ to this repository's "
        ".gitignore to keep journal files out of commits."
    )
    scoped_config = _with_storage_paths(
        location.config, location.local_storage, dependencies
    )
    return _storage_context(scoped_config, StorageScope.REPO_LOCAL, dependencies)


def detect_storage_location(
    config, dependencies: Dependencies, global_mode=False
) -> Union[StorageContext, StoragePrompt]:
    """Detect the applicable location without prompting or creating directories."""
    if global_mode:
        return _storage_context(config, StorageScope.GLOBAL, dependencies)

    repo_root = dependencies.get_git_root()
    if repo_root is None:
        return _storage_context(config, StorageScope.GLOBAL, dependencies)
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
        return _storage_context(config, StorageScope.GLOBAL, dependencies)

    local_storage = dependencies.join(repo_root, ".jour")
    if dependencies.exists(local_storage):
        scoped_config = _with_storage_paths(config, local_storage, dependencies)
        return _storage_context(scoped_config, StorageScope.REPO_LOCAL, dependencies)

    return StoragePrompt(
        config=config,
        global_context=_storage_context(config, StorageScope.GLOBAL, dependencies),
        repo_root=repo_root,
        local_storage=local_storage,
        jour_home=jour_home,
        ignore_path=ignore_path,
        ignore_contents=ignore_contents,
        ignored_repositories=tuple(ignored_repositories),
    )


def initialize_local_storage(config, dependencies: Dependencies):
    """Compatibility wrapper returning config for initialized local storage."""
    return initialize_local_context(config, dependencies).config


def initialize_local_context(config, dependencies: Dependencies):
    """Create repo-local storage and return its resolved location context."""
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
    scoped_config = _with_storage_paths(config, local_storage, dependencies)
    return _storage_context(scoped_config, StorageScope.REPO_LOCAL, dependencies)


def _storage_context(config, scope, dependencies):
    return StorageContext(
        scope=scope,
        storage_path=get_storage_path(config, dependencies),
        database_path=dependencies.expanduser(
            config.get("database", {}).get("path", "~/.jour/jour.db")
        ),
        config=config,
    )


def _with_storage_paths(config, storage_path, dependencies):
    scoped_config = deepcopy(config)
    scoped_config.setdefault("storage", {})["path"] = storage_path
    scoped_config.setdefault("database", {})["path"] = dependencies.join(
        storage_path, "jour.db"
    )
    return scoped_config
