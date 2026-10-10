import argparse
from jour_cli.notes import cmd_notes_make, cmd_notes_list
from jour_cli.tags import cmd_tags_list, cmd_tags_show
from jour_cli.search import cmd_search

def main():
    parser = argparse.ArgumentParser(description="Minimal CLI Journal")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    notes_parser = subparsers.add_parser("notes")
    notes_sub = notes_parser.add_subparsers(dest="action", required=True)
    make_parser = notes_sub.add_parser("make")
    make_parser.add_argument("-n", "--note", default=None, help="Note body text")
    make_parser.add_argument("-t", "--tag", default=None, help="Comma-delimited tags")
    make_parser.add_argument("file", nargs="?", default=None, help="Optional file to read note from")
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
