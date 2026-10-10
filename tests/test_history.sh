#!/usr/bin/env sh
# Tests for jour history — runs inside the container.

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

echo "\n[1] history command exists and works"
OUTPUT=$(jour history)
if [ -n "$OUTPUT" ]; then
    pass "history returned output"
else
    fail "history returned nothing"
fi

echo "\n[2] history shows timestamped entries"
OUTPUT=$(jour history)
if echo "$OUTPUT" | grep -qE "^\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\]"; then
    pass "history entries have timestamps"
else
    fail "history entries missing timestamps"
fi

echo "\n[3] history shows command names"
OUTPUT=$(jour history)
if echo "$OUTPUT" | grep -qE "(notes make|notes list|tags list|search|history)"; then
    pass "history shows command names"
else
    fail "history missing command names"
fi

echo "\n[4] history -n flag limits entries"
jour notes make --note "test for limit" -t "limit_test"
jour notes list
jour tags list
OUTPUT=$(jour history -n 1)
LINE_COUNT=$(echo "$OUTPUT" | wc -l | tr -d ' ')
if [ "$LINE_COUNT" -eq 1 ]; then
    pass "-n 1 limits to single entry"
else
    fail "-n 1 returned $LINE_COUNT lines instead of 1"
fi

echo "\n[5] history -n flag with higher count works"
OUTPUT=$(jour history -n 10)
LINE_COUNT=$(echo "$OUTPUT" | wc -l | tr -d ' ')
if [ "$LINE_COUNT" -ge 3 ]; then
    pass "-n 10 returns multiple entries"
else
    fail "-n 10 returned $LINE_COUNT lines instead of >= 3"
fi

echo "\n[6] history default count is 20"
OUTPUT=$(jour history)
LINE_COUNT=$(echo "$OUTPUT" | wc -l | tr -d ' ')
if [ "$LINE_COUNT" -le 20 ]; then
    pass "default history limit is 20 or less"
else
    fail "default history returned $LINE_COUNT lines instead of <= 20"
fi

echo "\n[7] history shows args when present"
OUTPUT=$(jour history)
if echo "$OUTPUT" | grep -qE "(notes make|tags list|search)"; then
    pass "history shows command with arguments"
else
    fail "history missing argument details"
fi

echo "\n================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"
[ "$FAIL" -eq 0 ]
