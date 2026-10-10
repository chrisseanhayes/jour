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
    
    for f_path in sorted(glob.glob(os.path.join(storage, f"*.{ext}")), reverse=True):
        basename = os.path.splitext(os.path.basename(f_path))[0]
        
        try:
            with open(f_path, "r") as f:
                content = f.read()
        except:
            continue
            
        parts = content.split("---", 2)
        tags = []
        body = ""
        if len(parts) >= 3:
            front_matter = parts[1]
            body = parts[2].strip()
            for line in front_matter.split("\n"):
                if line.startswith("tags: "):
                    tags_str = line[len("tags: "):].strip()
                    import ast
                    try:
                        tags = ast.literal_eval(tags_str)
                    except:
                        pass
        else:
            body = content.strip()
            
        body_preview = body.replace("\n", " ")
        if len(body_preview) > 40:
            body_preview = body_preview[:37] + "..."
            
        tags_display = f"[{', '.join(tags)}]" if tags else "[]"
        print(f"{basename} {tags_display} {body_preview}")

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
