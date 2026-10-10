import subprocess

from jour_cli.config import get_storage_path, load_config


def cmd_search(args):
    config = load_config()
    storage = get_storage_path(config)
    subprocess.run(["grep", "-rn", args.query, storage])
