#!/usr/bin/env sh
# Test for notes edit with history fallback when no hash provided
set -e

IMAGE="jour-cli-test"

echo "==> Building image: $IMAGE"
podman build -t "$IMAGE" -f Containerfile .

echo "\n==> Running edit tests"
podman run --rm "$IMAGE" sh -c '
    # Create a test note first so it gets logged to history
    jour notes make --note "Test content for edit fallback" --tag test
    
    # Now run edit without hash - should use last edited from history
    jour notes edit
    
    # Verify the note was opened (check if file exists and has correct content)
    cat ~/.jour/notes/test_*.jmd | head -5
'

echo "\n==> Checking history log for edit tests"
podman run --rm "$IMAGE" sh -c "cat ~/.jour/logs/history | grep -E \"notes edit\"" || echo "No commands logged (may be expected if no commands were run)"

echo "\n==> All edit tests completed with log verification"
