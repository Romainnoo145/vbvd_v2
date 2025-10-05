"""
Test movements-only query result counts
"""

import asyncio
import httpx


async def test_movements_only():
    """Test actual result counts with movements-only queries"""

    print("\n" + "="*80)
    print("MOVEMENTS-ONLY QUERY TEST")
    print("="*80 + "\n")

    queries = {
        "Surrealism + Contemporary (2 movements)": '(Surrealism OR "Contemporary Art") AND TYPE:IMAGE',
        "Surrealism only (1 movement)": 'Surrealism AND TYPE:IMAGE',
        "Contemporary only (1 movement)": '"Contemporary Art" AND TYPE:IMAGE',
    }

    api_key = "erockleyell"
    countries = ["netherlands", "belgium", "france", "germany"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for label, query in queries.items():
            print(f"\n{label}:")
            print(f"Query: {query}\n")

            for country in countries:
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

                        status = ""
                        if total_count > 10000:
                            status = "⚠️  TOO MANY"
                        elif total_count > 500:
                            status = "✓ GOOD"
                        elif total_count > 50:
                            status = "✓ OK"
                        else:
                            status = "⚠️  FEW"

                        print(f"  {country:12} {total_count:>8,} results {status}")

                except Exception as e:
                    print(f"  {country}: ERROR - {e}")

            print()

    print("="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("If results are too many (>10k), we may need to:")
    print("1. Add one more constraint (e.g., time period)")
    print("2. Accept it but fetch only 200 items (what we do now)")
    print("3. Use more specific movements")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_movements_only())
