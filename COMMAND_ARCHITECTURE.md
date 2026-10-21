# Commands and State Architecture

This guide describes how to add a command to Jour and how its state models are
intended to be used. Jour uses explicit state boundaries and a small note
lifecycle; it does not use a general-purpose state-machine framework.

## Architecture at a glance

A CLI invocation passes through these boundaries:

```text
Typer parsing
    -> CommandState
    -> AppFactory and StorageContext
    -> command handler
    -> NoteDocument / NoteLifecycle as needed
    -> NoteStore
```

Each boundary answers a different question:

| Boundary | Question | Main implementation |
| --- | --- | --- |
| Command state | What did the user ask Jour to do? | `CommandState` in `jour_cli/cmd/cli.py` |
| Location context | Which journal and index does this invocation use? | `StorageContext` and `StoragePrompt` in `jour_cli/config.py` |
| Note document | What metadata and body does this note contain? | `NoteDocument` in `jour_cli/shared/note_document.py` |
| Note lifecycle | Is a create/edit draft valid, saved, rejected, or discarded? | `NoteLifecycle` in `jour_cli/shared/note_lifecycle.py` |
| Persistence | How is a note read or changed? | `NoteStore` in `jour_cli/storage/note_store.py` |

State should be modeled where its rules belong. The CLI owns command syntax,
configuration owns storage selection, note formats own body validation, and
commands own the requested operation and its user-facing outcome.

## Adding a command

For a typical note operation, use this sequence.

### 1. Define the handler

Create a module under `jour_cli/cmd/`, with a function that accepts parsed
arguments and the shared `AppFactory`. Fetch configuration and the store from
the factory rather than constructing filesystem or database dependencies in
the handler.

For example, `delete_note` in `jour_cli/cmd/delete.py` is intentionally small:

```python
def delete_note(args, app_factory):
    config = app_factory.get_config()
    note_store = app_factory.get_note_store(config)
    if note_store.delete(args.hash):
        app_factory.dependencies.write_stdout(f"Note {args.hash} deleted.")
    else:
        app_factory.dependencies.write_stderr(f"Error: Note {args.hash} not found.")
        app_factory.dependencies.exit(1)
```

Follow the dependency-injection style already used by neighboring handlers:

* Use `app_factory.dependencies` for I/O, confirmation, and process exit.
* Use `app_factory.get_config()` and `app_factory.get_note_store(config)` for
  location-aware storage.
* Keep persistence behind `NoteStore`; do not access note files directly from
  the command.
* Report failures explicitly through the existing stderr/exit pattern.

`jour watch` is an intentionally long-running command scoped to global
filesystem storage. It persists note paths to the SQLite index database before
processing them and reconciles the directory on startup so edits or deletions
made while it was stopped are picked up after restart.

### 2. Register syntax in the Typer CLI

Import the handler in `jour_cli/cmd/cli.py` and declare a Typer command with
help text, typed arguments, and options. Route it through `run_cmd` so it gets
the normalized command path, parsed argument state, and command-history
logging:

```python
@app.command()
def delete(
    hash: str = typer.Argument(..., help="Note hash"),
):
    """Delete a note."""
    run_cmd(("delete",), delete_note, positional=("hash",), hash=hash)
```

Use a canonical command path tuple. Mark positional argument names in
`positional=...`; remaining values are classified as options. `CommandState`
then exposes both groups and converts them to the `SimpleNamespace` expected
by current handlers.

If the same operation has grouped and top-level spellings, register the
additional spelling to the same Typer handler, as the note commands do. Do not
implement command behavior twice for aliases. Keep the canonical path stable
so history uses a predictable command name.

`history` currently handles its small logging flow directly instead of calling
`run_cmd`; follow the shared path for new ordinary commands unless the command
has a specific reason to differ.

### 3. Test the behavior and wiring

Add focused tests in the relevant existing test modules:

* Handler tests: success, not-found, invalid input, and persistence effects.
* CLI tests: command registration, parsed arguments, canonical command path,
  and aliases if exposed.
* State tests: add a test at the state boundary if the command introduces or
  changes a state transition.

Prefer assertions on observable results—store calls, output, exit status, and
selected context—rather than internal implementation details.

### 4. Update user documentation

Add the command to the Commands section in `README.md`, including meaningful
flags and behavior. If it introduces a new persistent format or scope rule,
document compatibility and migration implications too.

### When a command needs more than a handler

Use existing shared models rather than adding another interpretation of note
state:

