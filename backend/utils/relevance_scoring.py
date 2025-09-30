"""
Relevance Scoring Utilities
Multi-factor relevance scoring for artists and artworks
"""

import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)


class ArtistRelevanceScorer:
    """
    Calculate artist relevance scores based on multiple factors

    Scoring components:
    - Theme concept match: 35% (how many concepts they're associated with)
    - Art movement alignment: 30% (modern art movements for VBvD)
    - Chronological fit: 20% (active during theme period)
    - Diversity bonus: 15% (gender/ethnicity representation)
    """

    def calculate_artist_relevance(
        self,
        artist_data: Dict[str, Any],
        theme_concepts: List[str],
        reference_artists: List[str] = None,
        diversity_priority: bool = True
    ) -> tuple[float, str]:
        """
        Calculate comprehensive artist relevance score

        Args:
            artist_data: Artist metadata (name, description, birth_year, etc.)
            theme_concepts: List of exhibition theme concepts
            reference_artists: List of curator-provided reference artist names
            diversity_priority: Whether to apply diversity bonus

        Returns:
            (score, reasoning) tuple
        """
        score_components = {
            'theme_match': 0.0,
            'movement_alignment': 0.0,
            'chronological_fit': 0.0,
            'diversity_bonus': 0.0
        }
        reasoning_parts = []

        artist_name = artist_data.get('name', '')
        description = artist_data.get('description', '').lower()

        # COMPONENT 1: Theme Concept Match (35%)
        theme_score = self._calculate_theme_match(artist_data, theme_concepts)
        score_components['theme_match'] = theme_score * 0.35
        if theme_score >= 0.7:
            matched_concepts = [c for c in theme_concepts if c.lower() in description]
            reasoning_parts.append(f"Strong theme alignment ({', '.join(matched_concepts[:3])})")

        # COMPONENT 2: Art Movement Alignment (30%)
        movement_score = self._calculate_movement_alignment(artist_data)
        score_components['movement_alignment'] = movement_score * 0.30
        if movement_score >= 0.5:
            reasoning_parts.append("Relevant modern art movement")

        # COMPONENT 3: Chronological Fit (20%)
        chrono_score = self._calculate_chronological_fit(artist_data)
        score_components['chronological_fit'] = chrono_score * 0.20

        # COMPONENT 4: Diversity Bonus (15%)
        if diversity_priority and artist_data.get('is_diverse', False):
            score_components['diversity_bonus'] = 0.15
            gender = artist_data.get('gender', 'unknown')
            region = artist_data.get('region', 'unknown')
            if gender == 'female':
                reasoning_parts.append("Female artist")
            if region == 'non-Western':
                reasoning_parts.append("Non-Western perspective")

        # BONUS: Reference Artist Match
        if reference_artists and artist_name in reference_artists:
            # Curator-provided reference artists get a boost
            score_components['theme_match'] = max(score_components['theme_match'], 0.30)
            reasoning_parts.append("Curator reference artist")

        # Calculate final score
        final_score = sum(score_components.values())

        # Build reasoning
        if not reasoning_parts:
            reasoning = f"Artist shows moderate relevance to exhibition theme."
        else:
            reasoning = ". ".join(reasoning_parts) + "."

        return min(1.0, final_score), reasoning

    def _calculate_theme_match(self, artist_data: Dict[str, Any], theme_concepts: List[str]) -> float:
        """Calculate how well artist matches theme concepts"""
        if not theme_concepts:
            return 0.5  # Neutral if no concepts provided

        description = artist_data.get('description', '').lower()
        if not description:
            return 0.3  # Low score for missing description

        # Count concept matches
        matches = sum(1 for concept in theme_concepts if concept.lower() in description)

        # Score: 0.3 base + 0.2 per match (max 1.0)
        score = 0.3 + (matches * 0.2)
        return min(1.0, score)

    def _calculate_movement_alignment(self, artist_data: Dict[str, Any]) -> float:
        """Calculate alignment with modern art movements"""
        description = artist_data.get('description', '').lower()
        if not description:
            return 0.3

        # Modern art movements (Van Bommel van Dam focus)
        modern_movements = [
            'abstract', 'expressionism', 'minimalism', 'modernism', 'contemporary',
            'cubism', 'surrealism', 'de stijl', 'color field', 'geometric',
            'conceptual', 'pop art', 'post-modern', 'avant-garde'
        ]

        # Count movement keywords
        movement_matches = sum(1 for movement in modern_movements if movement in description)

        # Score based on matches
        if movement_matches >= 3:
            return 1.0
        elif movement_matches == 2:
            return 0.8
        elif movement_matches == 1:
            return 0.6
        else:
            return 0.3

    def _calculate_chronological_fit(self, artist_data: Dict[str, Any]) -> float:
        """Calculate chronological relevance (modern art focus)"""
        birth_year = artist_data.get('birth_year')
        death_year = artist_data.get('death_year')

        if not birth_year:
            return 0.5  # Neutral if no date info

        # Modern art era: 1880-present
        # Van Bommel van Dam focuses on 20th-21st century
        if birth_year >= 1880:
            if birth_year >= 1950:
                return 1.0  # Contemporary/late modern
            elif birth_year >= 1900:
                return 0.9  # Mid-20th century
            else:
                return 0.7  # Early modern
        elif birth_year >= 1850:
            return 0.5  # Transitional period
        else:
            return 0.3  # Pre-modern (less relevant)


