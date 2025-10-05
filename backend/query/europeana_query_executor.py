"""
Execute Europeana queries in parallel and aggregate results

Fetches artworks from Europeana API using validated queries,
deduplicates results, and prepares for artist extraction.
"""

import os
import logging
import asyncio
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field
import httpx

from backend.query.europeana_query_builder import EuropeanaQuery

logger = logging.getLogger(__name__)


class ArtworkSearchResults(BaseModel):
    """Aggregated artwork search results from multiple sections"""
    total_artworks: int = Field(description="Total artworks fetched (before deduplication)")
    unique_artworks: int = Field(description="Unique artworks (after deduplication)")
    artworks_by_section: Dict[str, int] = Field(default_factory=dict, description="Artwork count per section")
    artworks: List[Dict] = Field(default_factory=list, description="Deduplicated artwork records")
    failed_sections: List[str] = Field(default_factory=list, description="Sections that failed to fetch")
    success_rate: float = Field(description="Percentage of sections that succeeded")


class EuropeanaQueryExecutor:
    """
    Execute Europeana queries in parallel and aggregate results

    Strategy:
    - Run all section queries in parallel (asyncio.gather)
    - Fetch 150-200 artworks per section
    - Deduplicate by europeana ID
    - Tag each artwork with section_id for tracking
    - Handle failures gracefully
    """

    DEFAULT_ROWS_PER_SECTION = 200  # Target artworks per section
    MAX_ROWS_PER_REQUEST = 100  # Europeana API limit
    API_TIMEOUT = 30.0  # 30 second timeout per request

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize executor with Europeana API key

        Args:
            api_key: Europeana API key (defaults to env var EUROPEANA_API_KEY)
        """
        self.api_key = api_key or os.getenv('EUROPEANA_API_KEY')
        if not self.api_key:
            raise ValueError("Europeana API key required (EUROPEANA_API_KEY env var or constructor param)")

        self.api_url = "https://api.europeana.eu/record/v2/search.json"
        logger.info(f"QueryExecutor initialized with API key: {self.api_key[:10]}...")

    async def execute_queries(
        self,
        queries: List[EuropeanaQuery],
        rows_per_section: Optional[int] = None
    ) -> ArtworkSearchResults:
        """
        Execute multiple queries in parallel and aggregate results

        Args:
            queries: List of EuropeanaQuery objects from QueryBuilder
            rows_per_section: Number of artworks to fetch per section (default: 200)

        Returns:
            ArtworkSearchResults with deduplicated artworks and statistics
        """
        if not queries:
            logger.warning("No queries provided to execute")
            return ArtworkSearchResults(
                total_artworks=0,
                unique_artworks=0,
                artworks_by_section={},
                artworks=[],
                failed_sections=[],
                success_rate=0.0
            )

        rows = rows_per_section or self.DEFAULT_ROWS_PER_SECTION

        logger.info(f"Executing {len(queries)} queries in parallel (fetching {rows} artworks each)")

        # Execute all queries in parallel
        tasks = [
            self._execute_single_query(query, rows)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        return self._aggregate_results(queries, results)

    async def _execute_single_query(
        self,
        query: EuropeanaQuery,
        rows: int
    ) -> Optional[Dict]:
        """
        Execute a single Europeana query with pagination support

        Args:
            query: EuropeanaQuery object
            rows: Target number of results to fetch (will paginate if needed)

        Returns:
            Dict with 'items' list or None if failed
        """
        try:
            # Calculate number of pages needed
            num_pages = (rows + self.MAX_ROWS_PER_REQUEST - 1) // self.MAX_ROWS_PER_REQUEST

            logger.info(f"Fetching {rows} artworks for section '{query.section_title}' ({num_pages} pages)...")

            all_items = []
            total_results = 0

            # Fetch multiple pages
            for page in range(num_pages):
                start = page * self.MAX_ROWS_PER_REQUEST + 1  # Europeana uses 1-based indexing

                # Build API parameters
                params = {
                    'wskey': self.api_key,
                    'query': query.query,
                    'rows': min(self.MAX_ROWS_PER_REQUEST, rows - len(all_items)),
                    'start': start,
                    'profile': 'rich',  # Get full metadata
                    'media': 'true',    # Only items with media
                    'thumbnail': 'true'  # Only items with thumbnails
                }

                # Add qf filters if present
                if query.qf:
                    params['qf'] = query.qf

                # Make API request
                async with httpx.AsyncClient(timeout=self.API_TIMEOUT) as client:
                    response = await client.get(self.api_url, params=params)
                    response.raise_for_status()
                    data = response.json()

                # Extract items
                items = data.get('items', [])
                total_results = data.get('totalResults', 0)

                if not items:
                    logger.warning(f"Page {page + 1} returned no items, stopping pagination")
                    break

                all_items.extend(items)
                logger.info(f"  Page {page + 1}/{num_pages}: +{len(items)} artworks (total: {len(all_items)})")

                # Stop if we've reached the target
                if len(all_items) >= rows:
                    break

            logger.info(f"✓ Section '{query.section_title}': {len(all_items)} artworks fetched ({total_results:,} total available)")

            # Tag each artwork with section_id
            for item in all_items:
                item['_section_id'] = query.section_id
                item['_section_title'] = query.section_title

            return {
                'section_id': query.section_id,
                'section_title': query.section_title,
                'items': all_items,
                'total_available': total_results
            }

        except httpx.HTTPError as e:
            logger.error(f"✗ HTTP error fetching section '{query.section_title}': {e}")
            return None
        except Exception as e:
            logger.error(f"✗ Error fetching section '{query.section_title}': {e}")
            return None

    def _aggregate_results(
        self,
        queries: List[EuropeanaQuery],
        results: List
    ) -> ArtworkSearchResults:
        """
        Aggregate results from multiple queries with deduplication

        Args:
            queries: Original query list
            results: Results from asyncio.gather (may include exceptions)

        Returns:
            ArtworkSearchResults with deduplicated artworks
        """
        all_artworks = []
        artworks_by_section = {}
        failed_sections = []
        seen_ids: Set[str] = set()

        # Process each result
        for i, result in enumerate(results):
            query = queries[i]

            # Handle exceptions from asyncio.gather
            if isinstance(result, Exception):
                logger.error(f"Section '{query.section_title}' failed with exception: {result}")
                failed_sections.append(query.section_title)
                artworks_by_section[query.section_title] = 0
                continue

            # Handle None (failed query)
            if result is None:
                failed_sections.append(query.section_title)
                artworks_by_section[query.section_title] = 0
                continue

            # Process successful result
            items = result['items']
            artworks_by_section[query.section_title] = len(items)

            # Add artworks (with deduplication)
            for item in items:
                # Use Europeana ID for deduplication
                artwork_id = item.get('id')
                if artwork_id and artwork_id not in seen_ids:
                    seen_ids.add(artwork_id)
                    all_artworks.append(item)

        # Calculate statistics
        total_fetched = sum(artworks_by_section.values())
        unique_count = len(all_artworks)
        success_rate = ((len(queries) - len(failed_sections)) / len(queries)) * 100

        logger.info(f"Aggregation complete: {total_fetched} total, {unique_count} unique artworks")
        logger.info(f"Success rate: {success_rate:.1f}% ({len(queries) - len(failed_sections)}/{len(queries)} sections)")

        if failed_sections:
            logger.warning(f"Failed sections: {', '.join(failed_sections)}")

        # Check minimum threshold (2/3 sections must succeed)
        min_required = max(1, (len(queries) * 2) // 3)
        successful = len(queries) - len(failed_sections)

        if successful < min_required:
            logger.warning(f"Only {successful}/{len(queries)} sections succeeded (minimum: {min_required})")

        return ArtworkSearchResults(
            total_artworks=total_fetched,
            unique_artworks=unique_count,
            artworks_by_section=artworks_by_section,
            artworks=all_artworks,
            failed_sections=failed_sections,
            success_rate=round(success_rate, 2)
        )
