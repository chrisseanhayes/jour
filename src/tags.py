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
