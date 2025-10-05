"""
Test WebSocket connection for theme-only generation
"""
import asyncio
import json
import websockets

async def test_websocket(session_id: str):
    uri = f"ws://localhost:8001/ws/{session_id}"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Receive messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    data = json.loads(message)

                    print(f"\n📨 Message type: {data.get('type')}")

                    if data.get('type') == 'progress':
                        print(f"   Progress: {data.get('progress')}%")
                        print(f"   Message: {data.get('message')}")

                    elif data.get('type') == 'stage_complete':
                        print(f"   ✅ Stage completed: {data.get('completed_stage')}")
                        if 'data' in data:
                            print(f"   Data keys: {list(data['data'].keys())}")

                    elif data.get('type') == 'theme_complete':
                        print(f"   ✅ THEME COMPLETE!")
                        theme = data.get('theme')
                        if theme:
                            print(f"\n🎨 Exhibition Title: {theme.get('exhibition_title')}")
                            print(f"   Iteration: {theme.get('iteration_count')}")
                            print(f"   Central Argument: {theme.get('central_argument', '')[:100]}...")
                            print(f"   Sections: {len(theme.get('exhibition_sections', []))}")
                            print(f"   Key Questions: {len(theme.get('key_questions', []))}")
                        break

                    elif data.get('type') == 'error':
                        print(f"   ❌ Error: {data.get('error')}")
                        break

                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for message (60s)")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed")
                    break

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_websocket_theme.py <session_id>")
        sys.exit(1)

    session_id = sys.argv[1]
    asyncio.run(test_websocket(session_id))
