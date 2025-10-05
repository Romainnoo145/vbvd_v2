"""
Scoring utilities for artist relevance to exhibition themes
"""

from backend.scoring.theme_relevance_scorer import (
    ThemeRelevanceScorer,
    RelevanceScore,
    ScoreDimensions
)

__all__ = [
    'ThemeRelevanceScorer',
    'RelevanceScore',
    'ScoreDimensions'
]
