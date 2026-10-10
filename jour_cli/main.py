import argparse
from datetime import datetime
from jour_cli.notes import cmd_notes_make, cmd_notes_list, cmd_notes_cat, cmd_notes_delete, cmd_notes_edit
from jour_cli.tags import cmd_tags_list, cmd_tags_show
from jour_cli.search import cmd_search
from jour_cli.logging import log_command, read_history

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
    cat_parser = notes_sub.add_parser("cat")
    cat_parser.add_argument("hash")
    delete_parser = notes_sub.add_parser("delete")
    delete_parser.add_argument("hash")
    edit_parser = notes_sub.add_parser("edit")
    edit_parser.add_argument("hash")
    
    tags_parser = subparsers.add_parser("tags")
    tags_sub = tags_parser.add_subparsers(dest="action", required=True)
    tags_sub.add_parser("list")
    show_parser = tags_sub.add_parser("show")
    show_parser.add_argument("tag")
    
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    
    history_parser = subparsers.add_parser("history")
    history_parser.add_argument("-n", "--count", type=int, default=20, help="Number of entries to show (default: 20)")
    
    args = parser.parse_args()
    
    if args.command == "notes":
        if args.action == "make":
            log_command("notes make", args)
            cmd_notes_make(args)
        elif args.action == "list":
            log_command("notes list", args)
            cmd_notes_list(args)
        elif args.action == "cat":
            log_command("notes cat", args)
            cmd_notes_cat(args)
        elif args.action == "delete":
            log_command("notes delete", args)
            cmd_notes_delete(args)
        elif args.action == "edit":
            log_command("notes edit", args)
            cmd_notes_edit(args)
    elif args.command == "tags":
        if args.action == "list":
            log_command("tags list", args)
            cmd_tags_list(args)
        elif args.action == "show":
            log_command("tags show", args)
            cmd_tags_show(args)
    elif args.command == "search":
        log_command("search", args)
        cmd_search(args)
    elif args.command == "history":
        history_entries = read_history(args.count)
        for entry in history_entries:
            print(entry)

if __name__ == "__main__":
    main()
