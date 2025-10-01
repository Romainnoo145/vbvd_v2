"""
WebSocket Progressive Streaming Test Client

Demonstrates how frontend will receive stage-by-stage results:
- Stage 1 (1-2 min): Title & curatorial statement
- Stage 2 (3-4 min): Artists with scores
- Stage 3 (5-8 min): Artworks with IIIF manifests
"""

import asyncio
import json
import sys
from datetime import datetime
import websockets
import httpx

API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"


async def test_progressive_streaming():
    """Test progressive streaming with WebSocket connection"""

    print("\n" + "="*80)
    print("PROGRESSIVE STREAMING TEST - Surrealism Exhibition")
    print("="*80)

    # Step 1: Submit curator brief
    print("\n📤 Step 1: Submitting curator brief...")

    curator_brief = {
        "theme_title": "Surrealism and the Unconscious Mind",
        "theme_description": "Exploring how surrealist artists used automatism, dream imagery, and psychological symbolism to access the unconscious mind.",
        "theme_concepts": ["surrealism", "automatism", "dream imagery", "psychoanalysis", "biomorphism"],
        "reference_artists": ["Salvador Dalí", "René Magritte", "Max Ernst"],
        "target_audience": "general",
        "duration_weeks": 12
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/curator/submit",
            json={
                "curator_brief": curator_brief,
                "config": {
                    "max_artists": 5,  # Reduced for faster test
                    "max_artworks": 15,
                    "min_artist_relevance": 0.6,
                    "min_artwork_relevance": 0.5
                }
            },
            timeout=10.0
        )

        if response.status_code != 200:
            print(f"❌ Failed to submit brief: {response.text}")
            return

        result = response.json()
        session_id = result["session_id"]
        ws_url = f"{WS_BASE}{result['websocket_url']}"

        print(f"✅ Brief submitted!")
        print(f"   Session ID: {session_id}")
        print(f"   WebSocket URL: {ws_url}")

    # Step 2: Connect to WebSocket and receive progressive updates
    print(f"\n🔌 Step 2: Connecting to WebSocket...")

    stage_data = {
        "theme": None,
        "artists": None,
        "artworks": None
    }

    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ WebSocket connected!")

            # Listen for messages
            print(f"\n👂 Step 3: Listening for stage completions...")
            print(f"{'─'*80}\n")

            while True:
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=600.0)
                    message = json.loads(message_str)

                    if message["type"] == "connected":
                        print(f"🟢 Connected: {message['message']}")

                    elif message["type"] == "progress":
                        # Regular progress update
                        print(f"⏳ [{message['progress']:.0f}%] {message['stage']}: {message['message']}")

                    elif message["type"] == "stage_complete":
                        # Stage completion with data!
                        completed_stage = message["completed_stage"]
                        progress = message["progress"]

                        print(f"\n{'═'*80}")
                        print(f"✨ STAGE COMPLETE: {completed_stage.upper()} ({progress:.0f}%)")
                        print(f"{'═'*80}")

                        if completed_stage == "theme_refinement":
                            data = message["data"]
                            stage_data["theme"] = data

                            print(f"\n📋 EXHIBITION THEME:")
                            print(f"   Title: {data['exhibition_title']}")
                            if data['subtitle']:
                                print(f"   Subtitle: {data['subtitle']}")
                            print(f"   Audience: {data['target_audience_refined']}")
                            print(f"   Complexity: {data['complexity_level']}")

                            print(f"\n📄 Curatorial Statement ({len(data['curatorial_statement'])} chars):")
                            print(f"   {data['curatorial_statement'][:200]}...")

                            print(f"\n🎓 Scholarly Rationale ({len(data['scholarly_rationale'])} chars):")
                            print(f"   {data['scholarly_rationale'][:200]}...")

                        elif completed_stage == "artist_discovery":
                            data = message["data"]
                            stage_data["artists"] = data
                            artists = data["artists"]

                            print(f"\n👨‍🎨 DISCOVERED ARTISTS ({len(artists)}):")
                            for i, artist in enumerate(artists, 1):
                                print(f"\n   {i}. {artist['name']}")
                                print(f"      Score: {artist['relevance_score']:.2f}")
                                print(f"      Life: {artist.get('birth_year', '?')} - {artist.get('death_year', 'present')}")
                                print(f"      Wikidata: {artist['wikidata_id']}")
                                print(f"      Reasoning: {artist['relevance_reasoning'][:100]}...")

                        elif completed_stage == "artwork_discovery":
                            data = message["data"]
                            stage_data["artworks"] = data
                            artworks = data["artworks"]

                            print(f"\n🎨 DISCOVERED ARTWORKS ({len(artworks)}):")

                            # Count IIIF availability
                            with_iiif = sum(1 for a in artworks if a.get('iiif_manifest'))
                            print(f"   IIIF Manifests: {with_iiif}/{len(artworks)} ({with_iiif/len(artworks)*100:.0f}%)")

                            # Show top 5
                            for i, artwork in enumerate(artworks[:5], 1):
                                print(f"\n   {i}. {artwork['title']}")
                                print(f"      Artist: {artwork['artist_name']}")
                                print(f"      Date: {artwork.get('date_created', 'Unknown')}")
                                print(f"      Medium: {artwork.get('medium', 'Unknown')}")
                                print(f"      Institution: {artwork.get('institution_name', 'Unknown')}")
                                print(f"      Score: {artwork['relevance_score']:.2f}")
                                print(f"      IIIF: {'✅' if artwork.get('iiif_manifest') else '❌'}")
                                if artwork.get('height_cm') and artwork.get('width_cm'):
                                    print(f"      Size: {artwork['height_cm']}cm × {artwork['width_cm']}cm")

                        print(f"\n{'─'*80}\n")

                    elif message["type"] == "completed":
                        print(f"\n🎉 PIPELINE COMPLETE!")
                        print(f"   Proposal URL: {API_BASE}{message['proposal_url']}")

                        # Final summary
                        print(f"\n{'='*80}")
                        print("FINAL SUMMARY")
                        print(f"{'='*80}")

                        if stage_data["theme"]:
                            print(f"✅ Theme: {stage_data['theme']['exhibition_title']}")
                        if stage_data["artists"]:
                            print(f"✅ Artists: {len(stage_data['artists']['artists'])} discovered")
                        if stage_data["artworks"]:
                            artworks = stage_data['artworks']['artworks']
                            with_iiif = sum(1 for a in artworks if a.get('iiif_manifest'))
                            print(f"✅ Artworks: {len(artworks)} discovered ({with_iiif} with IIIF)")

                        break

                    elif message["type"] == "error":
                        print(f"\n❌ ERROR: {message['error']}")
                        break

                except asyncio.TimeoutError:
                    print("\n⏰ Timeout waiting for message (10 minutes)")
                    break
                except Exception as e:
                    print(f"\n❌ Error receiving message: {e}")
                    break

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    print("\n⚠️  PREREQUISITE: API server must be running!")
    print("   Start with: cd backend/api && uvicorn main:app --reload\n")

    try:
        asyncio.run(test_progressive_streaming())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
