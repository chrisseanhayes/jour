import os
import yaml

JOUR_DIR = os.path.expanduser("~/.jour")
CONFIG_PATH = os.path.join(JOUR_DIR, ".jourconfig")

DEFAULT_CONFIG = {
    "storage": {
        "path": "~/.jour",
        "extension": "jmd"
    },
    "editor": {
        "command": "open -t"
    },
    "front_matter": {
        "layout": "default",
        "date_format": "%Y-%m-%d %H:%M"
    }
}

def deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config():
    os.makedirs(JOUR_DIR, exist_ok=True)
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            user_config = yaml.safe_load(f)
            if isinstance(user_config, dict):
                config = deep_merge(config, user_config)
    return config

def get_storage_path(config):
    return os.path.expanduser(config.get("storage", {}).get("path", "~/.jour"))
