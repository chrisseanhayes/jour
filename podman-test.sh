#!/usr/bin/env sh
# Build and run the jour CLI smoke tests inside a Podman container.
set -e

IMAGE="jour-cli-test"

echo "==> Building image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "\n==> Running smoke tests"
podman run --rm "$IMAGE"
