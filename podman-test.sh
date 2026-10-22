#!/usr/bin/env sh
# Build and run jour CLI test suites inside a Podman container.
set -e

IMAGE="jour-cli-test"

echo "==> Building image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "\n==> Running unit tests"
podman run --rm "$IMAGE" python3 -m unittest discover -s tests -p 'test_*.py'

echo "\n==> Running container smoke tests"
podman run --rm "$IMAGE" sh tests/smoke.sh

echo "\n==> All tests completed successfully"
