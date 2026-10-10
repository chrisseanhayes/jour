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
