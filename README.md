# jour

A fast, minimal command-line journaling tool written in Python.

☕️ [Buy me a coffee](https://www.google.com/search?q=https://www.buymeacoffee.com/hayescs4)

> **Alpha software:** `jour` is in active development. Commands, configuration, and storage formats may change between releases.

---

## Demo

Open an interactive shell with the CLI in a Podman container and an isolated,
persistent demo journal:

```bash
./demo.sh
```

The script builds the image and opens a shell where you can run `jour` commands.
Each container gets a unique name, and demo data persists in the
`jour-demo-data` Podman volume between runs. `nano` is configured as the
container's editor, so `jour make` opens an interactive note editor.

---

## Installation

Requires `pipx` for clean, isolated installation without modifying system Python packages.

```bash
./install.sh

```

This script checks for `pipx` (installing it via Homebrew if missing), installs `jour` to `~/.local/bin`, and requires that directory to be in your `$PATH`.

On macOS, install the global notes watcher as a per-user LaunchAgent after installing Jour:

```bash
./install-watcher.sh
```

The script is safe to rerun; it updates and restarts `com.jour.global-watcher`. The agent starts at login and restarts if it exits. Its output is written to `~/.jour/watcher.log`, including filesystem events, startup reconciliation, index updates, and processing errors. To stop and remove the agent, run `launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jour.global-watcher.plist"` and remove that plist.

---

## Commands

* **`jour --version`**: Display the installed Jour version.
* **`jour make`**: Create a new Markdown note by default. Pass text via `-n`/`--note`, pipe via stdin (`cat file.txt | jour make`), or open your default editor (`$VISUAL` or `$EDITOR`). Use `--type json` to create a JSON document note in the `.jmd` body; its YAML front matter records `type: json`. JSON note bodies must be valid JSON objects. Empty Markdown bodies are discarded.
* **`jour list`**: Display notes chronologically with hash, tags, and content preview. Add `--show-archived` to include notes tagged `jour-archive`, or use `-q`/`--query` with a JMESPath expression to output structured records as JSON. Query records include `type` (`markdown` or `json`), `data` (the parsed JSON object for JSON notes, otherwise `null`), and `kvp` (the parsed front-matter key/value mapping). JSON document fields are also available at the record root for direct JMESPath filtering.
* **`jour archive <hash>`**: Hide a note from default lists by tagging it `jour-archive`. Use `jour archive --undo <hash>` to restore it.
* **`jour cat <hash>`**: View full note content and YAML front matter.
* **`jour edit <hash>`**: Open a note for editing. Clearing the body prompts for deletion confirmation.
* **`jour add-kvp -k <key> -v <value> <hash>`**: Add or replace a string key/value pair in a note's front matter. KVP data remains available to JMESPath queries.
* **`jour delete <hash>`**: Permanently delete a note and remove it from the index.
* **`jour prune`**: Delete all notes with empty bodies.
* **`jour rebuild`**: Rebuild the tag and key/value indexes from the current note files, removing entries for notes that were deleted outside Jour.
* **`jour watch`**: Keep the global tag and key/value indexes current as note files change. Run it as a long-lived process; changes are debounced for one second, pending work is stored in SQLite, and files are reconciled when the watcher starts.
* **`jour index --status`**: Show when the index was last rebuilt and how many indexed notes have been deleted from disk.
* **`jour init`**: Explicitly initialize repo-local storage and its metadata index inside a Git repository.
* **`jour git init`**: Initialize a dedicated Git repository in the active Jour storage directory. `jour git commit` commits changes to note files only (using the configured storage extension); metadata and other staged files are not included. Use `-m`/`--message` to set a commit message (default: `Update notes`). Add `-g` before the command to track the global journal instead.
* **`jour tags list`**: List all tags used across your notes.
* **`jour tags show <tag>`**: Display all notes associated with a specific tag.

---

## Configuration & Storage

* **File Storage**: Flat files (`~/.jour/*.jmd`) with YAML front matter.
* **Identifiers**: Chronological prefix with a UUID suffix (`{YYYYmmddHHMMSS}_{8-char uuid hex}`).
* **Tag and Key/Value Index**: Lightweight SQLite database (`~/.jour/jour.db`) indexes tags and `kvp` front matter. Location is configurable via `database.path` in `~/.jour/.jourconfig`.
* **Global note watcher**: `jour watch` always watches the global storage directory, even when started inside a repository. It uses the platform's native file events where available. Configure it to start at login with your operating system's service manager if continuous background monitoring is desired. On startup it reconciles files with the index, and queued events remain available after an interrupted run.

Notes can include string-keyed, JSON-compatible values in a `kvp` YAML front-matter mapping. These values are stored in the SQLite index and available in JMESPath queries, for example `jour list -q "[?kvp.key1 == 'value1'].id"`:

```yaml
kvp:
  key1: value1
  key2: value2
  key3: value3
```
* **Repo-Local Journals**: Interactive commands prompt to use `./.jour` inside Git repositories. Answering no adds the path to `~/.jour/.jourignore`. Use `jour -g` to force global storage from inside a repo.
* **Aliases**: Legacy `jour notes make/list/archive/cat/delete/edit` commands remain supported.

## Execution Model

Each invocation is handled as three related states:

* **Command state** captures the normalized command path, positional arguments, and options; top-level and grouped aliases execute the same command handler.
* **Location context** first detects global or repo-local scope without prompting or creating directories, then resolves any interactive choice and its side effects once for the command's application context. `jour init` explicitly creates repo-local storage.
* **Note document** parses common front matter and body content while retaining the original serialized note. Body validation is delegated to an injected note-format registry; Markdown and JSON are built in, and applications can register additional validators that expose structured data to JMESPath. Create/edit follow explicit `draft → validated → saved` transitions, with rejected and discarded outcomes; archive and KVP operations express metadata changes as document transitions.

These boundaries keep CLI syntax, storage selection, note-format validation, and persistence separate without requiring a general-purpose state-machine framework. The `NoteStore` interface remains the persistence seam for future storage backends.

For a contributor guide to adding commands and working with these state models, see [Command and State Architecture](./COMMAND_ARCHITECTURE.md).

To extend formats in an embedding application, import `NoteFormat`, `NoteFormatRegistry`, and `create_default_note_formats()` from `jour_cli`. Register an object implementing `name` and `parse_body(body)`, then pass the registry to `AppFactory` as `note_formats`. The parser validates the body and may return any JSON-serializable structured value for JMESPath queries; the registry checks that contract. The standalone CLI uses the built-in Markdown and JSON formats.

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