"""
Test actual Europeana API results with new AND query structure
"""

import asyncio
import httpx


async def test_query_counts():
    """Test actual result counts from Europeana API"""

    print("\n" + "="*80)
    print("EUROPEANA API RESULT COUNT TEST")
    print("="*80 + "\n")

    queries = {
        "OLD (all OR)": "(Surrealism OR photography OR fotografie OR modern OR abstract) AND TYPE:IMAGE",
        "NEW (with AND)": "(Surrealism OR \"Contemporary Art\") AND (photography OR fotografie OR modern OR abstract) AND TYPE:IMAGE",
    }

    api_key = "erockleyell"
    country = "netherlands"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for label, query in queries.items():
            try:
                response = await client.get(
                    "https://api.europeana.eu/record/v2/search.json",
                    params={
                        "wskey": api_key,
                        "query": query,
                        "rows": 0,  # Only get count
                        "profile": "minimal",
                        "media": "true",
                        "thumbnail": "true",
                        "qf": f"COUNTRY:{country}"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    total_count = data.get('totalResults', 0)
                    print(f"{label}:")
                    print(f"  Query: {query}")
                    print(f"  Results: {total_count:,}")

                    if "all OR" in label and total_count > 100000:
                        print(f"  ⚠️  TOO BROAD - {total_count:,} is way too many!")
                    elif "with AND" in label and 100 < total_count < 10000:
                        print(f"  ✅ GOOD - {total_count:,} is a reasonable range")
                    elif total_count < 50:
                        print(f"  ⚠️  TOO NARROW - {total_count} might be too few")
                    print()

            except Exception as e:
                print(f"{label}: ERROR - {e}\n")

    print("="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_query_counts())
