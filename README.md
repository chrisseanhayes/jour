# jour — Minimal CLI Journal

A minimal, fast, command-line journaling tool written in Python.

## Features

- **`jour make`**: Create a new note. You can pass the note body directly via the `-n`/`--note` flag, pipe it via stdin (e.g., `cat file.txt | jour make`), or simply run the command to open your default editor (`$VISUAL` or `$EDITOR`). Empty note bodies are not saved; an empty note left in the editor is discarded.
- **`jour list`**: Display notes, sorted chronologically, with their hash, applied tags, and a brief content preview. Notes tagged `jour-archive` are hidden by default; use `jour list --show-archived` to include them. Use `-q`/`--query` with a JMESPath expression to query structured note records (`id`, `tags`, `content`, and parsed `body`); query results are emitted as JSON.
- **`jour archive <hash>`**: Tag a note with `jour-archive` so it is hidden from `list` by default. Use `jour archive --undo <hash>` to remove that tag and restore the note to the default list. The note's other tags and front-matter fields are preserved.
- **`jour cat <hash>`**: View the full content and YAML front matter of a specific note by its hash identifier (the extension-free ID shown by `list`).
- **`jour delete <hash>`**: Delete a specific note from your storage and the tag index.
- **`jour edit <hash>`**: Open a specific journal entry for editing in the system's default editor. The editor is determined by your configuration or falls back to the system default (e.g., `vi` or `nano`). If the body is cleared, you are asked to confirm deletion; declining restores the previous note.
- **Compatibility**: The original `jour notes make/list/archive/cat/delete/edit` command forms remain available as aliases.
- **`jour prune`**: Delete all notes with empty bodies, including notes created before empty-note checks were added.
- **Hashtag tags**: Whole-word hashtags in note bodies (for example `#helloworld` or `#this-great-day`) are indexed as tags without the leading `#`, alongside tags supplied with `--tag`.
- **`jour tags list`**: List all tags used across your notes. The local SQLite index is refreshed from note files before tag queries, so tags added by editors that return before saving are included.
- **`jour tags show <tag>`**: Show all notes associated with a specific tag.
- **`jour search <query>`**: Fast, grep-based full-text search across all your journal entries. Use `-q`/`--query` to apply a JMESPath expression to the matching structured note records and emit the result as JSON.
- **Repo-local journals**: The first interactive note-related command in a Git repository asks whether to use `./.jour` for that repository. Answering no records the repository in `~/.jour/.jourignore` and uses the global journal. Non-interactive commands use the global journal unless repo-local storage already exists. Use `jour -g <command>` to explicitly use global data from a repository.
- **`jour init`**: Initialize repo-local storage and its tag index explicitly without a prompt. This must be run inside a Git repository; it also removes that repository from `~/.jour/.jourignore` if present.

## Storage & Architecture

- **Replaceable note storage**: Commands use the `NoteStore` CRUD interface rather than performing note persistence themselves. The default `FileSystemNoteStore` keeps notes as flat files (`~/.jour/*.jmd`) with YAML front matter; note-store, editor, configuration, and dependency factories are wired at the CLI composition root and can be replaced in tests.
- **Robust identifiers**: Notes are identified by the extension-free ID shown by `jour list`, based on a chronological prefix and UUID suffix (`{YYYYmmddHHMMSS}_{8-char uuid hex}`). The filesystem backend adds the configured extension when storing notes.
- **SQLite Tag Index**: The default filesystem store maintains tag queries (`tags list` and `tags show`) in the lightweight SQLite index (`~/.jour/jour.db`). Its location can be changed with `database.path` in `~/.jour/.jourconfig`.
- **Storage scope**: Repo-local notes and their SQLite tag index are stored together in `./.jour`. Add `.jour/` to the repository's `.gitignore` to keep journal content out of commits. `~/.jour/.jourignore` contains absolute repository paths that should always use global data.
- **Code organization**: Command handlers and CLI wiring live in `jour_cli/cmd/`; storage interfaces and implementations live in `jour_cli/storage/`; command history is in `jour_cli/history.py`; app configuration remains in `jour_cli/config.py`. Loading configuration does not initialize the tag-index database.
- **Testing**: Testing is performed inside fresh Podman containers to ensure total environment isolation from the host machine, matching the project's strict dependency rules.

## Installation

The CLI requires `pipx` for a clean, isolated installation without breaking system Python packages.

To install or update the tool:
```bash
./install.sh
```
This script will check for `pipx` (installing it via Homebrew if missing), and then install `jour` into `~/.local/bin`. Ensure that directory is in your `$PATH`.

## Uninstallation

To remove the CLI:
```bash
./uninstall.sh
```

If you also wish to permanently wipe all of your journal notes, tags, and database configurations, pass the removal flag:
```bash
./uninstall.sh --remove-all-data
```

## Testing

Testing is exclusively executed inside Podman containers. We do not install dependencies or execute test suites directly on the host machine to guarantee pristine environment isolation.

To build the container image and execute the test suites (smoke, tags, cat, delete):
```bash
./podman-test.sh
