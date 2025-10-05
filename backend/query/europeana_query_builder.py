"""
Europeana Query Builder - Transform exhibition themes into optimized Europeana searches

This module bridges the gap between RefinedTheme (creative framework) and Europeana API queries.
Key innovation: Combines SEMANTIC keywords from exhibition sections with STRUCTURED filters from form.
"""

import re
import logging
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field

from backend.models import CuratorBrief
from backend.config.europeana_topics import (
    TIME_PERIODS,
    ART_MOVEMENTS,
    MEDIA_TYPES,
    build_europeana_query
)

logger = logging.getLogger(__name__)


class EuropeanaQuery(BaseModel):
    """Optimized Europeana API query for a specific exhibition section"""
    section_id: str = Field(description="Exhibition section identifier")
    section_title: str = Field(description="Human-readable section title")
    query: str = Field(description="Main search query (broad, semantic)")
    qf: List[str] = Field(default_factory=list, description="Query facet filters (narrow, structured)")
    rows: int = Field(default=200, description="Number of results to fetch")
    preview_count: Optional[int] = Field(default=None, description="Estimated result count from preview")


class QueryPreview(BaseModel):
    """Preview result for query validation"""
    section_id: str
    total_count: int
    institution_count: Optional[int] = None
    status: str  # "good", "warning", "error"
    message: str
    suggestions: List[str] = Field(default_factory=list)


