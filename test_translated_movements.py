"""
Test if translating movement names helps get more results
"""

import asyncio
import httpx


async def test_translated_movements():
    """Test if movement name translations improve results"""

    print("\n" + "="*80)
    print("MOVEMENT NAME TRANSLATION TEST")
    print("="*80 + "\n")

    test_cases = [
        {
            "label": "English only",
            "query": '(Surrealism OR "Contemporary Art") AND TYPE:IMAGE',
        },
        {
            "label": "English + Dutch",
            "query": '(Surrealism OR Surrealisme OR "Contemporary Art" OR "Hedendaagse Kunst") AND TYPE:IMAGE',
            "country": "netherlands"
        },
        {
            "label": "English + French",
            "query": '(Surrealism OR Surréalisme OR "Contemporary Art" OR "Art Contemporain") AND TYPE:IMAGE',
            "country": "france"
        },
        {
            "label": "English + German",
            "query": '(Surrealism OR Surrealismus OR "Contemporary Art" OR "Zeitgenössische Kunst") AND TYPE:IMAGE',
            "country": "germany"
        }
    ]

    api_key = "erockleyell"

    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_cases:
            label = test["label"]
            query = test["query"]
            country = test.get("country", "netherlands")

            print(f"\n{label} (testing {country}):")
            print(f"Query: {query[:80]}...")

            try:
                response = await client.get(
                    "https://api.europeana.eu/record/v2/search.json",
                    params={
                        "wskey": api_key,
                        "query": query,
                        "rows": 0,
                        "profile": "minimal",
                        "media": "true",
                        "thumbnail": "true",
                        "qf": f"COUNTRY:{country}"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    total_count = data.get('totalResults', 0)

                    print(f"Results: {total_count:,}")

                    if "English only" in label:
                        baseline = total_count
                    else:
                        improvement = total_count - baseline if 'baseline' in locals() else 0
                        if improvement > 0:
                            print(f"  ✅ +{improvement:,} more results with translation!")
                        elif improvement == 0:
                            print(f"  → No change with translation")
                        else:
                            print(f"  ⚠️  Fewer results with translation")

            except Exception as e:
                print(f"ERROR: {e}")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("If translations help, we should add movement name translations!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_translated_movements())
