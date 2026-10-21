#!/usr/bin/env sh
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
    echo "The watcher installer currently supports macOS LaunchAgents only." >&2
    exit 1
fi

if ! command -v jour >/dev/null 2>&1; then
    echo "Could not find 'jour' on PATH. Install Jour first, then retry." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to create the LaunchAgent property list." >&2
    exit 1
fi

JOUR_BIN=$(command -v jour)
JOUR_BIN=$(python3 -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$JOUR_BIN")
AGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$AGENT_DIR/com.jour.global-watcher.plist"
LOG_DIR="$HOME/.jour"
LABEL="com.jour.global-watcher"
UID_VALUE=$(id -u)

mkdir -p "$AGENT_DIR" "$LOG_DIR"

export JOUR_BIN PLIST_PATH LOG_DIR LABEL
python3 - <<'PY'
import os
import plistlib
import tempfile

plist_path = os.environ["PLIST_PATH"]
agent = {
    "Label": os.environ["LABEL"],
    "ProgramArguments": [os.environ["JOUR_BIN"], "-g", "watch"],
    "RunAtLoad": True,
    "KeepAlive": True,
    "ProcessType": "Background",
    "StandardOutPath": os.path.join(os.environ["LOG_DIR"], "watcher.log"),
    "StandardErrorPath": os.path.join(os.environ["LOG_DIR"], "watcher.log"),
}

with tempfile.NamedTemporaryFile(
    mode="wb", dir=os.path.dirname(plist_path), delete=False
) as plist_file:
    temporary_path = plist_file.name
    plistlib.dump(agent, plist_file, sort_keys=True)

os.chmod(temporary_path, 0o644)
existing_matches = False
if os.path.exists(plist_path):
    with open(plist_path, "rb") as existing_file:
        with open(temporary_path, "rb") as temporary_file:
            existing_matches = existing_file.read() == temporary_file.read()

if existing_matches:
    os.unlink(temporary_path)
else:
    os.replace(temporary_path, plist_path)
PY

DOMAIN="gui/$UID_VALUE"
launchctl bootout "$DOMAIN" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl enable "$DOMAIN/$LABEL"
launchctl bootstrap "$DOMAIN" "$PLIST_PATH"

echo "Installed and started the global Jour watcher."
echo "LaunchAgent: $PLIST_PATH"
echo "Log: $LOG_DIR/watcher.log"
