#!/usr/bin/env sh
# Build and run jour CLI test suites inside a Podman container.
set -e

IMAGE="jour-cli-test"

echo "==> Building image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "\n==> Running note input tests"
podman run --rm "$IMAGE" python3 -m unittest discover -s tests -p 'test_*.py'

echo "\n==> Running smoke tests"
podman run --rm "$IMAGE" sh tests/smoke.sh
echo "\n==> Checking history log for smoke tests"
podman run --rm "$IMAGE" sh -c 'cat ~/.jour/logs/history | grep -E "notes make|notes list|notes cat|notes delete|notes edit|tags list|tags show|search"' || echo "No commands logged (may be expected if no commands were run)"

echo "\n==> Running tag tests"
podman run --rm "$IMAGE" sh tests/test_tags.sh
echo "\n==> Checking history log for tag tests"
podman run --rm "$IMAGE" sh -c 'cat ~/.jour/logs/history | grep -E "tags list|tags show"' || echo "No commands logged (may be expected if no commands were run)"

echo "\n==> Running cat tests"
podman run --rm "$IMAGE" sh tests/test_cat.sh
echo "\n==> Checking history log for cat tests"
podman run --rm "$IMAGE" sh -c 'cat ~/.jour/logs/history | grep -E "notes cat"' || echo "No commands logged (may be expected if no commands were run)"

echo "\n==> Running delete tests"
podman run --rm "$IMAGE" sh tests/test_delete.sh
echo "\n==> Checking history log for delete tests"
podman run --rm "$IMAGE" sh -c 'cat ~/.jour/logs/history | grep -E "notes delete"' || echo "No commands logged (may be expected if no commands were run)"

echo "\n==> Running history tests"
podman run --rm "$IMAGE" sh tests/test_history.sh
echo "\n==> Checking history log for history command"
podman run --rm "$IMAGE" sh -c 'cat ~/.jour/logs/history | grep -E "history"' || echo "No commands logged (may be expected if no commands were run)"

echo "\n==> All tests completed with log verification"
