# jour

A fast, minimal command-line journaling tool written in Python[cite: 1].

☕️ [Buy me a coffee](https://www.google.com/search?q=https://www.buymeacoffee.com/hayescs4)[cite: 1]

> **Alpha software:** `jour` is in active development. Commands, configuration, and storage formats may change between releases[cite: 1].

---

## Installation

Requires `pipx` for clean, isolated installation without modifying system Python packages[cite: 1].

```bash
./install.sh

```

This script checks for `pipx` (installing it via Homebrew if missing), installs `jour` to `~/.local/bin`, and requires that directory to be in your `$PATH`[cite: 1].

---

## Commands

* **`jour make`**: Create a new note[cite: 1]. Pass text via `-n`/`--note`, pipe via stdin (`cat file.txt | jour make`), or open your default editor (`$VISUAL` or `$EDITOR`)[cite: 1]. Empty bodies are discarded[cite: 1].
* **`jour list`**: Display notes chronologically with hash, tags, and content preview[cite: 1]. Add `--show-archived` to include archived notes, or use `-q`/`--query` with a JMESPath expression to output structured records as JSON[cite: 1].
* **`jour archive <hash>`**: Hide a note from default lists by tagging it `jour-archive`[cite: 1]. Use `jour archive --undo <hash>` to restore it[cite: 1].
* **`jour cat <hash>`**: View full note content and YAML front matter[cite: 1].
* **`jour edit <hash>`**: Open a note for editing[cite: 1]. Clearing the body prompts for deletion confirmation[cite: 1].
* **`jour delete <hash>`**: Permanently delete a note and remove it from the tag index[cite: 1].
* **`jour prune`**: Delete all notes with empty bodies[cite: 1].
* **`jour init`**: Explicitly initialize repo-local storage and its tag index inside a Git repository[cite: 1].
* **`jour tags list`**: List all tags used across your notes[cite: 1].
* **`jour tags show <tag>`**: Display all notes associated with a specific tag[cite: 1].

---

## Configuration & Storage

* **File Storage**: Flat files (`~/.jour/*.jmd`) with YAML front matter[cite: 1].
* **Identifiers**: Chronological prefix with a UUID suffix (`{YYYYmmddHHMMSS}_{8-char uuid hex}`)[cite: 1].
* **Tag Index**: Lightweight SQLite database (`~/.jour/jour.db`)[cite: 1]. Location is configurable via `database.path` in `~/.jour/.jourconfig`[cite: 1].
* **Repo-Local Journals**: Interactive commands prompt to use `./.jour` inside Git repositories[cite: 1]. Answering no adds the path to `~/.jour/.jourignore`[cite: 1]. Use `jour -g` to force global storage from inside a repo[cite: 1].
* **Aliases**: Legacy `jour notes make/list/archive/cat/delete/edit` commands remain supported[cite: 1].

---

## Testing

Tests run inside Podman containers to maintain strict environment isolation from the host[cite: 1].

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