* Read and validate note content with `NoteDocument.from_content(...)`.
* Apply tags or KVP changes with `add_tag`, `remove_tag`, or `set_kvp`.
* For create/edit flows, create a `NoteLifecycle.draft(content)`, call
  `validate(app_factory.note_formats)`, and handle rejected results before
  reporting success.
* Use `app_factory.get_location_context()` when the command needs to inspect
  the selected scope itself. Most handlers should just use `get_config()`.

Avoid moving note-type checks into a command or inferring storage scope from
the current directory after the factory has resolved it.

## State-dependent behavior

State should clarify what is valid and what outcome to expect, not silently
change the meaning of a command.

Examples of appropriate state-dependent behavior:

* Location detection may produce a ready `StorageContext` or a
  `StoragePrompt`. Resolution handles the interactive choice and associated
  directory/ignore-file effects.
* A note's `type` selects a registered body validator.
* An empty edited note triggers the existing delete confirmation and either
  discard or restore behavior.
* Archiving an already archived note is idempotent; the requested action
  remains “archive.”

For a new command, write down its important transitions before implementing
them. For example:

```text
note found + archive requested -> archive tag present
note missing + archive requested -> explicit error; no mutation
already archived + archive requested -> success; no unnecessary update
```

Add code and tests for meaningful branches, including failure to persist.
Keep transition rules near the domain operation that owns them. A shared
policy/helper is appropriate only if multiple handlers need the same rule.

## Note lifecycle

`NoteLifecycle` models the content validation portion of create/edit:

```text
draft --validate succeeds--> validated --persistence succeeds--> saved
  |                              |
  +--validation fails--> rejected
                                 +--discard--> discarded
```

The lifecycle object is immutable: each transition returns a new state, and
invalid transition ordering raises `ValueError`. It does not itself save,
restore, or delete data. The command coordinates those side effects with the
store and translates outcomes into CLI messages.

Current behavior to preserve when changing these flows:

* Invalid JSON must not remain persisted.
* Invalid edits restore the original note when possible.
* Empty editor-created notes are removed.
* Empty existing notes require confirmation; declining restores the original.
* Store failures must be reported and must not be described as successful
  transitions.

## Extending note formats

`NoteFormat`, `NoteFormatRegistry`, and `create_default_note_formats()` are
public imports from `jour_cli`. A format implements a `name` and
`parse_body(body)` method. The registry checks that its result is
JSON-serializable, which allows structured data to be included in JMESPath
query records.

An embedding application can create a default registry, register a format,
and pass it as `note_formats` to `AppFactory`. This is an application API, not
a CLI plugin loader. The standalone `jour` CLI currently exposes the built-in
Markdown and JSON formats only.

Unknown declared types remain parseable as documents and can be listed or
displayed, but create/edit validation rejects them unless the active registry
has a matching format. Do not assume an unknown format has Markdown
validation semantics.

## OCP and extension limits

Jour applies the Open/Closed Principle selectively:

* **Formats:** open to extension through `NoteFormatRegistry`.
* **Persistence:** commands depend on `NoteStore`, so another backend can
  implement the same interface.
* **Built-in commands:** intentionally registered explicitly in Typer. Adding
  a first-party command means editing the CLI registry and documentation.
* **Storage scopes:** detection is separated from prompting and effects, but a
  genuinely new scope still needs deliberate changes to the scope/context and
  resolution rules.

This keeps the product's command surface discoverable instead of turning it
into a dynamic plugin system prematurely. Avoid a generic command registry or
state engine until there is a real second consumer or repeated logic that the
abstraction would simplify.

## Caveats

* `CommandState` is a normalized snapshot of a command invocation, not a
  persisted workflow or a general transition engine.
* `AppFactory` is created at module import time for the standalone CLI. Its
  location context is cached and reset by `set_global_mode`; do not treat it
  as a multi-command server session without defining a separate lifecycle.
* The note lifecycle models validation outcomes, while persistence remains
  outside it. A `saved` transition is only valid after the caller has actually
  completed the corresponding store operation.
* The editor currently writes changes through `NoteStore.edit` before the
  command validates the resulting content. Create/edit handlers therefore
  remove or restore files when validation fails; they are not transactional
  drafts isolated from storage.
* `NoteDocument` retains original serialized content for normal reads, but
  metadata edits serialize YAML front matter again. Formatting, quoting, or
  comments in front matter may therefore be normalized by metadata changes.
* `NoteStore` is the persistence seam, but the current filesystem store and
  SQLite tag index are still the only built-in backend.
* A format registry is injected into note lifecycle and query paths. If an
  embedding application has custom formats, it should use the same registry
  consistently wherever it validates or queries those notes.
