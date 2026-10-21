# `jour` — Git History Code Review

> A principles-first analysis of the `jour` CLI's evolution: refactoring patterns, feature additions, and architectural decisions evaluated against SOLID principles and clean design heuristics.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Commit History at a Glance](#commit-history-at-a-glance)
3. [Refactoring Arcs](#refactoring-arcs)
4. [Feature Additions](#feature-additions)
5. [Architecture Deep-Dive](#architecture-deep-dive)
6. [SOLID Principles Analysis](#solid-principles-analysis)
7. [Design Pattern Observations](#design-pattern-observations)
8. [Notable Observations](#notable-observations)
9. [Summary Scorecard](#summary-scorecard)

---

## Project Overview

`jour` is a personal journaling/note-taking CLI tool written in Python. It stores notes as front-matter-equipped Markdown (`.jmd`) files on the filesystem, backed by a SQLite metadata index. The project grew from a monolithic script into a layered, testable architecture over ~50 commits.

**Core concepts:**
- **Notes** — text documents with YAML front matter (tags, KVPs, note type)
- **NoteStore** — persistence interface (filesystem + SQLite index)
- **Dependencies** — injectable bundle of I/O, platform, and time primitives
- **AppFactory** — assembly root that wires config → dependencies → store → commands

---

## Commit History at a Glance

```
init ──► argparse monolith ──► Typer migration ──► DI injection ──► modular cmd split
      ──► full dependency refactor (d65da56) ──► state-machine (8a1d9f5)
      ──► feature additions (json notes, kvp, tags, rebuild, archive, prune, git, watcher)
```

| Era | Key Commits | Theme |
|---|---|---|
| Bootstrap | `init`, `pipe notes`, `implement notes cat/delete` | Raw prototype |
| CLI Framework | `f927fbf` — argparse → Typer | Ergonomics |
| DI Injection | `bc63eff`, `603cb4a` | Testability |
| Module Split | `820bfbd` — split `notes.py` | SRP awareness |
| Full Restructure | `d65da56` — 40 files, 1382 insertions | Architecture |
| State Machine | `8a1d9f5` — 22 files, 1143 insertions | Domain modeling |
| Feature Burst | tags, kvp, json notes, prune, archive, rebuild, git, watcher | Capability growth |

---

## Refactoring Arcs

### 1. argparse → Typer (`f927fbf`)

The earliest notable cleanup replaced Python's stdlib `argparse` with [Typer](https://typer.tiangolo.com/). This was a **surface-level refactor** — the command logic stayed in `main.py`, but argument declarations became declarative type-annotated functions. The gain was readability and reduced boilerplate; the tradeoff is a new framework dependency.

**Assessment:** Appropriate early cleanup; no architectural change yet.

---

### 2. File Operations Dependency Injection (`bc63eff`, `603cb4a`)

`notes.py` gained a `FileOperations` parameter rather than calling `os` directly. This was the first explicit acknowledgment that I/O coupling hurts testability.

```python
# Before: direct os calls inside notes.py
# After: injected FileOperations wrapper
def make_note(args, file_ops: FileOperations): ...
```

**Assessment:** Correct direction, but incomplete — the rest of the codebase still called `os` directly. The refactor seeded the idea rather than fully delivering on it.

---

### 3. Module Split: `notes.py` → `notes/` package (`820bfbd`)

A single 150+ line `notes.py` was split into per-command files under a `notes/` package: `_make.py`, `_edit.py`, `_list.py`, `_cat.py`, `_delete.py`. A shared `file_ops.py` housed path utilities.

```
Before:  notes.py (everything)
After:   notes/
           _make.py   _edit.py   _list.py
           _cat.py    _delete.py  file_ops.py
```

**Assessment:** Direct SRP response — each command got its own file. The underscore-prefixed naming convention signals "internal", which is idiomatic Python.

---

### 4. The Grand Restructure (`d65da56` — ~40 files touched)

The largest single commit. It introduced the full layered architecture that remains today:

```
jour_cli/
  app_factory.py        ← assembly root
  config.py             ← config loading
  cmd/                  ← Typer command wiring
    cli.py              ← main app, sub-typers
    notes/              ← note sub-commands
  shared/
    dependencies.py     ← I/O + runtime bundle
    note_content.py     ← content parsing
    note_input.py       ← stdin/editor input
    editor.py           ← editor abstraction
  storage/
    note_store.py       ← NoteStore ABC
    filesystem_note_store.py
    sqlite_tag_index.py
    factory.py
  history.py
```

Old files removed: `notes/`, `db.py`, `logging.py`, `search.py`, `tags.py`, `shared/file_ops.py`.

**Assessment:** A well-executed rearchitecture. The `Dependencies` god-object is the most debatable choice (see SOLID analysis below), but the overall layering is clean and testability improved dramatically.

---

### 5. State-Machine Architecture (`8a1d9f5` — 22 files, 1143 insertions)

Introduced the most sophisticated domain modeling in the codebase:

- **`NoteDocument`** — an immutable `@dataclass(frozen=True)` parse result holding content, front matter, tags, body, and KVPs. Mutations return new instances (value object pattern).
- **`NoteLifecycle`** — an immutable state machine with explicit states: `DRAFT → VALIDATED → SAVED` (or `REJECTED` / `DISCARDED`). Invalid transitions raise `ValueError`.
- **`NoteFormatRegistry`** — a pluggable registry of note body validators (`markdown`, `json`), following the **Registry pattern** and open to extension.

```python
class NoteLifecycleState(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    SAVED = "saved"
    REJECTED = "rejected"
    DISCARDED = "discarded"
```

**Assessment:** The strongest domain modeling in the project. Explicit state transitions prevent invalid lifecycle progressions at the type level. The `COMMAND_ARCHITECTURE.md` doc written alongside this commit shows intentional design thinking.

---

## Feature Additions

| Feature | Commit | Notes |
|---|---|---|
| JMESPath query on `list` | `f7f3e9e` | Added `-q`/`--query` option to filter JSON output |
| Archive | `69c736e` | Tag-based soft-delete via `jour-archive` tag |
| Prune | `80fb19e` | Delete notes with empty bodies |
| Remove `notes` supercommand | `6a9dfcc` | Commands promoted to top-level (`jour make` instead of `jour notes make`) |
| Init (local journal) | `c5788b2` | Per-git-repo journal scoping via `.jour/` |
| `--version` | `27f71e7` | Typer callback version flag |
| Rebuild index | `bdc4086` | `jour rebuild` + `jour index --status` |
| Structured JSON notes | `f3f3f98` | JSON note type with validation on save |
| Indexed KVPs | `0bd1b36` | Key/value pairs stored in SQLite alongside tags |
| `add-kvp` command | `dd4856b` | CLI command to mutate note KVPs |
| Hash-based note tags | `deaee56` | Tag notes by hash (content-addressable ref) |
| Git support | `02ee890` | `jour git init` / `jour git commit` for note version control |
| File watcher indexer | `7e16f83` | `jour watch` — watchdog-backed live index sync |

**Feature growth pattern:** Features mostly added new files (`cmd/git.py`, `cmd/watch.py`, `storage/note_watcher.py`) rather than modifying existing ones. This is OCP-aligned behavior — the core is extended, not patched.

---

## Architecture Deep-Dive

### Layering Model

```
┌────────────────────────────────────────┐
│              cmd/ (Typer CLI)          │
│   cli.py → run_cmd() → cmd functions  │
└─────────────────┬──────────────────────┘
                  │ AppFactory
┌─────────────────▼──────────────────────┐
│           app_factory.py               │
│  config + dependencies + note store    │
└──────┬──────────────────────┬──────────┘
       │                      │
┌──────▼───────────────────────────────────────┐  ┌────────▼───────────────┐
│  shared/                                     │  │  storage/              │
│  Dependencies (Composite of IO, SQLite, AdHoc)│  │  NoteStore (ABC)       │
│  ├── IO (Filesystem & Path I/O)             │  │  FileSystemNoteStore   │
│  ├── SQLite (DB connection management)       │  │  SQLiteTagIndex        │
│  └── AdHoc (Clock, UUID, Streams, Shell, OS) │  │  factory.py            │
│  NoteDocument / NoteLifecycle / NoteFormats  │  │                        │
└──────────────────────────────────────────────┘  └────────────────────────┘
```

### The Segregated Dependencies Architecture (`IO`, `SQLite`, `AdHoc`)

The runtime environment is segregated into three focused dependency classes, composed into a unified `Dependencies` container:

1. **`IO` (`jour_cli.shared.dependencies.IO`)**: Isolates all filesystem and path operations (`read_file`, `write_file`, `append_file`, `remove_file`, `list_files`, `expanduser`, `path`, `realpath`, `get_git_root`, `basename`, `dirname`, `makedirs`, `exists`, `join`, `splitext`). Testable via custom `file_opener`, `path_expander`, and `working_directory`.
2. **`SQLite` (`jour_cli.shared.dependencies.SQLite`)**: Isolates database connection lifecycle and execution primitives (`connect()`, `connection_factory`, and the `connection()` context manager), decoupling storage factories and indices from direct `sqlite3.connect` calls.
3. **`AdHoc` (`jour_cli.shared.dependencies.AdHoc`)**: Groups miscellaneous runtime concerns that would otherwise clutter interfaces into an ad-hoc dependency bundle: clock (`now`), UUID generation (`new_uuid_hex`), streams (`stdin_read`, `write_stdout`, `write_stderr`), process lifecycle (`exit`), platform queries (`is_macos`), environment variables (`get_environment_variable`), subprocess invocation (`run_command`), confirmation prompts (`confirm`), and logger.
4. **`Dependencies` (`jour_cli.shared.dependencies.Dependencies`)**: A composite container that holds `self.io: IO`, `self.sqlite: SQLite`, and `self.adhoc: AdHoc`. It exposes delegated methods for seamless backwards compatibility across the application and existing tests while allowing callers and tests to inject any of the three collaborators independently.

> [!NOTE]
> This structure resolves the monolithic god-object critique while retaining the ergonomic convenience of a single top-level bundle for command dispatch.

### `CommandState` Pattern

[`cli.py`](file:///Users/chrishayes/Desktop/code/jour/jour_cli/cmd/cli.py) introduces `CommandState` — a frozen dataclass capturing command path + positional args + options. The `run_cmd()` dispatcher constructs it, logs the invocation, and passes a `SimpleNamespace` args object to the actual command function. This unifies the logging cross-cut cleanly.

### Storage Abstraction

[`NoteStore`](file:///Users/chrishayes/Desktop/code/jour/jour_cli/storage/note_store.py) is a proper `ABC` with abstract methods for CRUD + search + tagging + index management. [`TagIndex`](file:///Users/chrishayes/Desktop/code/jour/jour_cli/storage/note_store.py) is a `Protocol` (structural typing) used by `FileSystemNoteStore` to decouple it from `SQLiteTagIndex` concretely.

---

## SOLID Principles Analysis

### S — Single Responsibility Principle

**Adherence: ★★★★☆ (Strong, with segregated dependencies)**

The module split (`820bfbd`) and grand restructure (`d65da56`), along with the dependency segregation, show clear SRP intent. By current state:

- `cmd/` files: each handles one command ✅
- `NoteDocument`: parsing and immutable manipulation only ✅
- `NoteLifecycle`: state transitions only ✅
- `NoteFormatRegistry`: body validation/parsing only ✅
- `SQLiteTagIndex`: index CRUD only ✅
- `history.py`: focused 53-line history log/read module ✅
- **`IO`**: dedicated purely to file and path operations ✅
- **`SQLite`**: dedicated purely to database connection management ✅
- **`AdHoc`**: groups miscellaneous runtime utilities (clock, streams, process, env) without polluting I/O or database domains ✅
- **`Dependencies`**: acts purely as a composite / facade aggregating `IO`, `SQLite`, and `AdHoc` ✅

**Secondary SRP tensions:**

- **[`note_content.py`](file:///Users/chrishayes/Desktop/code/jour/jour_cli/shared/note_content.py)** — a utility bag of private functions covering parsing, serialization, hashtag extraction, front matter building, tag manipulation, and KVP mutation. Could reasonably be split into a parser, a serializer, and a builder.
- **`AppFactory`** — manages config loading, storage context caching, note store creation, editor creation, history logging, and history reading. Multiple responsibilities that share a lifecycle.
- **`cmd/index.py`** — parses raw command history lines with a regex to find the last rebuild time. History interpretation logic leaking into an index module.

---

### O — Open/Closed Principle

**Adherence: ★★★★☆ (Strong)**

The `NoteFormatRegistry` is the clearest example of OCP in the codebase:

```python
class NoteFormat(Protocol):
    name: str
    def parse_body(self, body: str) -> Any: ...

# New formats extend behavior without touching existing code:
registry.register(MyCustomFormat())
```

Adding a new note format (`json` was added in `f3f3f98`) required zero modification to parsing, validation, or storage logic. ✅

Similarly, new commands are added as new files in `cmd/` and registered in `cli.py`. No existing command files change. ✅

**Misses:**

[`cmd/watch.py`](file:///Users/chrishayes/Desktop/code/jour/jour_cli/cmd/watch.py) uses an `isinstance` check to ensure the note store is a `FileSystemNoteStore`, bypassing the `NoteStore` abstraction:

```python
if not isinstance(note_store, FileSystemNoteStore):
    raise TypeError("The global watch command requires filesystem note storage.")
```

The watch feature is coupled to a specific implementation rather than an interface. The `NoteStore` ABC could expose a `watch()` method or a capability flag to address this cleanly.

Additionally, `GlobalNoteWatcher` reaches into `note_store.tag_index` directly — an attribute that exists only on `FileSystemNoteStore`, completely invisible through the `NoteStore` ABC interface. This would silently break any alternative `NoteStore` implementation.

---

### L — Liskov Substitution Principle

**Adherence: ★★★☆☆ (Partial)**

`NoteStore` is abstract with a well-defined contract. `FileSystemNoteStore` implements all 11 methods. `CommandEditor` correctly satisfies the `Editor` ABC. `SQLiteTagIndex` fully satisfies the `TagIndex` Protocol. No LSP violations in existing implementations.

However, there is only **one concrete `NoteStore` implementation**. LSP can't be fully evaluated without multiple substitutable implementations. The architecture sets up well for it, but the principle isn't actively exercised across implementations.

---

### I — Interface Segregation Principle

**Adherence: ★★★☆☆ (Mixed)**

`NoteStore` is a fairly wide interface — 11 abstract methods covering CRUD, search, tagging, index rebuilding, and deletion counting. Some commands only need `get()` and `update()` (e.g. `edit`), but they receive the full store. The `search` method is **dead code** — no command currently calls it, yet every future implementation must provide it.

**`TagIndex` width:** The Protocol bundles two distinct concerns — tag read queries (`tag_counts`, `notes_for_tag`, `tags_by_note`, `kvp_by_note`) and the watcher's durable change queue (`enqueue_note_change`, `pending_note_changes`, `complete_note_change`). Commands that only need tag reads are still coupled to the full watcher-queue interface. A narrower `ReadableTagIndex` protocol would be cleaner.

**Minimal, well-segmented interfaces:**
- `NoteFormat` Protocol — just `name` and `parse_body(body)` ✅
- `DependenciesFactory` Protocol — just `create() -> Dependencies` ✅
- `Editor` ABC — exactly one abstract method ✅
- `IO` class — focused strictly on filesystem and path operations ✅
- `SQLite` class — focused strictly on database connectivity and connection lifecycle ✅

`Dependencies` segregation: By isolating file I/O into `IO` and database operations into `SQLite`, tests and collaborators that only perform file or SQLite operations can interact with or mock those segregated objects directly (`dependencies.io`, `dependencies.sqlite`). The remaining miscellaneous environment concerns are housed in `AdHoc`.

---

### D — Dependency Inversion Principle

**Adherence: ★★★★★ (Significantly strengthened with SQLite & IO segregation)**

This is the project's greatest structural strength. The DIP journey is visible across multiple commits:

| Commit / Refactor | DIP Step |
|---|---|
| `bc63eff` | Inject `FileOperations` rather than call `os` directly |
| `d65da56` | Full `Dependencies` bundle; `NoteStore` ABC; `TagIndex` Protocol |
| `factory.py` | `DatabaseConnectionFactory` injected into `FileSystemNoteStoreFactory` |
| `AppFactory` | Assembly root binds all collaborators; commands depend only on interfaces |
| **Current Refactor** | Segregate `IO`, `SQLite`, and `AdHoc`; decouple `cmd/cli.py` from `sqlite3.connect` via `dependencies.sqlite` |

High-level modules (`cmd/`) depend on abstractions (`NoteStore`, `Dependencies`). Low-level modules (`FileSystemNoteStore`, `SQLiteTagIndex`) are injected at startup. Tests can substitute fakes at the `Dependencies` or `NoteStore` level without touching command code. With `dependencies.sqlite`, `FileSystemNoteStoreFactory` no longer requires `cmd/cli.py` to import `sqlite3.connect` directly. ✅

`GlobalNoteWatcher` also takes `observer_factory` and `sleep` callables, enabling test injection without a real filesystem watcher. ✅

**Specific remaining violations:**

1. **`cmd/watch.py` → `FileSystemNoteStore` (concrete)** via `isinstance` check
2. **`_NoteChangeHandler`** — constructor typed to `FileSystemNoteStore`, not `NoteStore`
3. **`GlobalNoteWatcher`** — accesses `note_store.tag_index` directly (concrete attribute, absent from the `NoteStore` interface); these three compound each other
4. **`Dependencies.confirm()`** — calls `typer.confirm()` directly, injecting a Typer framework dependency into a class intended to be framework-agnostic
5. **`NoteDocument.validate_body()` / `structured_data()`** — default to the module-level singleton `DEFAULT_NOTE_FORMATS`, making the format registry "ambient" rather than purely injected; test vs. production behavior can silently diverge if tests omit an explicit registry

---

## Design Pattern Observations

### Value Object / Immutable Data

`NoteDocument` and `NoteLifecycle` are both `@dataclass(frozen=True)`. Mutations return new instances. This makes note processing pipelines easy to reason about and thread-safe.

### State Machine

`NoteLifecycle` encodes valid transitions explicitly. Attempting `mark_saved()` from `DRAFT` raises `ValueError`. This is a small but well-executed state machine — far better than ad-hoc boolean flags.

> [!NOTE]
> One documented caveat (in `COMMAND_ARCHITECTURE.md`): the editor writes to disk *before* validation occurs. If validation fails, the command must clean up. The lifecycle models the *validation outcome*, not a true transactional draft — an honest design acknowledgment.

### Registry

`NoteFormatRegistry` is a clean plugin registry: formats are registered by name and looked up at parse time. The `copy()` method enables test isolation.

### Factory / Abstract Factory

`AppFactory` is the composition root. `FileSystemNoteStoreFactory` is a callable factory injecting `sqlite3.connect`. `DefaultDependenciesFactory` wraps the production `Dependencies`.

### Adapter / Wrapper

`Dependencies` is an adapter over stdlib (`os`, `subprocess`, `sys.stdin`, etc.), making those seams injectable.

### Command Object

Each `cmd/*.py` file is effectively a Command object: a callable that receives `args` and `app_factory`. The `run_cmd()` dispatcher in `cli.py` acts as a broker adding logging as a cross-cutting concern.

### Observer / Event Handler

`_NoteChangeHandler` extends watchdog's `FileSystemEventHandler`. Instead of processing events synchronously, it immediately writes the changed filepath to the `pending_note_changes` SQLite table — durable, crash-safe, and debounce-ready.

### Durable Queue + Optimistic Concurrency

The watcher uses a revision counter per queued change. `complete_note_change(filepath, revision)` only removes the row if the revision still matches, preventing a race where a new write event arrives while an old one is being processed. This is a thoughtful engineering choice for a background daemon.

---

## Notable Observations

> [!WARNING]
> **`_refresh_tag_index()` is O(n) on every read.** It is called before `list()`, `tag_counts()`, and `notes_for_tag()` — reading every `.jmd` file from disk and re-indexing on each invocation. For a small personal journal this is fine, but it will not scale. The `jour watch` daemon exists precisely to keep the index warm; for users not running the watcher, every read command is a full scan.

- **`history` command bypasses `run_cmd`** — it directly accesses `app_factory` inline rather than following the standard dispatcher pattern. Acknowledged in `COMMAND_ARCHITECTURE.md` as an intentional inconsistency.

- **Dual command registration** — note commands exist at both `jour notes make` and `jour make` via `app.command("make")(notes_make)`. No code duplication; pure Typer function aliasing.

- **`AppFactory` is a module-level singleton** in `cmd/cli.py`. `set_global_mode()` mutates cached state in `_location_context`. Correct for single CLI invocations but would be problematic in any multi-call or server context.

- **`note_content.py` private functions are publicly re-exported** — all `_`-prefixed functions are imported in `__init__.py`, blurring the private/public API boundary.

- **`_resolve_filename_from_history`** parses raw history log lines with `shlex.split` to extract the last token. Fragile: depends on the exact history log format; silently returns wrong filenames if the format ever changes.

- **Connection management is explicitly addressed** — `sqlite_tag_index.py` includes a comment acknowledging the connection leak that arose when code was adapted from short-lived CLI use to the long-running watcher, and explains why `conn.close()` was added in a `finally` block. Honest, self-aware commentary is good hygiene.

- **`install-watcher.sh`** suggests the watcher is designed to be run as a launchd background service on macOS, showing awareness of real deployment needs beyond a pure developer tool.

---

## Summary Scorecard

| Principle / Pattern | Score | Notes |
|---|---|---|
| **Single Responsibility** | ★★★★☆ | Excellent per-module; `Dependencies` and `note_content.py` are deliberate/pragmatic exceptions |
| **Open/Closed** | ★★★★☆ | `NoteFormatRegistry` is textbook OCP; `isinstance` + direct `tag_index` access in watcher are misses |
| **Liskov Substitution** | ★★★☆☆ | Only one concrete `NoteStore` — not actively tested across substitutions |
| **Interface Segregation** | ★★★☆☆ | `NoteStore`, `TagIndex`, and `Dependencies` wider than ideal; `NoteFormat` and `Editor` are minimal ✅ |
| **Dependency Inversion** | ★★★★☆ | Strong end-to-end injection; specific cracks in watcher layer and `typer.confirm` coupling |
| **Refactoring Quality** | ★★★★☆ | Multiple deliberate, well-scoped refactors visible in git history |
| **Feature Isolation** | ★★★★☆ | New features mostly added in new files; minimal churn to existing code |
| **Domain Modeling** | ★★★★★ | `NoteDocument`/`NoteLifecycle`/`NoteFormatRegistry` are excellent |
| **Test Alignment** | ★★★★☆ | DI makes tests straightforward; wide interfaces add setup friction |

### Key Strengths
- **DIP** is fully realized across the core — the codebase is genuinely testable at every layer
- **`NoteLifecycle` state machine** prevents invalid note states at the type level
- **`NoteFormatRegistry`** is a textbook extensibility mechanism
- Refactoring commits are well-scoped and clearly motivated
- The watcher's durable SQLite queue + revision-based optimistic concurrency is a solid engineering choice

### Areas to Watch
- `Dependencies` as a god-object is pragmatic but will grow without discipline
- The `isinstance(note_store, FileSystemNoteStore)` + `note_store.tag_index` access in the watcher are abstraction cracks that compound each other
- `NoteStore` ABC carries a dead `search()` method and may benefit from being split into narrower capability interfaces as the feature set grows
- The O(n) `_refresh_tag_index()` on every read is a latent performance problem for larger note sets
- With only one concrete `NoteStore`, the abstraction's substitutability is largely theoretical today

---

*Generated from git history analysis of the `jour` CLI project — Oct 2026*
