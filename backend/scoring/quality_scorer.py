"""
Artist Quality Scoring System

4-component scoring (0-100):
- Availability (40%): More works = higher score
- IIIF availability (30%): Higher percentage with IIIF manifests = higher score
- Institution diversity (20%): More institutions = higher score  
- Time period match (10%): Better overlap with theme period = higher score
"""

import logging
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QualityScore(BaseModel):
    """Quality score breakdown for an artist"""
    total_score: float = Field(description="Total quality score (0-100)")
    
    # Component scores
    availability_score: float = Field(description="Availability component (0-40)")
    iiif_score: float = Field(description="IIIF availability component (0-30)")
    institution_diversity_score: float = Field(description="Institution diversity component (0-20)")
    time_period_match_score: float = Field(description="Time period match component (0-10)")
    
    # Detailed breakdown for transparency
    breakdown: Dict[str, Any] = Field(default_factory=dict, description="Detailed scoring breakdown")


class QualityScorer:
    """
    Calculate quality scores for artists based on availability and feasibility
    
    Scoring formula (Appendix C from PRP):
    - Availability (40%): 3-5 works=10-20pts, 6-10=21-30pts, 11-20=31-37pts, 20+=38-40pts
    - IIIF (30%): 80-100%=30pts, 60-80%=24pts, 40-60%=18pts, <40%=proportional
    - Institution diversity (20%): 1 inst=5pts, 2-3=10-15pts, 4-5=16-19pts, 6+=20pts
    - Time period match (10%): 100% overlap=10pts, 50%=5pts, 0%=0pts
    """
    
    def __init__(self, theme_period: Optional[Tuple[int, int]] = None):
        """
        Initialize quality scorer
        
        Args:
            theme_period: Optional (start_year, end_year) for time period matching
        """
        self.theme_period = theme_period
        logger.info(f"QualityScorer initialized with theme_period={theme_period}")
    
    def score_artist(
        self,
        works_count: int,
        iiif_percentage: float,
        institution_count: int,
        year_range: Optional[Tuple[int, int]] = None
    ) -> QualityScore:
        """
        Calculate quality score for an artist
        
        Args:
            works_count: Number of artworks available
            iiif_percentage: Percentage of works with IIIF (0-100)
            institution_count: Number of unique institutions with works
            year_range: Optional (min_year, max_year) of artist's works
            
        Returns:
            QualityScore with total and component breakdowns
        """
        # Calculate each component
        availability = self._score_availability(works_count)
        iiif = self._score_iiif(iiif_percentage)
        institution_diversity = self._score_institution_diversity(institution_count)
        time_period = self._score_time_period_match(year_range)
        
        # Total score
        total = availability + iiif + institution_diversity + time_period
        
        # Build breakdown for transparency
        breakdown = {
            'works_count': works_count,
            'iiif_percentage': iiif_percentage,
            'institution_count': institution_count,
            'year_range': year_range,
            'theme_period': self.theme_period,
            'availability_details': self._get_availability_tier(works_count),
            'iiif_details': self._get_iiif_tier(iiif_percentage),
            'institution_details': self._get_institution_tier(institution_count),
            'period_overlap_percentage': self._calculate_period_overlap(year_range) if year_range else None
        }
        
        return QualityScore(
            total_score=round(total, 1),
            availability_score=round(availability, 1),
            iiif_score=round(iiif, 1),
            institution_diversity_score=round(institution_diversity, 1),
            time_period_match_score=round(time_period, 1),
            breakdown=breakdown
        )
    
    def _score_availability(self, works_count: int) -> float:
        """
        Score availability based on works count (0-40 points)
        
        Tiers:
        - 3-5 works: 10-20 points (incremental)
        - 6-10 works: 21-30 points (incremental)
        - 11-20 works: 31-37 points (incremental)
        - 20+ works: 38-40 points (capped)
        """
        if works_count < 3:
            # Below minimum threshold
            return works_count * 3.33  # 0-10 points
        elif works_count <= 5:
            # 3-5 works: 10-20 points
            return 10 + ((works_count - 3) / 2) * 10
        elif works_count <= 10:
            # 6-10 works: 21-30 points
            return 21 + ((works_count - 6) / 4) * 9
        elif works_count <= 20:
            # 11-20 works: 31-37 points
            return 31 + ((works_count - 11) / 9) * 6
        else:
            # 20+ works: 38-40 points (diminishing returns)
            bonus = min((works_count - 20) / 20, 1) * 2  # Up to 2 extra points
            return 38 + bonus
    
    def _score_iiif(self, iiif_percentage: float) -> float:
        """
        Score IIIF availability (0-30 points)
        
        Tiers:
        - 80-100%: 30 points
        - 60-80%: 24 points
        - 40-60%: 18 points
        - <40%: proportional (0-18 points)
        """
        if iiif_percentage >= 80:
            return 30.0
        elif iiif_percentage >= 60:
            # 60-80%: 24-30 points (linear)
            return 24 + ((iiif_percentage - 60) / 20) * 6
        elif iiif_percentage >= 40:
            # 40-60%: 18-24 points (linear)
            return 18 + ((iiif_percentage - 40) / 20) * 6
        else:
            # <40%: 0-18 points (linear)
            return (iiif_percentage / 40) * 18
    
    def _score_institution_diversity(self, institution_count: int) -> float:
        """
        Score institution diversity (0-20 points)
        
        Tiers:
        - 1 institution: 5 points
        - 2-3 institutions: 10-15 points
        - 4-5 institutions: 16-19 points
        - 6+ institutions: 20 points
        """
        if institution_count <= 1:
            return 5.0
        elif institution_count <= 3:
            # 2-3 institutions: 10-15 points
            return 10 + ((institution_count - 2) / 1) * 5
        elif institution_count <= 5:
            # 4-5 institutions: 16-19 points
            return 16 + ((institution_count - 4) / 1) * 3
        else:
            # 6+ institutions: 20 points
            return 20.0
    
    def _score_time_period_match(self, year_range: Optional[Tuple[int, int]]) -> float:
        """
        Score time period match with theme (0-10 points)
        
        Calculates overlap percentage between artist's year range and theme period
        - 100% overlap: 10 points
        - 50% overlap: 5 points
        - 0% overlap: 0 points
        """
        if not year_range or not self.theme_period:
            # No theme period specified - neutral score
            return 5.0
        
        overlap_percentage = self._calculate_period_overlap(year_range)
        return (overlap_percentage / 100) * 10
    
    def _calculate_period_overlap(self, year_range: Tuple[int, int]) -> float:
        """Calculate percentage overlap between artist's years and theme period"""
        if not self.theme_period:
            return 50.0  # Neutral
        
        artist_start, artist_end = year_range
        theme_start, theme_end = self.theme_period
        
        # Calculate overlap range
        overlap_start = max(artist_start, theme_start)
        overlap_end = min(artist_end, theme_end)
        
        if overlap_start > overlap_end:
            # No overlap
            return 0.0
        
        overlap_years = overlap_end - overlap_start + 1
        artist_years = artist_end - artist_start + 1
        
        # Percentage of artist's career that overlaps with theme
        overlap_percentage = (overlap_years / artist_years) * 100
        return min(overlap_percentage, 100.0)
    
    def _get_availability_tier(self, works_count: int) -> str:
        """Get human-readable availability tier"""
        if works_count < 3:
            return "Below minimum (needs 3+ works)"
        elif works_count <= 5:
            return "Low availability (3-5 works)"
        elif works_count <= 10:
            return "Moderate availability (6-10 works)"
        elif works_count <= 20:
            return "Good availability (11-20 works)"
        else:
            return f"Excellent availability ({works_count} works)"
    
    def _get_iiif_tier(self, iiif_percentage: float) -> str:
        """Get human-readable IIIF tier"""
        if iiif_percentage >= 80:
            return "Excellent IIIF coverage (80%+)"
        elif iiif_percentage >= 60:
            return "Good IIIF coverage (60-80%)"
        elif iiif_percentage >= 40:
            return "Moderate IIIF coverage (40-60%)"
        else:
            return f"Low IIIF coverage ({iiif_percentage:.0f}%)"
    
    def _get_institution_tier(self, institution_count: int) -> str:
        """Get human-readable institution diversity tier"""
        if institution_count <= 1:
            return "Single institution"
        elif institution_count <= 3:
            return f"Limited diversity ({institution_count} institutions)"
        elif institution_count <= 5:
            return f"Good diversity ({institution_count} institutions)"
        else:
            return f"Excellent diversity ({institution_count}+ institutions)"