class ArtworkRelevanceScorer:
    """
    Enhanced artwork relevance scoring

    Scoring components:
    - Artist match: 40% (is this by the selected artist?)
    - Theme alignment: 25% (does it fit the concepts?)
    - Date relevance: 20% (right time period?)
    - Visual quality: 15% (IIIF, images, metadata)
    """

    def calculate_artwork_relevance(
        self,
        artwork_data: Dict[str, Any],
        selected_artist_name: str,
        theme_concepts: List[str],
        theme_period: tuple[int, int] = None  # (start_year, end_year)
    ) -> tuple[float, str]:
        """
        Calculate comprehensive artwork relevance score

        Args:
            artwork_data: Artwork metadata
            selected_artist_name: Name of artist this artwork should be by
            theme_concepts: Exhibition theme concepts
            theme_period: Optional (start_year, end_year) tuple

        Returns:
            (score, reasoning) tuple
        """
        score_components = {
            'artist_match': 0.0,
            'theme_alignment': 0.0,
            'date_relevance': 0.0,
            'visual_quality': 0.0
        }
        reasoning_parts = []

        # COMPONENT 1: Artist Match (40%)
        artwork_artist = artwork_data.get('artist_name', '').lower()
        if selected_artist_name.lower() in artwork_artist or artwork_artist in selected_artist_name.lower():
            score_components['artist_match'] = 0.40
            reasoning_parts.append(f"By {selected_artist_name}")
        else:
            # Wrong artist - major penalty
            score_components['artist_match'] = 0.05

        # COMPONENT 2: Theme Alignment (25%)
        theme_score = self._calculate_theme_alignment(artwork_data, theme_concepts)
        score_components['theme_alignment'] = theme_score * 0.25
        if theme_score >= 0.7:
            reasoning_parts.append("Strong thematic fit")

        # COMPONENT 3: Date Relevance (20%)
        date_score = self._calculate_date_relevance(artwork_data, theme_period)
        score_components['date_relevance'] = date_score * 0.20

        # COMPONENT 4: Visual Quality (15%)
        visual_score = self._calculate_visual_quality(artwork_data)
        score_components['visual_quality'] = visual_score * 0.15
        if artwork_data.get('iiif_manifest'):
            reasoning_parts.append("IIIF available")

        # Calculate final score
        final_score = sum(score_components.values())

        # Build reasoning
        title = artwork_data.get('title', 'Untitled')
        if not reasoning_parts:
            reasoning = f"'{title}' shows moderate relevance."
        else:
            reasoning = f"'{title}': " + ", ".join(reasoning_parts) + "."

        return min(1.0, final_score), reasoning

    def _calculate_theme_alignment(self, artwork_data: Dict[str, Any], theme_concepts: List[str]) -> float:
        """Calculate thematic alignment"""
        if not theme_concepts:
            return 0.5

        # Check title, medium, classifications
        searchable = ' '.join([
            artwork_data.get('title', ''),
            artwork_data.get('medium', ''),
            ' '.join(artwork_data.get('classifications', []))
        ]).lower()

        matches = sum(1 for concept in theme_concepts if concept.lower() in searchable)

        # Score: 0.3 base + 0.25 per match
        return min(1.0, 0.3 + (matches * 0.25))

    def _calculate_date_relevance(self, artwork_data: Dict[str, Any], theme_period: tuple = None) -> float:
        """Calculate date relevance"""
        artwork_year = artwork_data.get('date_created_earliest')
        if not artwork_year:
            return 0.4  # Moderate penalty for missing date

        if not theme_period:
            # No period specified - just check if modern
            return 1.0 if artwork_year >= 1880 else 0.5

        start_year, end_year = theme_period

        # Within period
        if start_year <= artwork_year <= end_year:
            return 1.0

        # Close to period (within 10 years)
        if start_year - 10 <= artwork_year <= end_year + 10:
            return 0.7

        # Outside period
        return 0.3

    def _calculate_visual_quality(self, artwork_data: Dict[str, Any]) -> float:
        """Calculate visual content quality"""
        score = 0.0

        # IIIF manifest (best)
        if artwork_data.get('iiif_manifest'):
            score += 0.5

        # High-res images
        if artwork_data.get('high_res_images'):
            score += 0.3

        # Thumbnail
        if artwork_data.get('thumbnail_url'):
            score += 0.2

        # Metadata completeness bonus
        completeness = artwork_data.get('completeness_score', 0.0)
        score += completeness * 0.2

        return min(1.0, score)


# Convenience functions
def score_artist_relevance(artist_data, theme_concepts, reference_artists=None):
    """Calculate artist relevance score"""
    scorer = ArtistRelevanceScorer()
    return scorer.calculate_artist_relevance(artist_data, theme_concepts, reference_artists)


def score_artwork_relevance(artwork_data, artist_name, theme_concepts, theme_period=None):
    """Calculate artwork relevance score"""
    scorer = ArtworkRelevanceScorer()
    return scorer.calculate_artwork_relevance(artwork_data, artist_name, theme_concepts, theme_period)


__all__ = [
    'ArtistRelevanceScorer',
    'ArtworkRelevanceScorer',
    'score_artist_relevance',
    'score_artwork_relevance'
]
