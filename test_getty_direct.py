"""Direct Getty API test"""
import asyncio
import httpx

async def test_getty():
    query = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX gvp: <http://vocab.getty.edu/ontology#>

SELECT ?subject ?label WHERE {
    ?subject skos:prefLabel ?label .
    ?subject gvp:broaderExtended <http://vocab.getty.edu/aat/> .
    FILTER(CONTAINS(LCASE(STR(?label)), "impressionism"))
}
LIMIT 5
    """

    url = "http://vocab.getty.edu/sparql.json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            data={'query': query, 'format': 'json'},
            headers={
                'Accept': 'application/sparql-results+json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Text length: {len(response.text)}")
        print(f"First 500 chars: {response.text[:500]}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nSuccess! Found {len(data.get('results', {}).get('bindings', []))} results")
                for binding in data.get('results', {}).get('bindings', []):
                    print(f"  - {binding.get('label', {}).get('value', 'N/A')}")
            except Exception as e:
                print(f"JSON parse error: {e}")

if __name__ == "__main__":
    asyncio.run(test_getty())