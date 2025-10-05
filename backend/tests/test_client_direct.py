"""
Test the essential_data_client directly with full error tracing
"""
import asyncio
import logging
import traceback

# Enable all logging
logging.basicConfig(level=logging.DEBUG)

async def test():
    print("Importing essential_data_client...")
    from backend.clients.essential_data_client import EssentialDataClient

    print("Creating client...")
    client = EssentialDataClient()

    print("Calling _search_wikipedia...")
    try:
        results = await client._search_wikipedia("geometric abstraction", "art")
        print(f"✅ Got {len(results)} results")
        if results:
            print(f"First result keys: {list(results[0].keys())}")
            print(f"Summary: {results[0].get('summary', 'NO SUMMARY')[:100]}")
        else:
            print("❌ No results returned - checking why...")
            # Try getting summary directly
            summary = await client._get_wikipedia_summary("Geometric abstraction")
            print(f"Direct summary call: {summary[:100] if summary else 'None'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
