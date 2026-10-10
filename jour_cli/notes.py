import os
import sys
import glob
import shlex
import subprocess
import uuid
from datetime import datetime
from jour_cli.config import load_config, get_storage_path, _default_editor
from jour_cli.db import index_note, delete_note

def cmd_notes_make(args):
    config = load_config()
    storage = get_storage_path(config)
    os.makedirs(storage, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:8]
    ext = config.get("storage", {}).get("extension", "jmd")
    filepath = os.path.join(storage, f"{timestamp}_{uid}.{ext}")

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    layout = config.get("front_matter", {}).get("layout", "default")

    tags = []
    if getattr(args, "tag", None):
        tags = [t.strip() for t in args.tag.split(",") if t.strip()]

    # Priority: --note flag > file argument > piped stdin > open editor
    note_body = getattr(args, "note", None)
    if not note_body:
        file_arg = getattr(args, "file", None)
        if file_arg:
            with open(file_arg, "r") as f:
                note_body = f.read()
        elif not sys.stdin.isatty():
            note_body = sys.stdin.read()
            
    if note_body is None:
        note_body = ""

    content = f"""---
layout: {layout}
title: "{date_str}"
date: {date_str}
tags: {tags}
---

{note_body}
"""
    with open(filepath, "w") as f:
        f.write(content)

    index_note(filepath, tags)

    if not note_body:
        editor_cmd = config.get("editor", {}).get("command") or _default_editor()
        subprocess.run(shlex.split(editor_cmd) + [filepath])

def cmd_notes_list(args):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    for f in sorted(glob.glob(os.path.join(storage, f"*.{ext}")), reverse=True):
        print(os.path.basename(f))

def cmd_notes_cat(args):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    filepath = os.path.join(storage, f"{args.hash}.{ext}")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            print(f.read(), end="")
    else:
        print(f"Error: Note {args.hash} not found.", file=sys.stderr)
        sys.exit(1)

def cmd_notes_delete(args):
    config = load_config()
    storage = get_storage_path(config)
    ext = config.get("storage", {}).get("extension", "jmd")
    
    filename = f"{args.hash}.{ext}"
    filepath = os.path.join(storage, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        delete_note(filename)
        print(f"Note {args.hash} deleted.")
    else:
        print(f"Error: Note {args.hash} not found.", file=sys.stderr)
        sys.exit(1)
