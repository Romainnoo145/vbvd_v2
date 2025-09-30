"""
Quality Metrics Calculator for Exhibition Proposals
PRP Phase 3.2 - Comprehensive Quality Metrics Testing

Calculates overall quality score based on:
- Theme confidence: ≥ 0.70
- Artist relevance: ≥ 0.75
- Artwork metadata completeness: ≥ 0.60
- Artwork with images: ≥ 60%
- IIIF manifests: ≥ 40%
- Diversity representation: ≥ 30%
- Overall target: ≥ 0.80
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for an exhibition proposal"""

    # Component scores
    theme_confidence: float
    artist_relevance_avg: float
    artist_filtering_quality: float
    artwork_relevance_avg: float
    metadata_completeness_avg: float
    image_availability_pct: float
    iiif_availability_pct: float
    diversity_representation_pct: float

    # Counts
    total_artists: int
    total_artworks: int
    artists_with_issues: int
    artworks_below_threshold: int

    # Overall score
    overall_quality_score: float

    # Pass/fail flags
    meets_minimum_requirements: bool
    target_achieved: bool  # ≥ 0.80


class QualityMetricsCalculator:
    """
    Calculate comprehensive quality metrics for exhibition proposals
    """

    # PRP Target Thresholds
    MIN_THEME_CONFIDENCE = 0.70
    MIN_ARTIST_RELEVANCE = 0.75
    MIN_ARTWORK_COMPLETENESS = 0.60
    MIN_IMAGE_AVAILABILITY = 0.60
    MIN_IIIF_AVAILABILITY = 0.40
    MIN_DIVERSITY = 0.30
    TARGET_OVERALL_QUALITY = 0.80

    def calculate_exhibition_quality(
        self,
        theme_data: Dict[str, Any],
        artists_data: List[Dict[str, Any]],
        artworks_data: List[Dict[str, Any]]
    ) -> QualityMetrics:
        """
        Calculate overall quality metrics for an exhibition proposal

        Args:
            theme_data: RefinedTheme data with validated concepts
            artists_data: List of discovered artist data
            artworks_data: List of artwork candidates

        Returns:
            QualityMetrics with comprehensive scoring
        """
        logger.info("=== CALCULATING EXHIBITION QUALITY METRICS ===")

        # Component 1: Theme Confidence
        theme_confidence = self._calculate_theme_confidence(theme_data)

        # Component 2: Artist Quality
        artist_relevance, artist_filtering_quality, artists_with_issues = self._calculate_artist_quality(artists_data)

        # Component 3: Artwork Quality
        artwork_relevance, metadata_completeness, artworks_below_threshold = self._calculate_artwork_quality(artworks_data)

        # Component 4: Visual Content Availability
        image_pct, iiif_pct = self._calculate_visual_availability(artworks_data)

        # Component 5: Diversity Metrics
        diversity_pct = self._calculate_diversity_metrics(artists_data)

        # Calculate Overall Quality Score (weighted average)
        overall_score = self._calculate_overall_score(
            theme_confidence,
            artist_relevance,
            artist_filtering_quality,
            artwork_relevance,
            metadata_completeness,
            image_pct,
            iiif_pct,
            diversity_pct
        )

        # Check requirements
        meets_minimum = all([
            theme_confidence >= self.MIN_THEME_CONFIDENCE,
            artist_relevance >= self.MIN_ARTIST_RELEVANCE,
            metadata_completeness >= self.MIN_ARTWORK_COMPLETENESS,
            image_pct >= self.MIN_IMAGE_AVAILABILITY,
            iiif_pct >= self.MIN_IIIF_AVAILABILITY,
            diversity_pct >= self.MIN_DIVERSITY
        ])

        target_achieved = overall_score >= self.TARGET_OVERALL_QUALITY

        metrics = QualityMetrics(
            theme_confidence=theme_confidence,
            artist_relevance_avg=artist_relevance,
            artist_filtering_quality=artist_filtering_quality,
            artwork_relevance_avg=artwork_relevance,
            metadata_completeness_avg=metadata_completeness,
            image_availability_pct=image_pct,
            iiif_availability_pct=iiif_pct,
            diversity_representation_pct=diversity_pct,
            total_artists=len(artists_data),
            total_artworks=len(artworks_data),
            artists_with_issues=artists_with_issues,
            artworks_below_threshold=artworks_below_threshold,
            overall_quality_score=overall_score,
            meets_minimum_requirements=meets_minimum,
            target_achieved=target_achieved
        )

        self._log_quality_report(metrics)

        return metrics

    def _calculate_theme_confidence(self, theme_data: Dict[str, Any]) -> float:
        """Calculate theme confidence from RefinedTheme"""
        refinement_confidence = theme_data.get('refinement_confidence', 0.0)

        # Also factor in validated concepts
        validated_concepts = theme_data.get('validated_concepts', [])
        if validated_concepts:
            concept_confidences = [c.get('confidence_score', 0.0) for c in validated_concepts]
            avg_concept_confidence = sum(concept_confidences) / len(concept_confidences)

            # Weighted: 60% concepts, 40% refinement
            theme_confidence = (avg_concept_confidence * 0.6) + (refinement_confidence * 0.4)
        else:
            theme_confidence = refinement_confidence

        return round(theme_confidence, 2)

    def _calculate_artist_quality(
        self,
        artists_data: List[Dict[str, Any]]
    ) -> tuple[float, float, int]:
        """Calculate artist-related quality metrics"""
        if not artists_data:
            return 0.0, 0.0, 0

        # Artist relevance (if available)
        relevance_scores = [a.get('relevance_score', 0.8) for a in artists_data]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)

        # Artist filtering quality (check for art movements, missing birth years)
        issues_count = 0
        for artist in artists_data:
            # Check for required person metadata
            if not artist.get('birth_year'):
                issues_count += 1
            # Check if name might be an art movement (not a person)
            name = artist.get('name', '')
            if not artist.get('gender') and not artist.get('description'):
                issues_count += 1

        filtering_quality = 1.0 - (issues_count / len(artists_data))

        return round(avg_relevance, 2), round(filtering_quality, 2), issues_count

    def _calculate_artwork_quality(
        self,
        artworks_data: List[Dict[str, Any]]
    ) -> tuple[float, float, int]:
        """Calculate artwork-related quality metrics"""
        if not artworks_data:
            return 0.0, 0.0, 0

        # Artwork relevance
        relevance_scores = [a.get('relevance_score', 0.0) for a in artworks_data]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)

        # Metadata completeness
        completeness_scores = [a.get('completeness_score', 0.0) for a in artworks_data]
        avg_completeness = sum(completeness_scores) / len(completeness_scores)

        # Count artworks below threshold
        below_threshold = sum(1 for s in completeness_scores if s < self.MIN_ARTWORK_COMPLETENESS)

        return round(avg_relevance, 2), round(avg_completeness, 2), below_threshold

    def _calculate_visual_availability(
        self,
        artworks_data: List[Dict[str, Any]]
    ) -> tuple[float, float]:
        """Calculate image and IIIF availability percentages"""
        if not artworks_data:
            return 0.0, 0.0

        # Images (any type)
        with_images = sum(1 for a in artworks_data
                         if a.get('thumbnail_url') or a.get('iiif_manifest') or a.get('high_res_images'))
        image_pct = with_images / len(artworks_data)

        # IIIF manifests specifically
        with_iiif = sum(1 for a in artworks_data if a.get('iiif_manifest'))
        iiif_pct = with_iiif / len(artworks_data)

        return round(image_pct, 2), round(iiif_pct, 2)

    def _calculate_diversity_metrics(self, artists_data: List[Dict[str, Any]]) -> float:
        """Calculate diversity representation percentage"""
        if not artists_data:
            return 0.0

        diverse_count = sum(1 for a in artists_data if a.get('is_diverse', False))
        diversity_pct = diverse_count / len(artists_data)

        return round(diversity_pct, 2)

    def _calculate_overall_score(
        self,
        theme_confidence: float,
        artist_relevance: float,
        artist_filtering: float,
        artwork_relevance: float,
        metadata_completeness: float,
        image_pct: float,
        iiif_pct: float,
        diversity_pct: float
    ) -> float:
        """
        Calculate weighted overall quality score

        Weights (total 100%):
        - Theme confidence: 15%
        - Artist quality (relevance + filtering): 25%
        - Artwork quality (relevance + completeness): 30%
        - Visual availability: 20%
        - Diversity: 10%
        """
        score = (
            (theme_confidence * 0.15) +
            ((artist_relevance + artist_filtering) / 2 * 0.25) +
            ((artwork_relevance + metadata_completeness) / 2 * 0.30) +
            ((image_pct + iiif_pct) / 2 * 0.20) +
            (diversity_pct * 0.10)
        )

        return round(score, 2)

    def _log_quality_report(self, metrics: QualityMetrics):
        """Log comprehensive quality report"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("EXHIBITION QUALITY METRICS REPORT")
        logger.info("=" * 60)
        logger.info("")
        logger.info("COMPONENT SCORES:")
        logger.info(f"  Theme Confidence:        {metrics.theme_confidence:.2f} (target: ≥{self.MIN_THEME_CONFIDENCE})")
        logger.info(f"  Artist Relevance:        {metrics.artist_relevance_avg:.2f} (target: ≥{self.MIN_ARTIST_RELEVANCE})")
        logger.info(f"  Artist Filtering:        {metrics.artist_filtering_quality:.2f}")
        logger.info(f"  Artwork Relevance:       {metrics.artwork_relevance_avg:.2f}")
        logger.info(f"  Metadata Completeness:   {metrics.metadata_completeness_avg:.2f} (target: ≥{self.MIN_ARTWORK_COMPLETENESS})")
        logger.info(f"  Image Availability:      {metrics.image_availability_pct:.0%} (target: ≥{self.MIN_IMAGE_AVAILABILITY:.0%})")
        logger.info(f"  IIIF Availability:       {metrics.iiif_availability_pct:.0%} (target: ≥{self.MIN_IIIF_AVAILABILITY:.0%})")
        logger.info(f"  Diversity Representation:{metrics.diversity_representation_pct:.0%} (target: ≥{self.MIN_DIVERSITY:.0%})")
        logger.info("")
        logger.info("STATISTICS:")
        logger.info(f"  Total Artists:           {metrics.total_artists}")
        logger.info(f"  Artists with Issues:     {metrics.artists_with_issues}")
        logger.info(f"  Total Artworks:          {metrics.total_artworks}")
        logger.info(f"  Artworks Below Threshold:{metrics.artworks_below_threshold}")
        logger.info("")
        logger.info(f"OVERALL QUALITY SCORE:     {metrics.overall_quality_score:.2f}")
        logger.info(f"  Minimum Requirements:    {'✓ PASS' if metrics.meets_minimum_requirements else '✗ FAIL'}")
        logger.info(f"  Target (≥0.80) Achieved: {'✓ YES' if metrics.target_achieved else '✗ NO'}")
        logger.info("=" * 60)
        logger.info("")


def calculate_quality_score(theme, artists, artworks) -> QualityMetrics:
    """
    Convenience function to calculate quality metrics

    Args:
        theme: RefinedTheme object or dict
        artists: List of artist data
        artworks: List of artwork candidates

    Returns:
        QualityMetrics object
    """
    calculator = QualityMetricsCalculator()

    # Convert Pydantic models to dicts if needed
    if hasattr(theme, 'dict'):
        theme = theme.dict()

    artist_dicts = []
    for artist in artists:
        if hasattr(artist, 'dict'):
            artist_dicts.append(artist.dict())
        else:
            artist_dicts.append(artist)

    artwork_dicts = []
    for artwork in artworks:
        if hasattr(artwork, 'dict'):
            artwork_dicts.append(artwork.dict())
        else:
            artwork_dicts.append(artwork)

    return calculator.calculate_exhibition_quality(theme, artist_dicts, artwork_dicts)


__all__ = ['QualityMetrics', 'QualityMetricsCalculator', 'calculate_quality_score']
