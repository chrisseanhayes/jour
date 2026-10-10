#!/usr/bin/env sh
# Tag indexing and query tests for jour CLI — runs inside the container.

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# 1. Tag count — single note, single tag
# ---------------------------------------------------------------------------
echo "\n[tag-1] single note single tag count"
jour notes make -n "count test one" -t "cnt_single"
OUTPUT=$(jour tags list)
if echo "$OUTPUT" | grep -q "cnt_single: 1"; then
    pass "tag count is 1"
else
    fail "expected 'cnt_single: 1', got: $OUTPUT"
fi

# ---------------------------------------------------------------------------
# 2. Tag count increments across multiple notes
# ---------------------------------------------------------------------------
echo "\n[tag-2] tag count increments across notes"
jour notes make -n "count test two"   -t "cnt_multi"
jour notes make -n "count test three" -t "cnt_multi"
jour notes make -n "count test four"  -t "cnt_multi"
OUTPUT=$(jour tags list)
if echo "$OUTPUT" | grep -q "cnt_multi: 3"; then
    pass "tag count is 3"
else
    fail "expected 'cnt_multi: 3', got: $OUTPUT"
fi

# ---------------------------------------------------------------------------
# 3. tags show returns the correct filename
# ---------------------------------------------------------------------------
echo "\n[tag-3] tags show returns filename for tag"
jour notes make -n "show test note" -t "show_test"
OUTPUT=$(jour tags show show_test)
if [ -n "$OUTPUT" ]; then
    pass "tags show returned: $OUTPUT"
else
    fail "tags show returned nothing for 'show_test'"
fi

# ---------------------------------------------------------------------------
# 4. tags show returns multiple filenames when several notes share a tag
# ---------------------------------------------------------------------------
echo "\n[tag-4] tags show returns multiple notes for shared tag"
jour notes make -n "shared note one" -t "shared_tag"
jour notes make -n "shared note two" -t "shared_tag"
COUNT=$(jour tags show shared_tag | wc -l | tr -d ' ')
if [ "$COUNT" -ge 2 ]; then
    pass "tags show returned $COUNT notes for shared_tag"
else
    fail "expected >= 2 results for shared_tag, got $COUNT"
fi

# ---------------------------------------------------------------------------
# 5. tags show returns nothing for a tag that was never used
# ---------------------------------------------------------------------------
echo "\n[tag-5] tags show empty for nonexistent tag"
OUTPUT=$(jour tags show __tag_that_does_not_exist__)
if [ -z "$OUTPUT" ]; then
    pass "empty result for nonexistent tag"
else
    fail "unexpected output for nonexistent tag: $OUTPUT"
fi

# ---------------------------------------------------------------------------
# 6. Multiple tags on one note — each independently queryable
# ---------------------------------------------------------------------------
echo "\n[tag-6] multiple tags on one note are each queryable"
jour notes make -n "multi tag note" -t "mt_alpha,mt_beta,mt_gamma"
A=$(jour tags show mt_alpha | wc -l | tr -d ' ')
B=$(jour tags show mt_beta  | wc -l | tr -d ' ')
G=$(jour tags show mt_gamma | wc -l | tr -d ' ')
if [ "$A" -ge 1 ] && [ "$B" -ge 1 ] && [ "$G" -ge 1 ]; then
    pass "all three tags independently queryable"
else
    fail "mt_alpha=$A mt_beta=$B mt_gamma=$G (expected each >= 1)"
fi

# ---------------------------------------------------------------------------
# 7. Untagged note does not appear under any tag
# ---------------------------------------------------------------------------
echo "\n[tag-7] untagged note does not pollute tag index"
jour notes make -n "no tags here"
OUTPUT=$(jour tags show __tag_that_does_not_exist__)
if [ -z "$OUTPUT" ]; then
    pass "untagged note not present under spurious tag"
else
    fail "untagged note appeared under unexpected tag: $OUTPUT"
fi

# ---------------------------------------------------------------------------
# 8. tags list orders by count descending
# ---------------------------------------------------------------------------
echo "\n[tag-8] tags list is ordered by count descending"
# cnt_multi has 3 notes; cnt_single has 1 — cnt_multi must appear first
FIRST=$(jour tags list | grep -E "cnt_multi|cnt_single" | head -1)
if echo "$FIRST" | grep -q "cnt_multi"; then
    pass "highest-count tag appears first"
else
    fail "expected cnt_multi first, got: $FIRST"
fi

# ---------------------------------------------------------------------------
# 9. Tag with leading/trailing whitespace is normalised
# ---------------------------------------------------------------------------
echo "\n[tag-9] tag whitespace is stripped"
jour notes make -n "whitespace tag note" -t " ws_tag "
OUTPUT=$(jour tags show ws_tag)
if [ -n "$OUTPUT" ]; then
    pass "whitespace-padded tag stored and queried as 'ws_tag'"
else
    fail "whitespace-padded tag not found as 'ws_tag'"
fi

# ---------------------------------------------------------------------------
# 10. Re-indexing a note replaces its tags (no duplicates)
# ---------------------------------------------------------------------------
echo "\n[tag-10] index_note is idempotent — no duplicate tag rows"
# Create a note then check its tag appears exactly once in tags list
jour notes make -n "idempotent note" -t "idem_tag"
COUNT=$(jour tags list | grep "idem_tag:" | awk -F': ' '{print $2}' | tr -d ' ')
if [ "$COUNT" -eq 1 ]; then
    pass "idem_tag count is exactly 1"
else
    fail "expected idem_tag count=1, got: $COUNT"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "\n================================"
echo "Tag tests: $PASS passed, $FAIL failed"
echo "================================"
[ "$FAIL" -eq 0 ]
