# jour — Minimal CLI Journal

A minimal, fast, command-line journaling tool written in Python.

## Features

- **`jour notes make`**: Create a new note. You can pass the note body directly via the `-n`/`--note` flag, pipe it via stdin (e.g., `cat file.txt | jour notes make`), or simply run the command to open your default editor (`$VISUAL` or `$EDITOR`).
- **`jour notes list`**: Display a list of all your notes, sorted chronologically. Shows the note hash, applied tags, and a brief preview of the content.
- **`jour notes cat <hash>`**: View the full content and YAML front matter of a specific note by its hash identifier.
- **`jour notes delete <hash>`**: Delete a specific note from your storage and the tag index.
- **`jour tags list`**: List all tags used across your notes. Powered by a local SQLite index for O(1) instantaneous lookups.
- **`jour tags show <tag>`**: Show all notes associated with a specific tag.
- **`jour search <query>`**: Fast, grep-based full-text search across all your journal entries.

## Storage & Architecture

- **Flat Files**: Notes are stored as flat files (`~/.jour/*.jmd`) with YAML front matter, ensuring your data is portable, human-readable, and free from vendor lock-in.
- **Robust Naming**: Files use a chronological prefix and a UUID suffix (`{YYYYmmddHHMMSS}_{8-char uuid hex}.jmd`), making them easily sortable chronologically while completely preventing overwrite collisions in tight automation loops.
- **SQLite Tag Index**: Tag queries (`tags list` and `tags show`) are backed by a lightweight SQLite index (`~/.jour/jour.db`). This avoids O(n) file parsing and keeps queries instant as your journal grows.
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
```
