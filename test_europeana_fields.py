"""Check what fields Europeana actually returns"""
import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_key = os.getenv('EUROPEANA_API_KEY')
    api_url = "https://api.europeana.eu/record/v2/search.json"
    
    api_params = {
        'wskey': api_key,
        'query': 'art',
        'qf': ['TYPE:IMAGE'],
        'rows': 1,
        'profile': 'rich'
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=api_params)
        data = response.json()
    
    if data.get('items'):
        item = data['items'][0]
        print("Available fields in Europeana item:")
        print(json.dumps(list(item.keys()), indent=2))
        print("\nSample item:")
        print(json.dumps(item, indent=2)[:2000])

asyncio.run(main())
