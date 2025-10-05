"""
Multi-dimensional theme relevance scoring for artists

Scores artists on how well they FIT THE THEME based on:
- Semantic match (40%): Keywords from section.focus match artwork titles/descriptions
- Movement match (25%): Artist's works in selected art movements
- Media match (20%): Artist's works in preferred media types
- Time period match (15%): Artist's works in selected time period
- Geographic bonus (5-10%): Works available from nearby institutions
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any
from pydantic import BaseModel, Field
from collections import Counter

from backend.models import CuratorBrief
from backend.config.europeana_topics import TIME_PERIODS, ART_MOVEMENTS, MEDIA_TYPES

logger = logging.getLogger(__name__)


class ScoreDimensions(BaseModel):
    """Individual dimension scores for transparency"""
    semantic_score: float = Field(ge=0, le=100, description="Semantic keyword match (0-100)")
    movement_score: float = Field(ge=0, le=100, description="Art movement match (0-100)")
    media_score: float = Field(ge=0, le=100, description="Media type match (0-100)")
    time_period_score: float = Field(ge=0, le=100, description="Time period match (0-100)")
    geographic_bonus: float = Field(ge=0, le=10, description="Geographic proximity bonus (0-10)")


class RelevanceScore(BaseModel):
    """Complete relevance score for an artist"""
    artist_name: str
    total_score: float = Field(ge=0, le=100, description="Weighted total score")
    dimensions: ScoreDimensions
    works_analyzed: int = Field(description="Number of artworks analyzed")
    match_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed match info")


class ThemeRelevanceScorer:
    """
    Calculate multi-dimensional relevance scores for artists

    Implements Europeana-First scoring: artists who FIT THE THEME get high scores,
    not just artists who are available.
    """

    # Scoring weights (must sum to 100%)
    WEIGHTS = {
        'semantic': 0.40,    # 40% - Most important: does content match?
        'movement': 0.25,    # 25% - Art movement alignment
        'media': 0.20,       # 20% - Media type preference
        'time_period': 0.15  # 15% - Historical period match
    }

    # Geographic bonus for logistical feasibility
    GEOGRAPHIC_BONUS_MAX = 10.0  # Extra points for nearby works

    def __init__(self, curator_brief: CuratorBrief, section_keywords: List[str]):
        """
        Initialize scorer with theme criteria

        Args:
            curator_brief: Form input with movements, media, time period, geography
            section_keywords: Keywords extracted from exhibition section.focus
        """
        self.brief = curator_brief
        self.keywords = set(kw.lower() for kw in section_keywords)

        # Pre-compute normalized movement/media terms for matching
        self.movement_terms = self._get_movement_terms()
        self.media_terms = self._get_media_terms()
        self.time_range = self._get_time_range()
        self.preferred_countries = set(curator_brief.geographic_focus) if curator_brief.geographic_focus else set()

        logger.info(f"Scorer initialized: {len(self.keywords)} keywords, "
                   f"{len(self.movement_terms)} movement terms, "
                   f"{len(self.media_terms)} media terms")

    def score_artist(self, artist_name: str, artworks: List[Dict]) -> RelevanceScore:
        """
        Calculate relevance score for an artist based on their artworks

        Args:
            artist_name: Artist name
            artworks: List of artwork dicts from Europeana (includes title, dcType, year, country, etc.)

        Returns:
            RelevanceScore with total score and dimension breakdown
        """
        if not artworks:
            return RelevanceScore(
                artist_name=artist_name,
                total_score=0.0,
                dimensions=ScoreDimensions(
                    semantic_score=0, movement_score=0, media_score=0,
                    time_period_score=0, geographic_bonus=0
                ),
                works_analyzed=0
            )

        # Calculate each dimension
        semantic_score = self._calculate_semantic_score(artworks)
        movement_score = self._calculate_movement_score(artworks)
        media_score = self._calculate_media_score(artworks)
        time_period_score = self._calculate_time_period_score(artworks)
        geographic_bonus = self._calculate_geographic_bonus(artworks)

        # Weighted total (dimensions sum to 100, then add geographic bonus)
        total_score = (
            semantic_score * self.WEIGHTS['semantic'] +
            movement_score * self.WEIGHTS['movement'] +
            media_score * self.WEIGHTS['media'] +
            time_period_score * self.WEIGHTS['time_period'] +
            geographic_bonus
        )

        # Ensure total doesn't exceed 100
        total_score = min(100.0, total_score)

        dimensions = ScoreDimensions(
            semantic_score=semantic_score,
            movement_score=movement_score,
            media_score=media_score,
            time_period_score=time_period_score,
            geographic_bonus=geographic_bonus
        )

        return RelevanceScore(
            artist_name=artist_name,
            total_score=round(total_score, 2),
            dimensions=dimensions,
            works_analyzed=len(artworks),
            match_details=self._build_match_details(artworks)
        )

    def _calculate_semantic_score(self, artworks: List[Dict]) -> float:
        """
        Calculate semantic keyword match (40% weight)

        Checks how many artworks have titles/descriptions matching theme keywords
        """
        if not self.keywords:
            return 50.0  # Neutral score if no keywords

        matches = 0
        for artwork in artworks:
            # Extract text from title and description
            text_fields = []

            # Title (can be list or string)
            title = artwork.get('title', [])
            if isinstance(title, list):
                text_fields.extend(title)
            elif title:
                text_fields.append(title)

            # Description/subject
            description = artwork.get('dcDescription', [])
            if isinstance(description, list):
                text_fields.extend(description[:2])  # First 2 descriptions
            elif description:
                text_fields.append(description)

            # Check if any keyword appears in text
            combined_text = ' '.join(str(t) for t in text_fields).lower()
            if any(keyword in combined_text for keyword in self.keywords):
                matches += 1

        # Percentage of works matching keywords
        match_percentage = (matches / len(artworks)) * 100

        logger.debug(f"Semantic: {matches}/{len(artworks)} works match keywords = {match_percentage:.1f}%")
        return match_percentage

    def _calculate_movement_score(self, artworks: List[Dict]) -> float:
        """
        Calculate art movement match (25% weight)

        Checks if artwork metadata contains selected movements
        """
        if not self.movement_terms:
            return 50.0  # Neutral if no movements selected

        matches = 0
        for artwork in artworks:
            # Check various metadata fields for movement terms
            text_fields = []

            # Subject/concept fields often contain movement terms
            for field in ['dcSubject', 'dcType', 'edmConcept', 'dcDescription']:
                value = artwork.get(field, [])
                if isinstance(value, list):
                    text_fields.extend(value)
                elif value:
                    text_fields.append(value)

            # Check if any movement term appears
            combined_text = ' '.join(str(t) for t in text_fields).lower()
            if any(term in combined_text for term in self.movement_terms):
                matches += 1

        match_percentage = (matches / len(artworks)) * 100

        logger.debug(f"Movement: {matches}/{len(artworks)} works in selected movements = {match_percentage:.1f}%")
        return match_percentage

    def _calculate_media_score(self, artworks: List[Dict]) -> float:
        """
        Calculate media type match (20% weight)

        Checks if artworks are in preferred media types
        """
        if not self.media_terms:
            return 50.0  # Neutral if no media preferences

        matches = 0
        for artwork in artworks:
            # Check dcType and proxy_dcType fields
            media_fields = []

            for field in ['type', 'dcType', 'edmType']:
                value = artwork.get(field, [])
                if isinstance(value, list):
                    media_fields.extend(value)
                elif value:
                    media_fields.append(value)

            # Check for media type match
            combined_media = ' '.join(str(m) for m in media_fields).lower()
            if any(term in combined_media for term in self.media_terms):
                matches += 1

        match_percentage = (matches / len(artworks)) * 100

        logger.debug(f"Media: {matches}/{len(artworks)} works in preferred media = {match_percentage:.1f}%")
        return match_percentage

    def _calculate_time_period_score(self, artworks: List[Dict]) -> float:
        """
        Calculate time period match (15% weight)

        Checks if artworks were created in selected time period
        """
        if not self.time_range:
            return 50.0  # Neutral if no time period selected

        start_year, end_year = self.time_range
        matches = 0
        total_dated = 0

        for artwork in artworks:
            # Extract year from various fields
            year_value = artwork.get('year')
            if not year_value:
                continue

            # Parse year
            if isinstance(year_value, list):
                year_value = year_value[0] if year_value else None

            if year_value:
                try:
                    year = int(str(year_value)[:4])  # Extract first 4 digits
                    total_dated += 1

                    if start_year <= year <= end_year:
                        matches += 1
                except (ValueError, TypeError):
                    continue

        if total_dated == 0:
            return 50.0  # Neutral if no dated works

        match_percentage = (matches / total_dated) * 100

        logger.debug(f"Time: {matches}/{total_dated} dated works in period [{start_year}-{end_year}] = {match_percentage:.1f}%")
        return match_percentage

    def _calculate_geographic_bonus(self, artworks: List[Dict]) -> float:
        """
        Calculate geographic proximity bonus (0-10 points)

        Awards bonus points for works available from nearby institutions
        """
        if not self.preferred_countries:
            return 0.0

        # Count works from preferred countries
        nearby_works = 0
        for artwork in artworks:
            countries = artwork.get('country', [])
            if not isinstance(countries, list):
                countries = [countries] if countries else []

            if any(c in self.preferred_countries for c in countries):
                nearby_works += 1

        # Award up to 10 bonus points based on percentage
        nearby_percentage = nearby_works / len(artworks)
        bonus = nearby_percentage * self.GEOGRAPHIC_BONUS_MAX

        logger.debug(f"Geographic: {nearby_works}/{len(artworks)} works nearby = +{bonus:.1f} points")
        return round(bonus, 2)

    def _get_movement_terms(self) -> Set[str]:
        """Get normalized movement terms for matching"""
        terms = set()
        if self.brief.art_movements:
            for movement_key in self.brief.art_movements:
                if movement_key in ART_MOVEMENTS:
                    # Add all variants (lowercase for matching)
                    terms.update(term.lower() for term in ART_MOVEMENTS[movement_key])
        return terms

    def _get_media_terms(self) -> Set[str]:
        """Get normalized media terms for matching"""
        terms = set()
        if self.brief.media_types:
            for media_key in self.brief.media_types:
                if media_key in MEDIA_TYPES:
                    # Add all variants (lowercase for matching)
                    terms.update(term.lower() for term in MEDIA_TYPES[media_key])
        return terms

    def _get_time_range(self) -> Optional[tuple]:
        """Get time period range as (start_year, end_year)"""
        if self.brief.time_period and self.brief.time_period in TIME_PERIODS:
            period = TIME_PERIODS[self.brief.time_period]
            return (period['start'], period['end'])
        return None

    def _build_match_details(self, artworks: List[Dict]) -> Dict:
        """Build detailed match information for transparency"""
        # Count institutions
        institutions = set()
        for artwork in artworks:
            provider = artwork.get('dataProvider', [])
            if isinstance(provider, list):
                institutions.update(provider)
            elif provider:
                institutions.add(provider)

        # Count countries
        countries = Counter()
        for artwork in artworks:
            country_list = artwork.get('country', [])
            if not isinstance(country_list, list):
                country_list = [country_list] if country_list else []
            countries.update(country_list)

        return {
            'total_works': len(artworks),
            'institutions_count': len(institutions),
            'top_institutions': list(institutions)[:5],
            'countries': dict(countries.most_common(5))
        }
