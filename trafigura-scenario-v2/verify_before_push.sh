#!/bin/bash
# Pre-push verification for the V2 POC. Run this before every push.
#
# Catches the exact class of mistake that happened during development:
# leftover file mutations from manual testing silently corrupting the
# "clean baseline" (e.g. scenario files stuck with an already-applied fix,
# or a stray `git checkout` reverting an in-progress change without anyone
# noticing until the next demo run).
#
# Checks, in order:
#   1. No uncommitted changes under agent/workspace/src/scenarios/ (if
#      there are, either commit them deliberately or `git checkout --` them
#      before proceeding - this script refuses to guess which you meant).
#   2. Backend compiles.
#   3. Backend starts and responds to /api/health.
#   4. Backend is reset to its healthy default state (fee off, discount on,
#      cutoff early) via /api/admin/reset-all - so this check is
#      deterministic regardless of what a previous manual session left running.
#   5. Workspace compiles.
#   6. Clean baseline genuinely reports "54 passed, 0 failed" - not just
#      "compiles", but *the numbers a demo would actually show*.
#   7. Backend process is cleanly killed and ports are freed.
#
# Exit code 0 = safe to push. Any non-zero = do NOT push; read the message.

set -u
V2_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$V2_ROOT/backend"
WORKSPACE_DIR="$V2_ROOT/agent/workspace"
FAIL=0

echo "=== 1. Checking for uncommitted scenario file changes ==="
cd "$V2_ROOT/.."
DIRTY=$(git status --short -- trafigura-scenario-v2/agent/workspace/src/scenarios/ 2>/dev/null)
if [ -n "$DIRTY" ]; then
    echo "FAIL: uncommitted changes under scenarios/ - commit or discard them first:"
    echo "$DIRTY"
    FAIL=1
else
    echo "OK: no uncommitted scenario changes"
fi

echo ""
echo "=== 2. Compiling backend ==="
cd "$BACKEND_DIR"
find src -name "*.java" > sources.txt
if ! javac -d out @sources.txt 2>&1; then
    echo "FAIL: backend did not compile"
    FAIL=1
else
    echo "OK: backend compiled"
fi

if [ "$FAIL" -eq 1 ]; then
    echo ""
    echo "=== ABORTED: fix the above before continuing ==="
    exit 1
fi

echo ""
echo "=== 3. Starting backend ==="
lsof -ti:5100 2>/dev/null | xargs kill -9 2>/dev/null
nohup java -cp out api.TradeApiServer 5100 > /tmp/verify_backend.log 2>&1 &
BPID=$!
sleep 2
if ! curl -s --max-time 3 http://127.0.0.1:5100/api/health | grep -q '"status":"ok"'; then
    echo "FAIL: backend did not respond to /api/health"
    cat /tmp/verify_backend.log
    kill "$BPID" 2>/dev/null
    exit 1
fi
echo "OK: backend responding"

echo ""
echo "=== 4. Resetting backend to healthy defaults ==="
curl -s -X POST http://127.0.0.1:5100/api/admin/reset-all -d '{}' > /dev/null
echo "OK: reset-all called"

echo ""
echo "=== 5. Compiling workspace ==="
cd "$WORKSPACE_DIR"
find src -name "*.java" > sources.txt
if ! javac -d out @sources.txt TestRunner.java 2>&1; then
    echo "FAIL: workspace did not compile"
    kill "$BPID" 2>/dev/null
    exit 1
fi
echo "OK: workspace compiled"

echo ""
echo "=== 6. Running clean baseline check ==="
OUTPUT=$(timeout 30 java -cp out:. TestRunner 2>&1)
echo "$OUTPUT" | tail -8
if echo "$OUTPUT" | grep -q "54 passed, 0 failed"; then
    echo "OK: clean baseline is genuinely 54 passed, 0 failed"
else
    echo "FAIL: clean baseline is NOT 54/0 - something is dirty. Do not push."
    FAIL=1
fi

echo ""
echo "=== 7. Cleaning up ==="
kill "$BPID" 2>/dev/null
rm -rf out sources.txt "$BACKEND_DIR/out" "$BACKEND_DIR/sources.txt"
echo "OK: backend stopped, build artifacts removed"

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "=== SAFE TO PUSH ==="
    exit 0
else
    echo "=== DO NOT PUSH - see failures above ==="
    exit 1
fi
