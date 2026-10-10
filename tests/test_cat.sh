#!/usr/bin/env sh
# Tests for jour notes cat — runs inside the container.

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

echo "\n[1] notes cat outputs the correct note body"
jour notes make --note "cat test body 1" -t "cattest"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
LATEST_HASH=$(basename "$LATEST" .jmd)

OUTPUT=$(jour notes cat "$LATEST_HASH")
if echo "$OUTPUT" | grep -q "cat test body 1"; then
    pass "notes cat printed the body"
else
    fail "notes cat did not print the body"
fi

if echo "$OUTPUT" | grep -q "cattest"; then
    pass "notes cat printed the front matter"
else
    fail "notes cat did not print the front matter"
fi

echo "\n[2] notes cat outputs error for non-existent note"
if OUTPUT=$(jour notes cat "invalid_hash_12345" 2>&1); then
    fail "notes cat succeeded unexpectedly"
else
    pass "notes cat failed with non-zero exit code"
fi

if echo "$OUTPUT" | grep -q "Error: Note invalid_hash_12345 not found"; then
    pass "notes cat printed the expected error"
else
    fail "notes cat printed unexpected error: $OUTPUT"
fi

echo "\n================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"
[ "$FAIL" -eq 0 ]
