"""
Essential Data Client
Unified client for accessing all 5 essential data sources with parallel search capabilities
"""
import asyncio
import httpx
import json
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import quote
import os
from datetime import datetime

from backend.config import data_config

# Set up logging
logger = logging.getLogger(__name__)


class EssentialDataClient:
    """Simple client for the 5 essential data sources"""

    def __init__(self, timeout: float = 30.0):
        """Initialize the client with HTTP connection pool"""
        self.timeout = timeout
        self.client = None  # Will be created in __aenter__
        self.config = data_config

    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def search_essential(self,
                              query: str,
                              sources: List[str],
                              context: str = "art") -> Dict[str, List[Dict]]:
        """
        Search essential sources - Wikipedia, Wikidata, Getty, Yale LUX, Brave

        Args:
            query: Search query
            sources: List of sources to search
            context: Additional context for the search

        Returns:
            Dictionary with results from each source
        """
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

        tasks = []
        for source in sources:
            if source == 'wikipedia':
                tasks.append(self._search_wikipedia(query, context))
            elif source == 'wikidata':
                tasks.append(self._search_wikidata(query, context))
            elif source == 'getty':
                tasks.append(self._search_getty(query, context))
            elif source == 'yale_lux':
                tasks.append(self._search_yale_lux(query, context))
            elif source == 'brave_search':
                tasks.append(self._search_brave(query, context))
            else:
                logger.warning(f"Unknown source: {source}")

        # Execute searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize by source
        source_results = {}
        for i, source in enumerate(sources):
            if isinstance(results[i], Exception):
                logger.error(f"Error searching {source}: {results[i]}")
                source_results[source] = []
            elif isinstance(results[i], list):
                source_results[source] = results[i]
            else:
                source_results[source] = []

        return source_results

    async def _search_wikipedia(self, query: str, context: str) -> List[Dict]:
        """
        Search Wikipedia with context-aware queries

        Returns list of articles with summaries
        """
        try:
            # First, search for relevant pages
            search_url = self.config.get_endpoint_url('wikipedia', 'api')
            search_params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f"{query} {context}",
                'srlimit': 5,
                'srprop': 'snippet|size|wordcount'
            }

            headers = self.config.get_headers('wikipedia')
            response = await self.client.get(search_url, params=search_params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('search', [])

                # Get summaries for top results
                results = []
                for page in pages[:3]:  # Limit to top 3 for performance
                    summary = await self._get_wikipedia_summary(page['title'])
                    if summary:
                        results.append({
                            'title': page['title'],
                            'snippet': page.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', ''),
                            'summary': summary,
                            'url': f"https://en.wikipedia.org/wiki/{quote(page['title'].replace(' ', '_'))}",
                            'word_count': page.get('wordcount', 0),
                            'source': 'wikipedia'
                        })

                return results
            else:
                logger.error(f"Wikipedia search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []

    async def _get_wikipedia_summary(self, title: str) -> Optional[str]:
        """Get Wikipedia page summary"""
        try:
            summary_url = self.config.get_endpoint_url('wikipedia', 'summary', title=title)
            headers = self.config.get_headers('wikipedia')
            response = await self.client.get(summary_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return data.get('extract', '')
            return None
        except Exception as e:
            logger.warning(f"Failed to get Wikipedia summary for {title}: {e}")
            return None

    async def _search_wikidata(self, query: str, context: str) -> List[Dict]:
        """
        Search Wikidata for structured art/artist data using SPARQL
        """
        try:
            # Build SPARQL query based on context
            if 'artist' in context.lower():
                sparql_query = self._build_wikidata_artist_query(query)
            elif 'artwork' in context.lower() or 'art' in context.lower():
                sparql_query = self._build_wikidata_artwork_query(query)
            else:
                sparql_query = self._build_wikidata_general_query(query)

            sparql_url = self.config.get_endpoint_url('wikidata', 'sparql')
            headers = self.config.get_headers('wikidata')

            response = await self.client.post(
                sparql_url,
                data={'query': sparql_query, 'format': 'json'},
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                for binding in data.get('results', {}).get('bindings', []):
                    result = {
                        'title': binding.get('itemLabel', {}).get('value', ''),
                        'description': binding.get('description', {}).get('value', ''),
                        'wikidata_id': binding.get('item', {}).get('value', '').split('/')[-1],
                        'source': 'wikidata'
                    }

                    # Add optional fields if present
                    if 'image' in binding:
                        result['image_url'] = binding['image']['value']
                    if 'birth' in binding:
                        result['birth_year'] = binding['birth']['value'][:4] if binding['birth']['value'] else None
                    if 'death' in binding:
                        result['death_year'] = binding['death']['value'][:4] if binding['death']['value'] else None

                    results.append(result)

                return results
            else:
                logger.error(f"Wikidata SPARQL query failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Wikidata search failed: {e}")
            return []

    def _build_wikidata_artwork_query(self, query: str) -> str:
        """Build SPARQL query for artwork search"""
        return f"""
        SELECT DISTINCT ?item ?itemLabel ?description ?image ?creator ?creatorLabel ?date WHERE {{
            ?item rdfs:label ?label .
            ?item wdt:P31/wdt:P279* wd:Q838948 .  # Instance of work of art
            FILTER(CONTAINS(LCASE(?label), "{query.lower()}"))

            OPTIONAL {{ ?item wdt:P18 ?image }}
            OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}
            OPTIONAL {{ ?item wdt:P170 ?creator }}  # Creator
            OPTIONAL {{ ?item wdt:P571 ?date }}     # Inception date

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
            }}
        }}
        LIMIT 10
        """

    def _build_wikidata_artist_query(self, query: str) -> str:
        """Build SPARQL query for artist search"""
        return f"""
        SELECT DISTINCT ?item ?itemLabel ?description ?image ?birth ?death ?movement ?movementLabel WHERE {{
            ?item rdfs:label ?label .
            ?item wdt:P106/wdt:P279* wd:Q483501 .  # Occupation: artist
            FILTER(CONTAINS(LCASE(?label), "{query.lower()}"))

            OPTIONAL {{ ?item wdt:P18 ?image }}
            OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}
            OPTIONAL {{ ?item wdt:P569 ?birth }}    # Date of birth
            OPTIONAL {{ ?item wdt:P570 ?death }}    # Date of death
            OPTIONAL {{ ?item wdt:P135 ?movement }} # Movement

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
            }}
        }}
        LIMIT 10
        """

    def _build_wikidata_general_query(self, query: str) -> str:
        """Build general SPARQL query"""
        return f"""
        SELECT DISTINCT ?item ?itemLabel ?description WHERE {{
            ?item rdfs:label ?label .
            FILTER(CONTAINS(LCASE(?label), "{query.lower()}"))
            FILTER(EXISTS {{
                {{?item wdt:P31/wdt:P279* wd:Q838948}} UNION  # Work of art
                {{?item wdt:P106/wdt:P279* wd:Q483501}} UNION # Artist
                {{?item wdt:P31/wdt:P279* wd:Q210272}}        # Cultural heritage
            }})

            OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}

            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en"
            }}
        }}
        LIMIT 10
        """

    async def _search_getty(self, query: str, context: str) -> List[Dict]:
        """
        Search Getty Vocabularies (AAT, ULAN) using SPARQL
        """
        try:
            results = []

            # Determine which vocabulary to search
            if 'artist' in context.lower() or 'person' in context.lower():
                # Search ULAN for artists
                sparql_query = self._build_getty_ulan_query(query)
                vocab_type = 'ULAN'
            else:
                # Search AAT for concepts
                sparql_query = self._build_getty_aat_query(query)
                vocab_type = 'AAT'

            sparql_url = self.config.get_endpoint_url('getty_vocabularies', 'sparql')
            headers = self.config.get_headers('getty_vocabularies')
            headers['Accept'] = 'application/sparql-results+json'
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

            response = await self.client.post(
                sparql_url,
                data={'query': sparql_query, 'format': 'json'},
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                for binding in data.get('results', {}).get('bindings', []):
                    result = {
                        'uri': binding.get('subject', {}).get('value', ''),
                        'label': binding.get('label', {}).get('value', ''),
                        'vocabulary': vocab_type,
                        'source': 'getty',
                        'type': binding.get('type', {}).get('value', '') if 'type' in binding else vocab_type
                    }

                    # Add scope note if available
                    if 'note' in binding:
                        result['scope_note'] = binding['note']['value']

                    # Extract ID from URI
                    if result['uri']:
                        result['getty_id'] = result['uri'].split('/')[-1]

                    results.append(result)

                return results
            else:
                logger.error(f"Getty search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Getty search failed: {e}")
            return []

    def _build_getty_aat_query(self, query: str) -> str:
        """Build SPARQL query for Getty AAT (Art & Architecture Thesaurus)"""
        return f"""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX gvp: <http://vocab.getty.edu/ontology#>

SELECT ?subject ?label WHERE {{
    ?subject skos:prefLabel ?label .
    ?subject gvp:broaderExtended <http://vocab.getty.edu/aat/> .
    FILTER(CONTAINS(LCASE(STR(?label)), "{query.lower()}"))
}}
LIMIT 10
        """

    def _build_getty_ulan_query(self, query: str) -> str:
        """Build SPARQL query for Getty ULAN (Union List of Artist Names)"""
        return f"""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX gvp: <http://vocab.getty.edu/ontology#>
PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>

SELECT ?subject ?label WHERE {{
    ?subject gvp:prefLabelGVP/xl:literalForm ?label .
    FILTER(CONTAINS(LCASE(STR(?label)), "{query.lower()}"))
}}
LIMIT 10
        """

    async def _search_yale_lux(self, query: str, context: str) -> List[Dict]:
        """
        Search Yale LUX collection using their API
        """
        try:
            search_url = self.config.get_endpoint_url('yale_lux', 'search')

            # Determine search type based on context
            search_type = 'HumanMadeObject'  # Default to objects
            if 'artist' in context.lower() or 'person' in context.lower():
                search_type = 'Person'
            elif 'place' in context.lower():
                search_type = 'Place'

            params = {
                'q': query,
                'type': search_type,
                'page': 1,
                'pageSize': 10
            }

            headers = self.config.get_headers('yale_lux')
            response = await self.client.get(search_url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                results = []

                # Parse Activity Streams format
                if data.get('type') in ['OrderedCollection', 'OrderedCollectionPage']:
                    items = data.get('orderedItems', [])

                    for item in items:
                        result = {
                            'id': item.get('id', ''),
                            'type': item.get('type', ''),
                            'title': item.get('_label', 'Untitled'),
                            'source': 'yale_lux'
                        }

                        # Add additional fields based on type
                        if 'identified_by' in item:
                            for identifier in item['identified_by']:
                                if identifier.get('type') == 'Name':
                                    result['primary_name'] = identifier.get('content', '')
                                    break

                        # Add production info for objects
                        if 'produced_by' in item:
                            production = item['produced_by']
                            if 'carried_out_by' in production:
                                artists = []
                                for agent in production['carried_out_by']:
                                    if '_label' in agent:
                                        artists.append(agent['_label'])
                                if artists:
                                    result['artists'] = artists

                        # Add current location
                        if 'current_location' in item:
                            location = item['current_location']
                            if '_label' in location:
                                result['location'] = location['_label']

                        results.append(result)

                return results
            else:
                logger.error(f"Yale LUX search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Yale LUX search failed: {e}")
            return []

    async def _search_brave(self, query: str, context: str) -> List[Dict]:
        """
        Search the web using Brave Search API for current information
        """
        api_key = self.config.get_api_key('brave_search')
        if not api_key:
            logger.warning("Brave Search API key not configured")
            return []

        try:
            search_url = self.config.get_endpoint_url('brave_search', 'web')
            search_query = f"{query} {context} museum exhibition art"

            headers = self.config.get_headers('brave_search')
            params = {
                'q': search_query,
                'count': 10,
                'search_lang': 'en',
                'country': 'US',
                'safesearch': 'moderate',
                'freshness': 'py'  # Past year for current info
            }

            response = await self.client.get(
                search_url,
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                for result in data.get('web', {}).get('results', []):
                    results.append({
                        'title': result.get('title', ''),
                        'description': result.get('description', ''),
                        'url': result.get('url', ''),
                        'published': result.get('age', ''),
                        'source': 'brave_search',
                        'thumbnail': result.get('thumbnail', {}).get('src', '') if 'thumbnail' in result else ''
                    })

                return results
            elif response.status_code == 401:
                logger.error("Brave Search API authentication failed - check API key")
                return []
            else:
                logger.error(f"Brave Search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return []

    def deduplicate_results(self, results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Remove duplicate results across sources based on title similarity
        """
        # Implement deduplication logic if needed
        # For now, return as-is
        return results


# Convenience function for one-off searches
async def search_all_sources(query: str, context: str = "art") -> Dict[str, List[Dict]]:
    """
    Convenience function to search all available sources

    Args:
        query: Search query
        context: Additional context

    Returns:
        Dictionary with results from each source
    """
    async with EssentialDataClient() as client:
        sources = ['wikipedia', 'wikidata', 'getty', 'yale_lux']

        # Add Brave if API key is available
        if data_config.get_api_key('brave_search'):
            sources.append('brave_search')

        return await client.search_essential(query, sources, context)


__all__ = ['EssentialDataClient', 'search_all_sources']