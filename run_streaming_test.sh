#!/bin/bash

# Progressive Streaming Test Runner
# Starts API server and runs WebSocket test

set -e

echo "========================================"
echo "PROGRESSIVE STREAMING TEST"
echo "========================================"

# Check if API server is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 already in use. Stopping existing server..."
    kill $(lsof -t -i:8000) 2>/dev/null || true
    sleep 2
fi

echo ""
echo "📦 Step 1: Starting FastAPI server..."
cd backend/api

# Start server in background
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/api_server.log 2>&1 &
API_PID=$!

echo "✅ API server started (PID: $API_PID)"
echo "   Logs: /tmp/api_server.log"

# Wait for server to be ready
echo ""
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        echo "Server logs:"
        cat /tmp/api_server.log
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

cd ../..

echo ""
echo "📡 Step 2: Running WebSocket streaming test..."
echo "   This will take 5-8 minutes with optimized config"
echo "   (5 artists, 15 artworks)"
echo ""

# Run the test
python3 tests/test_websocket_streaming.py

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "========================================"
echo "🧹 Cleanup: Stopping API server..."
kill $API_PID 2>/dev/null || true

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ TEST PASSED!"
else
    echo "❌ TEST FAILED (exit code: $TEST_EXIT_CODE)"
    echo ""
    echo "Server logs:"
    tail -50 /tmp/api_server.log
fi

echo "========================================"

exit $TEST_EXIT_CODE
