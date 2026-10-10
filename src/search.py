import subprocess
from src.config import load_config, get_storage_path

def cmd_search(args):
    config = load_config()
    storage = get_storage_path(config)
    subprocess.run(["grep", "-rn", args.query, storage])