class EuropeanaQueryBuilder:
    """
    Transform RefinedTheme + CuratorBrief into optimized Europeana queries

    Strategy:
    - Extract semantic keywords from exhibition section focus text
    - Combine with art movements from form
    - Apply structured filters (TYPE, YEAR, media, geography)
    - Generate one query per exhibition section for targeted searches
    """

    # Common stopwords for keyword extraction
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'how', 'what', 'when', 'where', 'this',
        'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'can', 'could', 'should'
    }

    def __init__(self, curator_brief: CuratorBrief):
        """
        Initialize QueryBuilder with curator input

        Args:
            curator_brief: Form data with structured selections
        """
        self.brief = curator_brief
        logger.info(f"QueryBuilder initialized with time_period={curator_brief.time_period}, "
                   f"movements={curator_brief.art_movements}, media={curator_brief.media_types}")

    def build_section_queries(self, exhibition_sections: List[Dict]) -> List[EuropeanaQuery]:
        """
        Generate balanced per-country queries for each exhibition section

        Strategy: Generate separate queries per country to ensure balanced geographic distribution
        - Each section × each country = one query
        - Prevents Europeana relevance bias toward larger collections (e.g., Germany)
        - Guarantees equal representation from each geographic_focus country

        Args:
            exhibition_sections: List of ExhibitionSection dicts from RefinedTheme

        Returns:
            List of EuropeanaQuery objects (section_count × country_count queries)
        """
        queries = []

        for section in exhibition_sections:
            section_title = section.get('title', 'Untitled Section')
            section_focus = section.get('focus', '')

            logger.info(f"Building queries for section: {section_title}")

            # Extract semantic keywords from section focus
            keywords = self._extract_keywords(section_focus)

            # Build main query (broad, semantic)
            main_query = self._build_main_query(keywords)

            # Generate per-country queries for balanced distribution
            if self.brief.geographic_focus:
                # Calculate rows per country to balance across all countries
                rows_per_country = 200 // len(self.brief.geographic_focus)

                for country in self.brief.geographic_focus:
                    # Build country-specific filter
                    country_filter = f"COUNTRY:{country}"

                    query = EuropeanaQuery(
                        section_id=f"{self._normalize_section_id(section_title)}-{country.lower()}",
                        section_title=section_title,
                        query=main_query,
                        qf=[country_filter],
                        rows=rows_per_country
                    )

                    queries.append(query)
                    logger.info(f"  → {country}: {rows_per_country} rows with filter {country_filter}")
            else:
                # Fallback: no geographic filter if not specified
                query = EuropeanaQuery(
                    section_id=self._normalize_section_id(section_title),
                    section_title=section_title,
                    query=main_query,
                    qf=[],
                    rows=200
                )
                queries.append(query)
                logger.info(f"Created query without geographic filter: {main_query[:100]}...")

        logger.info(f"Generated {len(queries)} total queries ({len(exhibition_sections)} sections × {len(self.brief.geographic_focus) if self.brief.geographic_focus else 1} countries)")

        return queries

    def _extract_keywords(self, focus_text: str) -> List[str]:
        """
        Extract meaningful keywords from exhibition section focus text

        Uses simple but effective approach:
        - Lowercase and tokenize
        - Remove stopwords
        - Filter short words (<3 chars)
        - Keep top 5-8 keywords

        Args:
            focus_text: Section focus description

        Returns:
            List of semantic keywords
        """
        if not focus_text:
            return []

        # Normalize and tokenize
        text = focus_text.lower()
        # Remove punctuation except hyphens (to keep compound terms)
        text = re.sub(r'[^\w\s-]', ' ', text)
        words = text.split()

        # Filter keywords
        keywords = [
            word for word in words
            if word not in self.STOPWORDS
            and len(word) >= 3
            and not word.isdigit()
        ]

        # Keep top 8 keywords (enough for meaningful search, not too broad)
        keywords = keywords[:8]

        logger.debug(f"Extracted keywords from '{focus_text[:50]}...': {keywords}")
        return keywords

    def _build_main_query(self, section_keywords: List[str]) -> str:
        """
        Build main search query - SIMPLIFIED based on API testing

        Strategy: BROAD discovery with OR logic
        - Art movements from form (primary signal)
        - 1-2 most relevant section keywords
        - OR between terms (broad results for artist discovery)
        - TYPE:IMAGE filter

        Tested approach:
        - "Surrealism" OR "Contemporary Art" OR "digital" → 300+ results ✅
        - Too many keywords with implicit AND → 0 results ❌

        Args:
            section_keywords: Keywords from section focus (we'll use top 1-2)

        Returns:
            Query string like: ("Surrealism" OR "digital art") AND TYPE:IMAGE
        """
        or_terms = []

        # Add art movements from form - these are VALIDATED and work great
        if self.brief.art_movements:
            for movement_key in self.brief.art_movements[:2]:  # Top 2 movements
                if movement_key in ART_MOVEMENTS:
                    movement_terms = ART_MOVEMENTS[movement_key]
                    if movement_terms:
                        # Quote multi-word movements
                        term = movement_terms[0]
                        if ' ' in term:
                            or_terms.append(f'"{term}"')
                        else:
                            or_terms.append(term)

        # Add 1-2 most meaningful section keywords
        # Filter out too-specific words that return 0 results
        meaningful_keywords = [
            kw for kw in section_keywords[:3]
            if len(kw) > 4  # Avoid short generic words
            and kw not in {'exploring', 'examining', 'investigating'}  # Skip action verbs
        ]

        for keyword in meaningful_keywords[:2]:  # Max 2 section keywords
            if ' ' in keyword:
                or_terms.append(f'"{keyword}"')
            else:
                or_terms.append(keyword)

        # Fallback: if no terms, use generic "art"
        if not or_terms:
            or_terms.append('art')

        # Build query with OR logic
        if len(or_terms) == 1:
            semantic_query = or_terms[0]
        else:
            semantic_query = '(' + ' OR '.join(or_terms) + ')'

        query = f'{semantic_query} AND TYPE:IMAGE'

        return query

    def _build_qf_filters(self) -> List[str]:
        """
        Build query facet (qf) filters from structured form input

        Strategy: Europeana API reality check
        - NO TYPE filter (in main query with AND TYPE:IMAGE)
        - NO YEAR filter (too restrictive, filters out most historical art)
        - NO COUNTRY filter (doesn't work as expected - tested!)
        - NO media type filter (proxy_dc_type.en returns 0 results - tested!)

        Use API parameters instead:
        - media=true (only items with media files)
        - thumbnail=true (only items with thumbnails)

        Geographic focus, media type, and time period will be applied as SCORING factors,
        not hard filters, to enable discovery while maintaining relevance.

        Returns:
            Empty list - no qf filters for discovery phase
        """
        filters = []

        # No qf filters - rely on semantic query + API parameters
        # Filtering happens via relevance scoring after retrieval

        return filters

    def _normalize_section_id(self, section_title: str) -> str:
        """Convert section title to URL-safe identifier"""
        normalized = section_title.lower()
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'[\s_]+', '-', normalized)
        return normalized[:50]  # Limit length


def preview_query_results(query: EuropeanaQuery, api_client) -> QueryPreview:
    """
    Preview query results without fetching full data (rows=0)

    Args:
        query: EuropeanaQuery to preview
        api_client: EssentialDataClient instance

    Returns:
        QueryPreview with result counts and validation status
    """
    # This will be implemented in Task 3 (Query Validation)
    # For now, return placeholder
    return QueryPreview(
        section_id=query.section_id,
        total_count=0,
        status="pending",
        message="Preview not yet implemented"
    )
