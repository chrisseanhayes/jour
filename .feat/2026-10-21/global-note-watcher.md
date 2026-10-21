# Global Note Watcher

Date: 2026-10-21

## Conversation and decisions

1. **Watch global note files and keep indexes current.** Implemented a
   long-running `jour watch` command. It always selects global storage, watches
   the configured global note directory, and uses the platform's native
   filesystem event backend where available.
2. **Recover after app failure or downtime.** Persist changed file paths in a
   SQLite queue before processing them. Keep failed changes queued, use
   revisions so a newer event cannot be cleared by an older processing pass,
   and reconcile disk files against the index at startup.
3. **Run the watcher as a macOS daemon.** Add an idempotent installer for a
   per-user LaunchAgent that runs `jour -g watch` at login and restarts after
   exit. Its monitor output goes to `~/.jour/watcher.log`.
4. **Debounce batch updates.** Wait for a one-second quiet period after the
   most recent event for a note before processing it. Store the timestamp with
   the durable queue entry so the debounce remains valid across restarts.
5. **Make monitor logging testable.** Inject the logger through `Dependencies`
   and use it for watcher lifecycle, filesystem events, reconciliation,
   indexing, deletion, and failure logs.

## Implementation

- `jour watch` command: `jour_cli/cmd/watch.py`, registered in
  `jour_cli/cmd/cli.py`.
- Filesystem event handling and debounce: `jour_cli/storage/note_watcher.py`.
- Durable queue and SQLite schema migration: `jour_cli/storage/sqlite_tag_index.py`.
- Logger injection: `jour_cli/shared/dependencies.py`.
- LaunchAgent installer: `install-watcher.sh`.
- Usage and architecture documentation: `README.md` and
  `COMMAND_ARCHITECTURE.md`.
- Watcher tests: `tests/test_file_watcher.py`; dependency injection test:
  `tests/test_runtime_injection.py`.

## Operations

Install Jour first, then run `./install-watcher.sh` on macOS. It installs and
starts `~/Library/LaunchAgents/com.jour.global-watcher.plist`. The LaunchAgent
logs to `~/.jour/watcher.log`. The watcher uses the global storage path from
Jour configuration; it does not watch repo-local journals.

## Verification at handoff

The full unittest suite passed: 116 tests. `git diff --check` passed. The
LaunchAgent installer was syntax-checked but not loaded during implementation.
