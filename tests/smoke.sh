#!/usr/bin/env sh
# Smoke tests for jour CLI — runs inside the container.

PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# 1. jour is on PATH
# ---------------------------------------------------------------------------
echo "\n[1] jour binary is on PATH"
if command -v jour > /dev/null 2>&1; then
    pass "jour found at $(command -v jour)"
else
    fail "jour not found on PATH"
fi

# ---------------------------------------------------------------------------
# 2. notes make — no flags (non-interactive: should write file without editor)
# ---------------------------------------------------------------------------
echo "\n[2] notes make via piped stdin"
echo "hello from smoke test" | jour notes make
NOTE_COUNT=$(ls ~/.jour/*.jmd 2>/dev/null | wc -l)
if [ "$NOTE_COUNT" -ge 1 ]; then
    pass "note file created ($NOTE_COUNT found)"
else
    fail "no note file found in ~/.jour"
fi

# ---------------------------------------------------------------------------
# 3. notes make --note flag
# ---------------------------------------------------------------------------
echo "\n[3] notes make --note flag"
jour notes make --note "flag note body"
NOTE_COUNT=$(ls ~/.jour/*.jmd 2>/dev/null | wc -l)
if [ "$NOTE_COUNT" -ge 2 ]; then
    pass "--note flag created a second note"
else
    fail "--note flag did not create a note"
fi

# ---------------------------------------------------------------------------
# 4. notes make --note + --tag flag
# ---------------------------------------------------------------------------
echo "\n[4] notes make --note + --tag"
jour notes make --note "tagged note" --tag "test,smoke"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "test" "$LATEST" && grep -q "smoke" "$LATEST"; then
    pass "tags written to front matter"
else
    fail "tags not found in front matter of $LATEST"
fi

# ---------------------------------------------------------------------------
# 5. notes list
# ---------------------------------------------------------------------------
echo "\n[5] notes list"
OUTPUT=$(jour notes list)
if [ -n "$OUTPUT" ]; then
    pass "notes list returned output"
else
    fail "notes list returned nothing"
fi

# ---------------------------------------------------------------------------
# 6. tags list
# ---------------------------------------------------------------------------
echo "\n[6] tags list"
OUTPUT=$(jour tags list)
if echo "$OUTPUT" | grep -q "test"; then
    pass "tags list shows expected tag"
else
    fail "tags list missing expected tag"
fi

# ---------------------------------------------------------------------------
# 7. tags show
# ---------------------------------------------------------------------------
echo "\n[7] tags show smoke"
OUTPUT=$(jour tags show smoke)
if [ -n "$OUTPUT" ]; then
    pass "tags show returned a file"
else
    fail "tags show returned nothing"
fi

# ---------------------------------------------------------------------------
# 8. search
# ---------------------------------------------------------------------------
echo "\n[8] search"
OUTPUT=$(jour search "smoke test")
if [ -n "$OUTPUT" ]; then
    pass "search returned a match"
else
    fail "search returned no match"
fi

# ---------------------------------------------------------------------------
# 9. note body is actually written to the file
# ---------------------------------------------------------------------------
echo "\n[9] note body persisted to file"
jour notes make --note "persisted body check"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "persisted body check" "$LATEST"; then
    pass "note body found in file"
else
    fail "note body missing from file"
fi

# ---------------------------------------------------------------------------
# 10. multiline pipe body is written in full
# ---------------------------------------------------------------------------
echo "\n[10] multiline piped body"
printf "line one\nline two\nline three" | jour notes make
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "line one" "$LATEST" && grep -q "line three" "$LATEST"; then
    pass "multiline pipe body fully written"
else
    fail "multiline pipe body incomplete"
fi

# ---------------------------------------------------------------------------
# 11. -n short flag (alias for --note)
# ---------------------------------------------------------------------------
echo "\n[11] -n short flag"
jour notes make -n "short flag note"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "short flag note" "$LATEST"; then
    pass "-n short flag written correctly"
else
    fail "-n short flag body missing"
fi

# ---------------------------------------------------------------------------
# 12. single tag via -t
# ---------------------------------------------------------------------------
echo "\n[12] single tag via -t"
jour notes make -n "single tag note" -t "journal"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "journal" "$LATEST"; then
    pass "single tag written to front matter"
else
    fail "single tag missing from front matter"
fi

# ---------------------------------------------------------------------------
# 13. multiple comma-delimited tags — all present in front matter
# ---------------------------------------------------------------------------
echo "\n[13] multiple comma-delimited tags"
jour notes make -n "multi tag note" -t "alpha,beta,gamma"
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "alpha" "$LATEST" && grep -q "beta" "$LATEST" && grep -q "gamma" "$LATEST"; then
    pass "all three tags written to front matter"
else
    fail "one or more tags missing from front matter"
fi

# ---------------------------------------------------------------------------
# 14. input redirection (< file) and file argument
# ---------------------------------------------------------------------------
echo "\n[14] input redirection and file argument"
echo "redirected body" > input_redir.txt
jour notes make < input_redir.txt
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "redirected body" "$LATEST"; then
    pass "input redirection works via stdin"
else
    fail "input redirection failed"
fi

echo "file argument body" > input_arg.txt
jour notes make input_arg.txt
LATEST=$(ls -t ~/.jour/*.jmd | head -1)
if grep -q "file argument body" "$LATEST"; then
    pass "file argument works"
else
    fail "file argument failed"
fi

# ---------------------------------------------------------------------------
# 15. output redirection (> file)
# ---------------------------------------------------------------------------
echo "\n[15] output redirection"
jour notes list > output_redir.txt
if grep -q "$(basename "$LATEST")" output_redir.txt; then
    pass "output redirection works"
else
    fail "output redirection failed"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "\n================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"
[ "$FAIL" -eq 0 ]
