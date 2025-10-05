"""
Debug Wikipedia API calls
"""
import asyncio
from backend.clients.essential_data_client import EssentialDataClient


async def test_wikipedia():
    """Test direct Wikipedia API call"""
    print("Testing Wikipedia API...")

    client = EssentialDataClient()

    try:
        results = await client._search_wikipedia("geometric abstraction", "art history")
        print(f"✅ Success! Got {len(results)} results")
        if results:
            print(f"\nFirst result:")
            print(f"  Title: {results[0].get('title')}")
            print(f"  Summary: {results[0].get('summary', 'NO SUMMARY')[:100]}...")
            print(f"  Keys: {list(results[0].keys())}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_wikipedia())
