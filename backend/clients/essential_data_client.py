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
from backend.config.europeana_topics import (
    find_best_theme_match,
    get_europeana_search_params,
    MEDIA_TYPES,
    ART_MOVEMENTS,
)

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
        Search essential sources - Wikipedia, Wikidata, Getty, Yale LUX, Brave, Europeana

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
            elif source == 'europeana':
                tasks.append(self._search_europeana(query, context))
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
            # Initialize client if needed
            if not self.client:
                self.client = httpx.AsyncClient(timeout=self.timeout)

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

            if not response:
                logger.warning("Wikipedia search returned no response")
                return []

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as json_error:
                    logger.warning(f"Wikipedia response JSON parsing failed: {json_error}")
                    return []

                if data is None:
                    logger.warning("Wikipedia search returned None data")
                    return []

                if not isinstance(data, dict):
                    logger.warning(f"Wikipedia search returned non-dict data: {type(data)}")
                    return []

                query_data = data.get('query')
                if query_data is None:
                    logger.warning("Wikipedia search query_data is None")
                    return []

                if not isinstance(query_data, dict):
                    logger.warning(f"Wikipedia query_data is not a dict: {type(query_data)}")
                    return []

                pages = query_data.get('search', [])
                if pages is None:
                    logger.warning("Wikipedia pages is None")
                    return []

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

            if not self.client:
                logger.warning("HTTP client not initialized")
                return None

            response = await self.client.get(summary_url, headers=headers)

            if response is None:
                logger.warning(f"Wikipedia summary for '{title}' returned None response")
                return None

            if response.status_code == 200:
                try:
                    data = response.json()

                    if data is None:
                        logger.warning(f"Wikipedia summary JSON for '{title}' is None")
                        return None

                    if not isinstance(data, dict):
                        logger.warning(f"Wikipedia summary for '{title}' is not a dict: {type(data)}")
                        return None

                    # Safely get the extract field
                    extract = data.get('extract')
                    if extract is None:
                        logger.warning(f"Wikipedia summary for '{title}' has no 'extract' field. Keys: {list(data.keys())}")
                        return None

                    return str(extract)

                except Exception as json_error:
                    logger.warning(f"Wikipedia summary JSON parsing failed for '{title}': {json_error}")
                    return None
            else:
                logger.warning(f"Wikipedia summary for '{title}' returned status {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Failed to get Wikipedia summary for {title}: {e}")
            import traceback
            traceback.print_exc()
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

        NOTE: Getty search is OPTIONAL and may not return results due to
        SPARQL endpoint limitations. The system gracefully degrades without it.
        """
        try:
            logger.warning("Getty Vocabularies search is currently optional and may not return results")
            # Getty SPARQL endpoint has reliability issues - return empty results
            # System will rely on Wikidata and Wikipedia instead
            return []

            # Original implementation kept for reference but disabled:
            """
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

            response = await self.client.get(
                sparql_url,
                params={'query': sparql_query},
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
            """

        except Exception as e:
            logger.warning(f"Getty search skipped (optional): {e}")
            return []

    def _build_getty_aat_query(self, query: str) -> str:
        """Build SPARQL query for Getty AAT (Art & Architecture Thesaurus)"""
        return f"""
PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
PREFIX gvp: <http://vocab.getty.edu/ontology#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>

SELECT ?subject ?label WHERE {{
    ?subject luc:term "{query}";
             a gvp:Concept;
             skos:inScheme <http://vocab.getty.edu/aat/>;
             gvp:prefLabelGVP/xl:literalForm ?label .
}}
LIMIT 10
        """

    def _build_getty_ulan_query(self, query: str) -> str:
        """Build SPARQL query for Getty ULAN (Union List of Artist Names)"""
        return f"""
PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
PREFIX gvp: <http://vocab.getty.edu/ontology#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xl: <http://www.w3.org/2008/05/skos-xl#>

SELECT ?subject ?label WHERE {{
    ?subject luc:term "{query}";
             a gvp:PersonConcept;
             skos:inScheme <http://vocab.getty.edu/ulan/>;
             gvp:prefLabelGVP/xl:literalForm ?label .
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
            # Initialize client if needed
            if not self.client:
                self.client = httpx.AsyncClient(timeout=self.timeout)

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

    async def _search_europeana(self, query: str, context: str) -> List[Dict]:
        """
        Search Europeana - 58M+ cultural heritage items with IIIF support
        Enhanced with theme-based filtering using Europeana topic taxonomy
        """
        api_key = self.config.get_api_key('europeana')
        if not api_key:
            logger.warning("Europeana API key not configured")
            return []

        try:
            search_url = "https://api.europeana.eu/record/v2/search.json"

            # Try to find theme mapping from context
            theme_mapping = find_best_theme_match(context)

            # Build search query based on context
            if 'artist' in context.lower() or 'person' in context.lower():
                # Search by artist name
                search_query = f'who:"{query}" AND TYPE:IMAGE'
            else:
                # General artwork search
                search_query = f'"{query}" AND TYPE:IMAGE'

            # Enhance query with theme-based art movements if available
            if theme_mapping and theme_mapping.art_movements:
                # Add art movement context for better relevance
                movements_query = ' OR '.join([f'"{m}"' for m in theme_mapping.art_movements[:3]])
                # Use OR to broaden search, not restrict it
                search_query = f'({search_query}) OR ({movements_query})'
                logger.info(f"Enhanced Europeana query with movements: {theme_mapping.art_movements[:3]}")

            params = {
                'wskey': api_key,
                'query': search_query,
                'rows': 30,  # Increased from 20 for better results with theme filtering
                'profile': 'rich',  # Get full metadata including IIIF
                'reusability': 'open,restricted',  # Include all available items
                'media': 'true',  # Only items with media
                'thumbnail': 'true',
                'qf': []  # Query facets for additional filtering
            }

            # Add theme-based qf filters if available
            if theme_mapping and theme_mapping.qf_filters:
                for field, values in theme_mapping.qf_filters.items():
                    # Add language suffix for proxy_dc fields
                    if field.startswith('proxy_dc'):
                        field_with_lang = f'{field}.en' if not field.endswith('.en') else field
                        for value in values:
                            params['qf'].append(f'{field_with_lang}:"{value}"')
                    else:
                        for value in values:
                            if field == 'YEAR' and len(values) == 2:
                                # Year range filter
                                params['qf'].append(f'YEAR:[{values[0]} TO {values[1]}]')
                                break
                            else:
                                params['qf'].append(f'{field}:"{value}"')

                if params['qf']:
                    logger.info(f"Applied Europeana qf filters: {params['qf']}")

            # Convert qf list to comma-separated string if not empty
            if not params['qf']:
                del params['qf']

            headers = self.config.get_headers('europeana')
            response = await self.client.get(search_url, params=params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get('items', []):
                    europeana_id = item.get('id', '')
                    result = {
                        'id': europeana_id,
                        'title': item.get('title', ['Untitled'])[0] if isinstance(item.get('title'), list) else item.get('title', 'Untitled'),
                        'source': 'europeana',
                        'type': item.get('type', ''),
                        'url': f"https://www.europeana.eu{europeana_id}",
                        'data_provider': item.get('dataProvider', [''])[0] if isinstance(item.get('dataProvider'), list) else item.get('dataProvider', ''),
                        'country': item.get('country', [''])[0] if isinstance(item.get('country'), list) else item.get('country', '')
                    }

                    # Construct IIIF Manifest URL from Europeana ID
                    # Format: https://iiif.europeana.eu/presentation/{record-id}/manifest
                    if europeana_id:
                        # Remove leading slash if present
                        record_id = europeana_id.lstrip('/')
                        result['iiif_manifest'] = f"https://iiif.europeana.eu/presentation/{record_id}/manifest"

                    # Extract creator/artist
                    if 'dcCreator' in item:
                        creators = item['dcCreator']
                        result['artist_name'] = creators[0] if isinstance(creators, list) else creators

                    # Extract date
                    if 'year' in item:
                        result['date'] = item['year'][0] if isinstance(item['year'], list) else item['year']

                    # Extract image URLs
                    if 'edmIsShownBy' in item:
                        result['image_url'] = item['edmIsShownBy'][0] if isinstance(item['edmIsShownBy'], list) else item['edmIsShownBy']

                    # Thumbnail
                    if 'edmPreview' in item:
                        result['thumbnail_url'] = item['edmPreview'][0] if isinstance(item['edmPreview'], list) else item['edmPreview']

                    # Rights information
                    if 'rights' in item:
                        result['rights'] = item['rights'][0] if isinstance(item['rights'], list) else item['rights']

                    # Description
                    if 'dcDescription' in item:
                        desc = item['dcDescription']
                        result['description'] = desc[0] if isinstance(desc, list) else desc

                    results.append(result)

                logger.info(f"Europeana: Found {len(results)} items, {sum(1 for r in results if r.get('iiif_manifest'))} with IIIF")
                return results

            elif response.status_code == 401:
                logger.error("Europeana API authentication failed - check API key")
                return []
            else:
                logger.error(f"Europeana search failed with status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Europeana search failed: {e}")
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

        # Add Europeana if API key is available
        if data_config.get_api_key('europeana'):
            sources.append('europeana')

        return await client.search_essential(query, sources, context)


__all__ = ['EssentialDataClient', 'search_all_sources']