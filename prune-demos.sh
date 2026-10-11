#!/bin/sh
set -eu

containers=$(podman ps -aq --filter 'name=^jour-demo-')

if [ -z "$containers" ]; then
    echo "No demo.sh containers to remove."
    exit 0
fi

printf '%s\n' "$containers" |
while IFS= read -r container; do
    [ -z "$container" ] || podman rm -f "$container"
done