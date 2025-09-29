"""
Test API Connectivity - Check if we can get REAL data
"""
import asyncio
import httpx
import json

async def test_wikidata_simple():
    """Test Wikidata with a very simple, fast query"""
    print("\n" + "="*80)
    print("TEST 1: Wikidata SPARQL - Simple Artist Query")
    print("="*80)

    # Much simpler query - just get 5 Dutch Golden Age painters directly
    query = """
    SELECT ?artist ?artistLabel ?birth ?death WHERE {
      VALUES ?artist { wd:Q41264 wd:Q5598 wd:Q41159 }  # Vermeer, Rembrandt, Jan Steen
      OPTIONAL { ?artist wdt:P569 ?birth }
      OPTIONAL { ?artist wdt:P570 ?death }

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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

                print(f"✅ SUCCESS! Got {len(results)} artists")
                for r in results:
                    name = r.get('artistLabel', {}).get('value', 'Unknown')
                    birth = r.get('birth', {}).get('value', 'Unknown')[:4]
                    death = r.get('death', {}).get('value', 'Unknown')[:4]
                    print(f"   • {name} ({birth}-{death})")
                return True
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_wikipedia():
    """Test Wikipedia API"""
    print("\n" + "="*80)
    print("TEST 2: Wikipedia API - Get Vermeer Summary")
    print("="*80)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/Johannes_Vermeer",
                headers={'User-Agent': 'AICuratorTest/1.0'}
            )

            if response.status_code == 200:
                data = response.json()
                title = data.get('title', 'Unknown')
                extract = data.get('extract', 'No summary')[:200]

                print(f"✅ SUCCESS! Got article for {title}")
                print(f"   Summary: {extract}...")
                return True
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_wikidata_with_gender_filter():
    """Test Wikidata with gender filtering - for diversity"""
    print("\n" + "="*80)
    print("TEST 3: Wikidata with Gender/Ethnicity Filtering")
    print("="*80)

    query = """
    SELECT ?artist ?artistLabel ?genderLabel ?birth ?death ?nationalityLabel WHERE {
      VALUES ?artist {
        wd:Q41264    # Vermeer (male)
        wd:Q235454   # Rachel Ruysch (female)
        wd:Q5598     # Rembrandt (male)
      }

      OPTIONAL { ?artist wdt:P21 ?gender }
      OPTIONAL { ?artist wdt:P569 ?birth }
      OPTIONAL { ?artist wdt:P570 ?death }
      OPTIONAL { ?artist wdt:P27 ?nationality }

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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

                print(f"✅ SUCCESS! Got {len(results)} artists with demographics")
                for r in results:
                    name = r.get('artistLabel', {}).get('value', 'Unknown')
                    gender = r.get('genderLabel', {}).get('value', 'Unknown')
                    nat = r.get('nationalityLabel', {}).get('value', 'Unknown')
                    print(f"   • {name} - Gender: {gender}, Nationality: {nat}")
                return True
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_wikidata_concept_search():
    """Test searching for artists by concept (e.g., Impressionism)"""
    print("\n" + "="*80)
    print("TEST 4: Wikidata Concept Search - Find Impressionist Artists")
    print("="*80)

    # Search for artists associated with Impressionism movement
    query = """
    SELECT DISTINCT ?artist ?artistLabel ?genderLabel ?birth ?death WHERE {
      ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter
      ?artist wdt:P135 wd:Q40415 .    # Movement: Impressionism

      OPTIONAL { ?artist wdt:P21 ?gender }
      OPTIONAL { ?artist wdt:P569 ?birth }
      OPTIONAL { ?artist wdt:P570 ?death }

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }
    LIMIT 10
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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

                print(f"✅ SUCCESS! Found {len(results)} Impressionist painters")

                # Count by gender
                male_count = sum(1 for r in results if r.get('genderLabel', {}).get('value') == 'male')
                female_count = sum(1 for r in results if r.get('genderLabel', {}).get('value') == 'female')

                print(f"   Demographics: {male_count} male, {female_count} female")
                print(f"\n   Artists found:")
                for r in results[:5]:
                    name = r.get('artistLabel', {}).get('value', 'Unknown')
                    gender = r.get('genderLabel', {}).get('value', 'Unknown')
                    birth = r.get('birth', {}).get('value', 'Unknown')[:4]
                    print(f"   • {name} ({gender}, b. {birth})")

                return True
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def main():
    print("\n🔍 TESTING API CONNECTIVITY - GETTING REAL DATA")
    print("="*80)
    print("Goal: Verify we can get actual artist data from Wikidata & Wikipedia")
    print("="*80)

    results = []

    # Test 1: Simple Wikidata query
    results.append(("Wikidata Simple", await test_wikidata_simple()))

    # Test 2: Wikipedia
    results.append(("Wikipedia", await test_wikipedia()))

    # Test 3: Wikidata with demographics
    results.append(("Wikidata Demographics", await test_wikidata_with_gender_filter()))

    # Test 4: Concept-based search
    results.append(("Concept Search", await test_wikidata_concept_search()))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for test_name, success in results:
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"{test_name:30} {status}")

    successful = sum(1 for _, success in results if success)
    print(f"\n{successful}/{len(results)} tests passed")

    if successful == len(results):
        print("\n✅ ALL APIS WORKING! Ready for real pipeline test")
        return True
    elif successful > 0:
        print(f"\n⚠️  PARTIAL: {successful} APIs working, pipeline may work with limited data")
        return True
    else:
        print("\n❌ NO APIS WORKING: Check network connection")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)