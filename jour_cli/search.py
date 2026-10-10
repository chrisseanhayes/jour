import subprocess
from jour_cli.config import load_config, get_storage_path

def cmd_search(args):
    config = load_config()
    storage = get_storage_path(config)
    subprocess.run(["grep", "-rn", args.query, storage])
