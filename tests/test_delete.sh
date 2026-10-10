#!/usr/bin/env sh
# Tests for jour notes delete — runs inside the container.

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

echo "\n[1] notes delete removes note and tags"
jour notes make --note "delete test body 1" -t "deletetag"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
LATEST_HASH=$(basename "$LATEST" .jmd)

jour notes delete "$LATEST_HASH"
if [ ! -f "$LATEST" ]; then
    pass "file was deleted"
else
    fail "file still exists"
fi

# Try catting it, should fail
if OUTPUT=$(jour notes cat "$LATEST_HASH" 2>&1); then
    fail "notes cat succeeded but shouldn't have"
else
    pass "notes cat failed as expected"
fi

# Check that the tag is gone
TAG_OUTPUT=$(jour tags show deletetag 2>&1)
if [ -z "$TAG_OUTPUT" ]; then
    pass "tag was deleted from db"
else
    fail "tag might still exist: $TAG_OUTPUT"
fi

echo "\n[2] notes delete outputs error for non-existent note"
if OUTPUT=$(jour notes delete "invalid_hash_12345" 2>&1); then
    fail "notes delete succeeded unexpectedly"
else
    pass "notes delete failed with non-zero exit code"
fi

if echo "$OUTPUT" | grep -q "Error: Note invalid_hash_12345 not found"; then
    pass "notes delete printed the expected error"
else
    fail "notes delete printed unexpected error: $OUTPUT"
fi

echo "\n================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"
[ "$FAIL" -eq 0 ]
