"""
Curator Input Validator
Validates curator input BEFORE agent processing to ensure query feasibility
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Validation status levels"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ConceptValidationResult:
    """Result of validating a single concept against Getty AAT"""
    concept: str
    is_valid: bool
    getty_aat_uri: Optional[str] = None
    getty_aat_id: Optional[str] = None
    confidence_score: float = 0.0
    suggested_alternatives: List[str] = None
    validation_message: str = ""

    def __post_init__(self):
        if self.suggested_alternatives is None:
            self.suggested_alternatives = []


@dataclass
class ArtistValidationResult:
    """Result of validating a single artist against Getty ULAN"""
    artist_name: str
    is_valid: bool
    getty_ulan_uri: Optional[str] = None
    getty_ulan_id: Optional[str] = None
    wikidata_uri: Optional[str] = None
    confidence_score: float = 0.0
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = None
    validation_message: str = ""


@dataclass
class FeasibilityAssessment:
    """Assessment of query feasibility based on historical patterns"""
    overall_score: float
    concept_coverage: float
    artist_availability: float
    expected_artworks: int
    complexity_rating: str  # "simple", "moderate", "complex"
    success_probability: float
    recommendations: List[str]
    risk_factors: List[str]


@dataclass
class ValidationResult:
    """Complete validation result for curator brief"""
    brief_id: str
    validation_status: ValidationStatus
    overall_confidence: float
    concept_validations: List[ConceptValidationResult]
    artist_validations: List[ArtistValidationResult]
    feasibility_assessment: FeasibilityAssessment
    validation_messages: List[str]
    recommendations: List[str]
    validated_at: datetime
    processing_time_seconds: float


class CuratorInputValidator:
    """
    Validates curator input before expensive agent processing
    Checks Getty AAT/ULAN resolution and estimates query feasibility
    """

    def __init__(self, data_client: EssentialDataClient):
        self.data_client = data_client
        self.validation_cache = {}  # Simple in-memory cache

    async def validate_curator_brief(self, brief: CuratorBrief) -> ValidationResult:
        """
        Perform complete validation of a curator brief

        Args:
            brief: CuratorBrief object to validate

        Returns:
            ValidationResult with detailed validation analysis
        """
        start_time = datetime.utcnow()

        logger.info(f"Starting validation for brief: {brief.theme_title}")

        # Run validations in parallel for efficiency
        concept_task = self._validate_concepts(brief.theme_concepts)
        artist_task = self._validate_artists(brief.reference_artists) if brief.reference_artists else []

        # Wait for both validations to complete
        if isinstance(artist_task, list):
            concept_results = await concept_task
            artist_results = artist_task
        else:
            concept_results, artist_results = await asyncio.gather(
                concept_task,
                artist_task
            )

        # Assess overall feasibility
        feasibility = await self._assess_feasibility(
            brief, concept_results, artist_results
        )

        # Calculate overall status and confidence
        validation_status, overall_confidence = self._calculate_overall_status(
            concept_results, artist_results, feasibility
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            brief, concept_results, artist_results, feasibility
        )

        # Compile validation messages
        validation_messages = self._compile_validation_messages(
            concept_results, artist_results, feasibility
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        result = ValidationResult(
            brief_id=getattr(brief, 'id', 'temp-brief'),
            validation_status=validation_status,
            overall_confidence=overall_confidence,
            concept_validations=concept_results,
            artist_validations=artist_results,
            feasibility_assessment=feasibility,
            validation_messages=validation_messages,
            recommendations=recommendations,
            validated_at=start_time,
            processing_time_seconds=processing_time
        )

        logger.info(f"Validation completed in {processing_time:.2f}s - Status: {validation_status}")

        return result

    async def _validate_concepts(self, concepts: List[str]) -> List[ConceptValidationResult]:
        """Validate theme concepts against Getty AAT"""
        if not concepts:
            return []

        results = []

        for concept in concepts:
            # Check cache first
            cache_key = f"concept:{concept.lower()}"
            if cache_key in self.validation_cache:
                results.append(self.validation_cache[cache_key])
                continue

            try:
                # Search Getty for the concept (includes both AAT and ULAN)
                getty_results = await self.data_client._search_getty(concept, "concept")

                if getty_results and len(getty_results) > 0:
                    # Found matching concepts
                    best_match = getty_results[0]  # Take the first result

                    result = ConceptValidationResult(
                        concept=concept,
                        is_valid=True,
                        getty_aat_uri=best_match.get('uri', ''),
                        getty_aat_id=best_match.get('id', ''),
                        confidence_score=0.85,  # High confidence for direct matches
                        validation_message=f"Found in Getty AAT: {best_match.get('label', 'Unknown')}"
                    )

                    # Add alternatives if available
                    if len(getty_results) > 1:
                        result.suggested_alternatives = [
                            res.get('label', '') for res in getty_results[1:4]
                        ]

                else:
                    # No direct match found - check for broader terms
                    broader_search = await self._search_broader_concepts(concept)

                    result = ConceptValidationResult(
                        concept=concept,
                        is_valid=bool(broader_search),
                        confidence_score=0.3 if broader_search else 0.0,
                        suggested_alternatives=broader_search,
                        validation_message=(
                            f"No direct match found. Consider broader terms."
                            if broader_search else
                            f"No matching concept found in Getty AAT"
                        )
                    )

                # Cache the result
                self.validation_cache[cache_key] = result
                results.append(result)

            except Exception as e:
                logger.error(f"Error validating concept '{concept}': {e}")
                results.append(ConceptValidationResult(
                    concept=concept,
                    is_valid=False,
                    confidence_score=0.0,
                    validation_message=f"Validation error: {str(e)}"
                ))

        return results

    async def _validate_artists(self, artists: List[str]) -> List[ArtistValidationResult]:
        """Validate reference artists against Getty ULAN and Wikidata"""
        if not artists:
            return []

        results = []

        for artist_name in artists:
            cache_key = f"artist:{artist_name.lower()}"
            if cache_key in self.validation_cache:
                results.append(self.validation_cache[cache_key])
                continue

            try:
                # Search both Getty and Wikidata in parallel
                getty_task = self.data_client._search_getty(artist_name, "artist")
                wikidata_task = self.data_client._search_wikidata(artist_name, "artist")

                getty_results, wikidata_results = await asyncio.gather(
                    getty_task, wikidata_task, return_exceptions=True
                )

                # Process Getty ULAN results
                getty_data = None
                if not isinstance(getty_results, Exception) and getty_results:
                    getty_data = getty_results[0] if getty_results else None

                # Process Wikidata results
                wikidata_data = None
                if not isinstance(wikidata_results, Exception) and wikidata_results:
                    # Look for artist entities in Wikidata results
                    for item in wikidata_results:
                        if 'painter' in item.get('description', '').lower() or \
                           'artist' in item.get('description', '').lower():
                            wikidata_data = item
                            break

                # Determine validation result
                is_valid = bool(getty_data or wikidata_data)
                confidence = 0.9 if getty_data else (0.7 if wikidata_data else 0.0)

                result = ArtistValidationResult(
                    artist_name=artist_name,
                    is_valid=is_valid,
                    getty_ulan_uri=getty_data.get('uri') if getty_data else None,
                    getty_ulan_id=getty_data.get('id') if getty_data else None,
                    wikidata_uri=wikidata_data.get('url') if wikidata_data else None,
                    confidence_score=confidence,
                    birth_year=self._extract_birth_year(getty_data or wikidata_data),
                    death_year=self._extract_death_year(getty_data or wikidata_data),
                    nationality=self._extract_nationality(getty_data or wikidata_data),
                    validation_message=(
                        f"Found in {'Getty ULAN' if getty_data else 'Wikidata'}"
                        if is_valid else
                        "Artist not found in authority databases"
                    )
                )

                self.validation_cache[cache_key] = result
                results.append(result)

            except Exception as e:
                logger.error(f"Error validating artist '{artist_name}': {e}")
                results.append(ArtistValidationResult(
                    artist_name=artist_name,
                    is_valid=False,
                    confidence_score=0.0,
                    validation_message=f"Validation error: {str(e)}"
                ))

        return results

    async def _assess_feasibility(
        self,
        brief: CuratorBrief,
        concept_results: List[ConceptValidationResult],
        artist_results: List[ArtistValidationResult]
    ) -> FeasibilityAssessment:
        """Assess overall query feasibility based on validation results"""

        # Calculate concept coverage
        valid_concepts = sum(1 for r in concept_results if r.is_valid)
        concept_coverage = valid_concepts / len(concept_results) if concept_results else 0

        # Calculate artist availability
        valid_artists = sum(1 for r in artist_results if r.is_valid)
        artist_availability = valid_artists / len(artist_results) if artist_results else 1.0

        # Estimate expected artworks based on historical patterns
        expected_artworks = await self._estimate_artwork_count(
            concept_results, artist_results, brief
        )

        # Determine complexity rating
        complexity_rating = self._calculate_complexity(brief, concept_results, artist_results)

        # Calculate success probability
        success_probability = (concept_coverage * 0.6 + artist_availability * 0.4)

        # Calculate overall feasibility score
        overall_score = min(success_probability * 0.8 + (expected_artworks / 100) * 0.2, 1.0)

        # Generate recommendations and risk factors
        recommendations = []
        risk_factors = []

        if concept_coverage < 0.7:
            recommendations.append("Consider refining theme concepts for better Getty AAT matches")
            risk_factors.append("Low concept validation rate may limit discovery")

        if artist_availability < 0.5:
            recommendations.append("Add more well-documented artists to improve results")
            risk_factors.append("Limited artist data may reduce artwork discovery")

        if expected_artworks < 20:
            recommendations.append("Broaden search criteria to increase artwork candidates")
            risk_factors.append("Low expected artwork count")

        if complexity_rating == "complex":
            recommendations.append("Consider breaking down into smaller focused exhibitions")
            risk_factors.append("High complexity may require more curation time")

        return FeasibilityAssessment(
            overall_score=overall_score,
            concept_coverage=concept_coverage,
            artist_availability=artist_availability,
            expected_artworks=expected_artworks,
            complexity_rating=complexity_rating,
            success_probability=success_probability,
            recommendations=recommendations,
            risk_factors=risk_factors
        )

    async def _search_broader_concepts(self, concept: str) -> List[str]:
        """Search for broader or related concepts"""
        # This would typically use a thesaurus or ontology
        # For now, return empty list - can be enhanced later
        return []

    def _extract_birth_year(self, artist_data: Optional[Dict]) -> Optional[int]:
        """Extract birth year from artist data"""
        if not artist_data:
            return None

        # Try various fields that might contain birth year
        for field in ['birth_date', 'born', 'birth_year']:
            if field in artist_data:
                try:
                    # Extract year from date string
                    date_str = str(artist_data[field])
                    # Look for 4-digit year
                    import re
                    year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', date_str)
                    if year_match:
                        return int(year_match.group(1))
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_death_year(self, artist_data: Optional[Dict]) -> Optional[int]:
        """Extract death year from artist data"""
        if not artist_data:
            return None

        for field in ['death_date', 'died', 'death_year']:
            if field in artist_data:
                try:
                    date_str = str(artist_data[field])
                    import re
                    year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', date_str)
                    if year_match:
                        return int(year_match.group(1))
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_nationality(self, artist_data: Optional[Dict]) -> Optional[str]:
        """Extract nationality from artist data"""
        if not artist_data:
            return None

        for field in ['nationality', 'country', 'place_of_birth']:
            if field in artist_data:
                return str(artist_data[field])
        return None

    async def _estimate_artwork_count(
        self,
        concept_results: List[ConceptValidationResult],
        artist_results: List[ArtistValidationResult],
        brief: CuratorBrief
    ) -> int:
        """Estimate expected artwork count based on historical patterns"""

        # Base estimate on number of valid artists and concepts
        valid_artists = sum(1 for r in artist_results if r.is_valid)
        valid_concepts = sum(1 for r in concept_results if r.is_valid)

        # Basic estimation formula (can be refined with actual historical data)
        base_estimate = valid_artists * 15  # Assume ~15 artworks per artist
        concept_multiplier = 1 + (valid_concepts * 0.1)  # More concepts = more variety

        # Adjust for international inclusion
        if brief.include_international:
            base_estimate *= 1.5

        # Adjust for duration (longer exhibitions can have more works)
        if brief.duration_weeks and brief.duration_weeks > 12:
            base_estimate *= 1.2

        return int(base_estimate * concept_multiplier)

    def _calculate_complexity(
        self,
        brief: CuratorBrief,
        concept_results: List[ConceptValidationResult],
        artist_results: List[ArtistValidationResult]
    ) -> str:
        """Calculate exhibition complexity rating"""

        complexity_score = 0

        # Number of concepts
        if len(concept_results) > 5:
            complexity_score += 2
        elif len(concept_results) > 3:
            complexity_score += 1

        # Number of artists
        if len(artist_results) > 8:
            complexity_score += 2
        elif len(artist_results) > 5:
            complexity_score += 1

        # International scope
        if brief.include_international:
            complexity_score += 1

        # Duration
        if brief.duration_weeks and brief.duration_weeks > 16:
            complexity_score += 1

        # Budget considerations
        if brief.budget_max and brief.budget_max > 500000:
            complexity_score += 1

        if complexity_score >= 5:
            return "complex"
        elif complexity_score >= 3:
            return "moderate"
        else:
            return "simple"

    def _calculate_overall_status(
        self,
        concept_results: List[ConceptValidationResult],
        artist_results: List[ArtistValidationResult],
        feasibility: FeasibilityAssessment
    ) -> Tuple[ValidationStatus, float]:
        """Calculate overall validation status and confidence"""

        # Check for critical errors
        concept_validity = sum(1 for r in concept_results if r.is_valid) / len(concept_results) if concept_results else 1.0
        artist_validity = sum(1 for r in artist_results if r.is_valid) / len(artist_results) if artist_results else 1.0

        overall_confidence = feasibility.overall_score

        if concept_validity < 0.3 or artist_validity < 0.3:
            return ValidationStatus.ERROR, overall_confidence
        elif concept_validity < 0.7 or artist_validity < 0.7 or feasibility.overall_score < 0.6:
            return ValidationStatus.WARNING, overall_confidence
        else:
            return ValidationStatus.VALID, overall_confidence

    def _generate_recommendations(
        self,
        brief: CuratorBrief,
        concept_results: List[ConceptValidationResult],
        artist_results: List[ArtistValidationResult],
        feasibility: FeasibilityAssessment
    ) -> List[str]:
        """Generate actionable recommendations for improving the brief"""

        recommendations = list(feasibility.recommendations)  # Start with feasibility recommendations

        # Concept-specific recommendations
        invalid_concepts = [r for r in concept_results if not r.is_valid]
        if invalid_concepts:
            recommendations.append(
                f"Consider revising these concepts: {', '.join([r.concept for r in invalid_concepts[:3]])}"
            )

        # Artist-specific recommendations
        invalid_artists = [r for r in artist_results if not r.is_valid]
        if invalid_artists:
            recommendations.append(
                f"Consider well-documented artists instead of: {', '.join([r.artist_name for r in invalid_artists[:3]])}"
            )

        # Budget recommendations
        if brief.budget_max and brief.budget_max < 50000 and feasibility.expected_artworks > 50:
            recommendations.append("Consider increasing budget for loan fees and insurance costs")

        # Duration recommendations
        if brief.duration_weeks and brief.duration_weeks < 8 and feasibility.complexity_rating == "complex":
            recommendations.append("Consider extending exhibition duration for complex themes")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _compile_validation_messages(
        self,
        concept_results: List[ConceptValidationResult],
        artist_results: List[ArtistValidationResult],
        feasibility: FeasibilityAssessment
    ) -> List[str]:
        """Compile all validation messages into a summary"""

        messages = []

        # Concept validation summary
        valid_concepts = sum(1 for r in concept_results if r.is_valid)
        messages.append(f"Concepts: {valid_concepts}/{len(concept_results)} validated against Getty AAT")

        # Artist validation summary
        valid_artists = sum(1 for r in artist_results if r.is_valid)
        messages.append(f"Artists: {valid_artists}/{len(artist_results)} found in authority databases")

        # Feasibility summary
        messages.append(f"Expected artworks: ~{feasibility.expected_artworks}")
        messages.append(f"Complexity: {feasibility.complexity_rating}")
        messages.append(f"Success probability: {feasibility.success_probability:.1%}")

        return messages