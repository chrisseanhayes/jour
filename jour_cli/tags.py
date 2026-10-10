from jour_cli.config import load_config
from jour_cli.db import get_notes_for_tag, get_tag_counts


def cmd_tags_list(args):
    load_config()
    for tag, count in get_tag_counts():
        print(f"{tag}: {count}")

def cmd_tags_show(args):
    load_config()
    for filename in get_notes_for_tag(args.tag):
        print(filename)
