"""
Artist Quality Scoring

Calculate 0-100 quality scores for artists based on:
- Availability (40%): Number of artworks
- IIIF availability (30%): Percentage with IIIF manifests
- Institution diversity (20%): Number of unique institutions
- Time period match (10%): Overlap with exhibition theme period
"""

from .quality_scorer import QualityScore, QualityScorer

__all__ = ['QualityScore', 'QualityScorer']
