from datetime import datetime
from typing import Optional
import os
import json
from jour_cli.config import load_config, get_storage_path


def _default_editor():
    """Get the default editor from config or use 'nano' as fallback."""
    config = load_config()
    if config and config.get("editor"):
        return config["editor"]
    return "nano"


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> Optional[dict]:
    """Load configuration from config file."""
    import glob
    config_path = get_storage_path() + "/config.json"
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except:
        return None


def get_storage_path(config: Optional[dict] = None) -> str:
    """Get the storage path from config."""
    if not config:
        config = load_config()
    if config and "storage":
        return config["storage"]
    return os.path.expanduser("~/.jour")


def get_history_path(file_ops=None):
    """Get the path to the history log file."""
    if file_ops is None:
        from jour_cli.shared.file_ops import FileOperations
        file_ops = FileOperations()
    
    home_dir = file_ops.path.expanduser("~")
    logs_dir = file_ops.path.join(home_dir, ".jour", "logs")
    history_file = file_ops.path.join(logs_dir, "history")
    
    # Create directory if it doesn't exist
    file_ops.makedirs(logs_dir, exist_ok=True)
    
    return history_file


def log_command(command, args=None, file_ops=None):
    """Log a command with timestamp to the history file."""
    if file_ops is None:
        from jour_cli.shared.file_ops import FileOperations
        file_ops = FileOperations()
    
    history_path = get_history_path(file_ops)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the command line
    if args:
        # Convert args to string representation
        args_str = ", ".join([f"{k}={v}" for k, v in vars(args).items() if v is not None])
        log_line = f"[{timestamp}] {command} {args_str}\n"
    else:
        log_line = f"[{timestamp}] {command}\n"
    
    with open(history_path, "a") as f:
        f.write(log_line)


def read_history(limit=20, file_ops=None):
    """Read and return the last N lines from the history file."""
    if file_ops is None:
        from jour_cli.shared.file_ops import FileOperations
        file_ops = FileOperations()
    
    history_path = get_history_path(file_ops)
    
    if not file_ops.path.exists(history_path):
        # Create empty history file to ensure it exists for future logging
        with open(history_path, "w") as f:
            pass
        return []
    
    with open(history_path, "r") as f:
        lines = f.readlines()
    
    # Return last N lines (or all if fewer than N)
    return [line.rstrip("\n") for line in lines[-limit:]]
