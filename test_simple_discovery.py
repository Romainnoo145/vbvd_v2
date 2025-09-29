"""
SIMPLIFIED TEST - Direct Wikidata query for Impressionists with diversity data
"""
import asyncio
import httpx


async def test_simple_impressionist_discovery():
    """Test with known working query - Impressionism"""

    print("=" * 80)
    print("SIMPLE TEST: Get Impressionist Artists with Gender Data")
    print("=" * 80)

    # Very simple query - just get Impressionists
    query = """
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>

    SELECT DISTINCT ?artist ?artistLabel ?genderLabel ?nationalityLabel ?birth ?death WHERE {
      ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter
      ?artist wdt:P135 wd:Q40415 .    # Movement: Impressionism

      OPTIONAL { ?artist wdt:P21 ?gender }
      OPTIONAL { ?artist wdt:P27 ?nationality }
      OPTIONAL { ?artist wdt:P569 ?birth }
      OPTIONAL { ?artist wdt:P570 ?death }

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }
    LIMIT 20
    """

    print("\n🔍 Executing SPARQL query...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://query.wikidata.org/sparql",
            data={'query': query, 'format': 'json'},
            headers={
                'Accept': 'application/sparql-results+json',
                'User-Agent': 'AICuratorTest/1.0'
            }
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {}).get('bindings', [])

            print(f"\n✅ SUCCESS! Found {len(results)} Impressionist artists\n")

            # Analyze diversity
            female_count = 0
            male_count = 0
            unknown_gender = 0

            nationalities = {}

            for r in results:
                name = r.get('artistLabel', {}).get('value', 'Unknown')
                gender = r.get('genderLabel', {}).get('value', 'unknown')
                nationality = r.get('nationalityLabel', {}).get('value', 'Unknown')
                birth = r.get('birth', {}).get('value', '')[:4] or '?'
                death = r.get('death', {}).get('value', '')[:4] or '?'

                # Count gender
                if 'female' in gender.lower():
                    female_count += 1
                    gender_icon = "👩"
                elif 'male' in gender.lower():
                    male_count += 1
                    gender_icon = "👨"
                else:
                    unknown_gender += 1
                    gender_icon = "❓"

                # Count nationalities
                nationalities[nationality] = nationalities.get(nationality, 0) + 1

                print(f"{gender_icon} {name} ({birth}-{death})")
                print(f"   Gender: {gender}, Nationality: {nationality}\n")

            # Summary
            print("=" * 80)
            print("DIVERSITY SUMMARY")
            print("=" * 80)

            total = len(results)
            print(f"\n👥 Gender Distribution:")
            print(f"   Female: {female_count} ({female_count/total*100:.1f}%)")
            print(f"   Male: {male_count} ({male_count/total*100:.1f}%)")
            print(f"   Unknown: {unknown_gender} ({unknown_gender/total*100:.1f}%)")

            print(f"\n🌍 Geographic Distribution:")
            for nat, count in sorted(nationalities.items(), key=lambda x: -x[1])[:5]:
                print(f"   {nat}: {count} artist{'s' if count > 1 else ''}")

            print("\n" + "=" * 80)
            print("✅ PROOF: We CAN get real gender + nationality data from Wikidata!")
            print("=" * 80)

            return results

        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None


if __name__ == "__main__":
    print("\n🎨 Testing Simple Artist Discovery with Real Wikidata\n")
    results = asyncio.run(test_simple_impressionist_discovery())

    if results:
        print(f"\n✨ Successfully retrieved {len(results)} artists with diversity data!")
    else:
        print("\n⚠️  Test failed")