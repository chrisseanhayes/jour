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
