#!/usr/bin/env sh
# Build and run jour CLI test suites inside a Podman container.
set -e

IMAGE="jour-cli-test"

echo "==> Building image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "\n==> Running smoke tests"
podman run --rm "$IMAGE" sh tests/smoke.sh

echo "\n==> Running tag tests"
podman run --rm "$IMAGE" sh tests/test_tags.sh
