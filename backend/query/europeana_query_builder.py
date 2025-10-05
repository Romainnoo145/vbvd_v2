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


class EuropeanaQueryBuilder:
    """
    Transform RefinedTheme + CuratorBrief into optimized Europeana queries

    Strategy:
    - Extract semantic keywords from exhibition section focus text
    - Combine with art movements from form
    - Apply structured filters (TYPE, YEAR, media, geography)
    - Generate one query per exhibition section for targeted searches
    - Use BILINGUAL keywords: English + local language for each country
    """

    # Common stopwords for keyword extraction
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'how', 'what', 'when', 'where', 'this',
        'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'can', 'could', 'should'
    }

    # Multilingual art keyword translations
    # Maps English keywords to translations in Dutch (nl), French (fr), German (de)
    MULTILINGUAL_KEYWORDS = {
        # Media types
        'painting': {'nl': 'schilderij', 'fr': 'peinture', 'de': 'Gemälde'},
        'sculpture': {'nl': 'sculptuur', 'fr': 'sculpture', 'de': 'Skulptur'},
        'drawing': {'nl': 'tekening', 'fr': 'dessin', 'de': 'Zeichnung'},
        'photography': {'nl': 'fotografie', 'fr': 'photographie', 'de': 'Fotografie'},
        'print': {'nl': 'prent', 'fr': 'estampe', 'de': 'Druck'},

        # Visual concepts
        'light': {'nl': 'licht', 'fr': 'lumière', 'de': 'Licht'},
        'color': {'nl': 'kleur', 'fr': 'couleur', 'de': 'Farbe'},
        'form': {'nl': 'vorm', 'fr': 'forme', 'de': 'Form'},
        'composition': {'nl': 'compositie', 'fr': 'composition', 'de': 'Komposition'},
        'abstract': {'nl': 'abstract', 'fr': 'abstrait', 'de': 'abstrakt'},
        'landscape': {'nl': 'landschap', 'fr': 'paysage', 'de': 'Landschaft'},
        'portrait': {'nl': 'portret', 'fr': 'portrait', 'de': 'Porträt'},

        # Artistic concepts
        'modern': {'nl': 'modern', 'fr': 'moderne', 'de': 'modern'},
        'contemporary': {'nl': 'hedendaags', 'fr': 'contemporain', 'de': 'zeitgenössisch'},
        'art': {'nl': 'kunst', 'fr': 'art', 'de': 'Kunst'},
        'artist': {'nl': 'kunstenaar', 'fr': 'artiste', 'de': 'Künstler'},
        'exhibition': {'nl': 'tentoonstelling', 'fr': 'exposition', 'de': 'Ausstellung'},
    }

    # Map country codes to language codes
    COUNTRY_LANGUAGES = {
        'netherlands': 'nl',
        'belgium': 'nl',  # Can be nl or fr, using nl as primary
        'france': 'fr',
        'germany': 'de',
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

        Strategy: Generate separate BILINGUAL queries per country
        - Each section × each country = one query with English + local language keywords
        - English keywords ensure international compatibility
        - Local language keywords capture local metadata richness
        - Prevents Europeana relevance bias toward larger collections
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

            # Generate per-country BILINGUAL queries for balanced distribution
            if self.brief.geographic_focus:
                # Calculate rows per country to balance across all countries
                rows_per_country = 200 // len(self.brief.geographic_focus)

                for country in self.brief.geographic_focus:
                    # Build country-specific BILINGUAL query (English + local language)
                    main_query = self._build_bilingual_query(keywords, country)

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
                    logger.info(f"  → {country}: {rows_per_country} rows | Query: {main_query[:80]}...")
            else:
                # Fallback: no geographic filter if not specified (use English only)
                main_query = self._build_bilingual_query(keywords, None)
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

    def _build_bilingual_query(self, section_keywords: List[str], country: Optional[str] = None) -> str:
        """
        Build BILINGUAL search query - English + local language with AND logic for specificity

        Strategy: Use AND to combine different query components
        - Art movements (OR between movements): Surrealism OR Contemporary Art
        - AND context keywords (OR between bilingual pairs): (light OR lumière OR color OR couleur)
        - Result: Artworks must match BOTH movement AND context keywords

        Structure: (movement1 OR movement2) AND (keyword1_en OR keyword1_local OR keyword2_en OR keyword2_local) AND TYPE:IMAGE

        Why this structure?
        ✅ Specific enough: Must match movement AND context (not just any term)
        ✅ Bilingual within each group: English OR local language for each concept
        ✅ Fair and context-rich!

        Args:
            section_keywords: Keywords from section focus (not used - reserved for future)
            country: Target country (e.g., "france", "netherlands") - if None, uses English only

        Returns:
            Query string like: (Surrealism OR "Contemporary Art") AND (light OR lumière OR color OR couleur) AND TYPE:IMAGE
        """
        query_parts = []

        # 1. Art movements group (OR between movements)
        movement_terms = []
        if self.brief.art_movements:
            for movement_key in self.brief.art_movements[:2]:  # Top 2 movements
                if movement_key in ART_MOVEMENTS:
                    movement_list = ART_MOVEMENTS[movement_key]
                    if movement_list:
                        term = movement_list[0]
                        # Quote multi-word movements
                        if ' ' in term:
                            movement_terms.append(f'"{term}"')
                        else:
                            movement_terms.append(term)

        if movement_terms:
            if len(movement_terms) == 1:
                query_parts.append(movement_terms[0])
            else:
                query_parts.append('(' + ' OR '.join(movement_terms) + ')')
        else:
            # Fallback: generic "art"
            query_parts.append('art')

        # 2. Context keywords group - BILINGUAL (OR between all bilingual pairs)
        context_terms = []
        context_keywords = self._get_context_keywords()

        for english_keyword in context_keywords:
            # Add English version
            context_terms.append(english_keyword)

            # Add local language version if country specified
            if country and english_keyword in self.MULTILINGUAL_KEYWORDS:
                country_lower = country.lower()
                if country_lower in self.COUNTRY_LANGUAGES:
                    lang_code = self.COUNTRY_LANGUAGES[country_lower]
                    translations = self.MULTILINGUAL_KEYWORDS[english_keyword]

                    if lang_code in translations:
                        local_term = translations[lang_code]
                        if local_term not in context_terms:  # Avoid duplicates
                            context_terms.append(local_term)

        if context_terms:
            if len(context_terms) == 1:
                query_parts.append(context_terms[0])
            else:
                query_parts.append('(' + ' OR '.join(context_terms) + ')')

        # Build final query with AND between groups
        if len(query_parts) == 1:
            semantic_query = query_parts[0]
        else:
            semantic_query = ' AND '.join(query_parts)

        query = f'{semantic_query} AND TYPE:IMAGE'

        logger.debug(f"Built bilingual query for {country or 'international'}: movements={len(movement_terms)}, context={len(context_terms)}")
        return query

    def _get_context_keywords(self) -> List[str]:
        """
        Get context keywords (English) based on curator brief

        Returns English keywords like ['photography', 'light', 'abstract']
        These will be translated to local language in _build_bilingual_query
        """
        keywords = []

        # Add media types from brief - map to keywords we have translations for
        if self.brief.media_types:
            media_map = {
                'painting': 'painting',
                'sculpture': 'sculpture',
                'photography': 'photography',
                'drawing': 'drawing',
                'print': 'print',
                'video_art': 'modern',  # Video art -> modern
                'installation': 'contemporary',  # Installation -> contemporary
                'mixed_media': 'abstract',  # Mixed media -> abstract
            }
            for media in self.brief.media_types[:2]:  # Top 2
                if media in media_map:
                    keyword = media_map[media]
                    if keyword not in keywords:
                        keywords.append(keyword)

        # Add thematic keywords based on art movements
        if self.brief.art_movements:
            for movement in self.brief.art_movements[:2]:
                if 'surrealism' in movement.lower() or 'surreal' in movement.lower():
                    if 'abstract' not in keywords and len(keywords) < 3:
                        keywords.append('abstract')
                elif 'abstract' in movement.lower():
                    if 'abstract' not in keywords and len(keywords) < 3:
                        keywords.append('abstract')
                elif 'impression' in movement.lower():
                    if 'light' not in keywords and len(keywords) < 3:
                        keywords.append('light')
                elif 'contemporary' in movement.lower():
                    if 'contemporary' not in keywords and len(keywords) < 3:
                        keywords.append('contemporary')

        # Ensure we have at least 2 keywords
        general_keywords = ['light', 'color', 'form']
        for kw in general_keywords:
            if kw not in keywords and len(keywords) < 3:
                keywords.append(kw)

        logger.debug(f"Context keywords: {keywords}")
        return keywords[:3]  # Max 3 context keywords

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


# Note: Query preview functionality is now provided by QueryValidator in query_validator.py
