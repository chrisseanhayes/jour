# jour

A fast, minimal command-line journaling tool written in Python.

☕️ [Buy me a coffee](https://www.google.com/search?q=https://www.buymeacoffee.com/hayescs4)

> **Alpha software:** `jour` is in active development. Commands, configuration, and storage formats may change between releases.

---

## Installation

Requires `pipx` for clean, isolated installation without modifying system Python packages.

```bash
./install.sh

```

This script checks for `pipx` (installing it via Homebrew if missing), installs `jour` to `~/.local/bin`, and requires that directory to be in your `$PATH`.

---

## Commands

* **`jour make`**: Create a new note. Pass text via `-n`/`--note`, pipe via stdin (`cat file.txt | jour make`), or open your default editor (`$VISUAL` or `$EDITOR`). Empty bodies are discarded.
* **`jour list`**: Display notes chronologically with hash, tags, and content preview. Add `--show-archived` to include archived notes, or use `-q`/`--query` with a JMESPath expression to output structured records as JSON.
* **`jour archive <hash>`**: Hide a note from default lists by tagging it `jour-archive`. Use `jour archive --undo <hash>` to restore it.
* **`jour cat <hash>`**: View full note content and YAML front matter.
* **`jour edit <hash>`**: Open a note for editing. Clearing the body prompts for deletion confirmation.
* **`jour delete <hash>`**: Permanently delete a note and remove it from the tag index.
* **`jour prune`**: Delete all notes with empty bodies.
* **`jour init`**: Explicitly initialize repo-local storage and its tag index inside a Git repository.
* **`jour tags list`**: List all tags used across your notes.
* **`jour tags show <tag>`**: Display all notes associated with a specific tag.

---

## Configuration & Storage

* **File Storage**: Flat files (`~/.jour/*.jmd`) with YAML front matter.
* **Identifiers**: Chronological prefix with a UUID suffix (`{YYYYmmddHHMMSS}_{8-char uuid hex}`).
* **Tag Index**: Lightweight SQLite database (`~/.jour/jour.db`). Location is configurable via `database.path` in `~/.jour/.jourconfig`.
* **Repo-Local Journals**: Interactive commands prompt to use `./.jour` inside Git repositories. Answering no adds the path to `~/.jour/.jourignore`. Use `jour -g` to force global storage from inside a repo.
* **Aliases**: Legacy `jour notes make/list/archive/cat/delete/edit` commands remain supported.

---

## Testing

Tests run inside Podman containers to maintain strict environment isolation from the host.

```bash
./podman-test.sh

```

---

## Uninstallation

```bash
./uninstall.sh

```

To permanently wipe all notes, tags, and database configurations:

```bash
./uninstall.sh --remove-all-data

```