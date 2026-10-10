Structuring the CLI into modular subcommand files isolates domain logic and keeps the codebase maintainable.

### Directory Structure

```text
src/
├── __init__.py
├── config.py
├── notes.py
├── tags.py
├── search.py
└── main.py

```

---

### 1. `src/config.py`

Handles default settings and deep-merges user overrides from `~/.jour/.jourconfig`.

```python
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

```

---

### 2. `src/notes.py`

Manages file creation and chronological listing.

```python
import os
import glob
import subprocess
from datetime import datetime
from src.config import load_config, get_storage_path

def cmd_notes_make(args):
    config = load_config()
    storage = get_storage_path(config)
    os.makedirs(storage, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    ext = config.get("storage", {}).get("extension", "jmd")
    filepath = os.path.join(storage, f"{timestamp}.{ext}")
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    layout = config.get("front_matter", {}).get("layout", "default")
    
    content = f"""---
layout: {layout}
title: "{date_str}"
date: {date_str}
tags: []
---

"""
    with open(filepath, "w") as f:
        f.write(content)
        
    editor = config.get("editor", {}).get("command", "open -t")
    subprocess.run(f"{editor} {filepath}", shell=True)

def cmd_notes_list(args):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    for f in sorted(glob.glob(os.path.join(storage, f"*.{ext}")), reverse=True):
        print(os.path.basename(f))

```

---

### 3. `src/tags.py`

Parses front matter tags across `.jmd` files.

```python
import os
import glob
import yaml
from src.config import load_config, get_storage_path

def parse_front_matter_tags(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                if fm and "tags" in fm and isinstance(fm["tags"], list):
                    return fm["tags"]
            except Exception:
                pass
    return []

def cmd_tags_list(args):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    tag_counts = {}
    for fpath in glob.glob(os.path.join(storage, f"*.{ext}")):
        for tag in parse_front_matter_tags(fpath):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{tag}: {count}")

def cmd_tags_show(args):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    for fpath in glob.glob(os.path.join(storage, f"*.{ext}")):
        if args.tag in parse_front_matter_tags(fpath):
            print(os.path.basename(fpath))

```

---

### 4. `src/search.py`

Executes grep-based text queries.

```python
import subprocess
from src.config import load_config, get_storage_path

def cmd_search(args):
    config = load_config()
    storage = get_storage_path(config)
    subprocess.run(["grep", "-rn", args.query, storage])

```

---

### 5. `src/main.py`

Defines argument parsing and routes commands to submodules.

```python
import argparse
from src.notes import cmd_notes_make, cmd_notes_list
from src.tags import cmd_tags_list, cmd_tags_show
from src.search import cmd_search

def main():
    parser = argparse.ArgumentParser(description="Minimal CLI Journal")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    notes_parser = subparsers.add_parser("notes")
    notes_sub = notes_parser.add_subparsers(dest="action", required=True)
    notes_sub.add_parser("make")
    notes_sub.add_parser("list")
    
    tags_parser = subparsers.add_parser("tags")
    tags_sub = tags_parser.add_subparsers(dest="action", required=True)
    tags_sub.add_parser("list")
    show_parser = tags_sub.add_parser("show")
    show_parser.add_argument("tag")
    
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    
    args = parser.parse_args()
    
    if args.command == "notes":
        if args.action == "make":
            cmd_notes_make(args)
        elif args.action == "list":
            cmd_notes_list(args)
    elif args.command == "tags":
        if args.action == "list":
            cmd_tags_list(args)
        elif args.action == "show":
            cmd_tags_show(args)
    elif args.command == "search":
        cmd_search(args)

if __name__ == "__main__":
    main()

```