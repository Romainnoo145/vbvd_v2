"""
Theme Refinement Agent - Stage 1 of AI Curator Pipeline
Transforms rough curator input into professional exhibition themes with scholarly backing
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field

# Optional OpenAI dependency for LLM-enhanced theme generation
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief, EnrichedQuery
from backend.validators.curator_input_validator import CuratorInputValidator

logger = logging.getLogger(__name__)


class ConceptValidation(BaseModel):
    """Validated art historical concept"""
    original_concept: str
    refined_concept: str
    getty_aat_uri: str
    getty_aat_id: str
    definition: str
    confidence_score: float
    historical_context: str
    related_concepts: List[str] = Field(default_factory=list)


class ThemeResearch(BaseModel):
    """Research data backing the exhibition theme"""
    wikipedia_sources: List[Dict[str, Any]] = Field(default_factory=list)
    art_historical_context: str
    scholarly_background: str
    current_discourse: str
    key_developments: List[str] = Field(default_factory=list)
    chronological_scope: str
    geographical_scope: str
    research_confidence: float


class ExhibitionSection(BaseModel):
    """Individual exhibition section"""
    title: str
    focus: str
    artist_emphasis: List[str] = Field(default_factory=list)
    estimated_artwork_count: int = Field(ge=5, le=15)


class RefinedTheme(BaseModel):
    """Professional exhibition theme with comprehensive curatorial framework"""
    original_brief_id: str
    session_id: str

    # Core theme elements
    exhibition_title: str
    subtitle: Optional[str] = None
    central_argument: str = Field(description="One sentence thesis statement")
    curatorial_statement: str
    theme_description: str
    scholarly_rationale: str

    # Exhibition structure
    exhibition_sections: List[ExhibitionSection] = Field(min_length=3, max_length=5)
    opening_wall_text: str = Field(description="First text visitors read, max 50 words")

    # Visitor experience
    key_questions: List[str] = Field(min_length=3, max_length=5, description="Questions the exhibition explores")
    contemporary_relevance: str = Field(description="Why this matters now")
    visitor_takeaway: str = Field(description="What visitors should remember")

    # Curatorial framework
    wall_text_strategy: str = Field(description="Tone and approach for labels")
    educational_angles: List[str] = Field(default_factory=list, description="Tour themes, workshop ideas")

    # Validated concepts
    validated_concepts: List[ConceptValidation]
    primary_focus: str
    secondary_themes: List[str] = Field(default_factory=list)

    # Supporting research
    research_backing: ThemeResearch

    # Exhibition parameters
    target_audience_refined: str
    complexity_level: str  # "accessible", "intermediate", "scholarly"
    estimated_duration: str
    space_recommendations: List[str] = Field(default_factory=list)

    # Metadata
    refinement_confidence: float
    iteration_count: int = Field(default=1, description="Number of refinements applied")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_version: str = "1.0"


class ThemeRefinementAgent:
    """
    Stage 1 Agent: Transform curator input into professional exhibition theme

    Workflow:
    1. Validate and enrich concepts using Getty AAT
    2. Research art historical context via Wikipedia
    3. Generate professional exhibition titles and statements
    4. Provide scholarly backing and rationale
    5. Output refined theme ready for Stage 2 (Artist Discovery)
    """

    def __init__(self, data_client: EssentialDataClient, openai_api_key: Optional[str] = None):
        self.data_client = data_client
        self.validator = CuratorInputValidator(data_client)
        self.agent_version = "1.0"

        # Initialize OpenAI client for LLM-enhanced theme generation
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI SDK not installed - using template-based generation")
            self.openai_client = None
        else:
            api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("No OpenAI API key provided - theme generation will use templates")
            self.openai_client = OpenAI(api_key=api_key) if api_key else None

    async def refine_theme(self, brief: CuratorBrief, session_id: str) -> RefinedTheme:
        """
        Transform curator brief into professional exhibition theme

        Args:
            brief: Original curator brief
            session_id: Session identifier for tracking

        Returns:
            RefinedTheme with validated concepts and scholarly backing
        """
        logger.info(f"Starting theme refinement for session {session_id}")
        start_time = datetime.utcnow()

        # Step 1: Validate and enrich concepts (for Getty AAT validation)
        concept_validations = await self._validate_and_enrich_concepts(brief.theme_concepts)

        # Step 2: Research art historical context (lightweight - only for confidence scoring)
        research_data = await self._conduct_research(brief, concept_validations)

        # Step 3: Generate comprehensive exhibition framework in ONE LLM call
        framework = await self._generate_comprehensive_exhibition_framework(brief, concept_validations)

        # Step 4: Determine theme focus and complexity
        primary_focus, secondary_themes = self._analyze_theme_focus(concept_validations)
        complexity_level = self._determine_complexity(brief, concept_validations, research_data)

        # Step 5: Generate recommendations
        space_recommendations = self._generate_space_recommendations(brief, concept_validations)
        audience_refinement = self._refine_target_audience(brief, complexity_level)

        # Step 6: Calculate confidence score
        refinement_confidence = self._calculate_refinement_confidence(
            concept_validations, research_data
        )

        # Step 7: Parse exhibition sections from framework
        exhibition_sections = [
            ExhibitionSection(**section) for section in framework["exhibition_sections"]
        ]

        # Step 8: Assemble refined theme
        refined_theme = RefinedTheme(
            original_brief_id=getattr(brief, 'id', 'temp-brief'),
            session_id=session_id,
            exhibition_title=framework["exhibition_title"],
            subtitle=framework.get("subtitle"),
            central_argument=framework["central_argument"],
            curatorial_statement=framework["curatorial_statement"],
            theme_description=brief.theme_description,  # Keep original as reference
            scholarly_rationale=framework["scholarly_rationale"],
            exhibition_sections=exhibition_sections,
            opening_wall_text=framework["opening_wall_text"],
            key_questions=framework["key_questions"],
            contemporary_relevance=framework["contemporary_relevance"],
            visitor_takeaway=framework["visitor_takeaway"],
            wall_text_strategy=framework["wall_text_strategy"],
            educational_angles=framework.get("educational_angles", []),
            validated_concepts=concept_validations,
            primary_focus=primary_focus,
            secondary_themes=secondary_themes,
            research_backing=research_data,
            target_audience_refined=audience_refinement,
            complexity_level=complexity_level,
            estimated_duration=self._estimate_duration(brief),
            space_recommendations=space_recommendations,
            refinement_confidence=refinement_confidence,
            iteration_count=1,
            agent_version=self.agent_version
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Theme refinement completed in {processing_time:.2f}s - Confidence: {refinement_confidence:.2f}")

        return refined_theme

    async def re_refine_theme(
        self,
        previous_theme: RefinedTheme,
        feedback: str,
        original_brief: CuratorBrief
    ) -> RefinedTheme:
        """
        Re-refine theme based on user feedback

        Fast operation: Reuses research data, only regenerates LLM content

        Args:
            previous_theme: The current refined theme
            feedback: User's feedback for changes
            original_brief: Original curator brief

        Returns:
            Updated RefinedTheme with incremented iteration_count
        """
        logger.info(f"Re-refining theme for session {previous_theme.session_id} (iteration {previous_theme.iteration_count + 1})")
        start_time = datetime.utcnow()

        if not self.openai_client:
            logger.warning("No OpenAI client - cannot re-refine theme")
            return previous_theme

        # Build prompt with previous theme + feedback
        concepts_str = ', '.join([v.refined_concept for v in previous_theme.validated_concepts[:5]])

        prompt = f"""You are the chief curator at Museum Van Bommel Van Dam refining an exhibition based on feedback.

Current Exhibition Framework:
- Title: {previous_theme.exhibition_title}
- Subtitle: {previous_theme.subtitle or "None"}
- Central Argument: {previous_theme.central_argument}
- Curatorial Statement: {previous_theme.curatorial_statement}
- Sections: {len(previous_theme.exhibition_sections)} sections
- Opening Wall Text: {previous_theme.opening_wall_text}

Curator's Feedback:
"{feedback}"

Your task: Adjust the exhibition framework based on this feedback while maintaining the exhibition's core integrity.

Original Context:
- Theme: {original_brief.theme_title}
- Concepts: {concepts_str}
- Target Audience: {original_brief.target_audience}

Return JSON with the SAME structure as before, incorporating the requested changes:
{{
  "exhibition_title": "Adjusted title if requested",
  "subtitle": "Adjusted subtitle or null",
  "central_argument": "Refined thesis",
  "curatorial_statement": "Adjusted statement (250-300 words)",
  "scholarly_rationale": "Updated rationale (150-200 words)",
  "exhibition_sections": [
    {{
      "title": "Section title",
      "focus": "Focus description",
      "artist_emphasis": ["Artists if relevant"],
      "estimated_artwork_count": 8
    }}
  ],
  "opening_wall_text": "Updated opening text (MAX 50 words)",
  "key_questions": ["Question 1", "Question 2", "Question 3"],
  "contemporary_relevance": "Updated relevance",
  "visitor_takeaway": "Updated takeaway",
  "wall_text_strategy": "Tone and approach",
  "educational_angles": ["Angle 1", "Angle 2", "Angle 3"]
}}

Important:
1. If feedback requests shorter title, make it shorter
2. If feedback requests tone change (more/less scholarly), adjust language
3. If feedback requests focus change, adjust sections and emphasis
4. If feedback doesn't mention something, keep it similar to current version
5. Maintain Van Bommel Van Dam's voice: confident, direct, passionate

Return ONLY valid JSON."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=2000,
                temperature=0.6,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}]
            )

            framework_json = response.choices[0].message.content.strip()
            framework = json.loads(framework_json)

            # Parse exhibition sections
            exhibition_sections = [
                ExhibitionSection(**section) for section in framework["exhibition_sections"]
            ]

            # Create updated refined theme (reuse previous research data)
            refined_theme = RefinedTheme(
                original_brief_id=previous_theme.original_brief_id,
                session_id=previous_theme.session_id,
                exhibition_title=framework["exhibition_title"],
                subtitle=framework.get("subtitle"),
                central_argument=framework["central_argument"],
                curatorial_statement=framework["curatorial_statement"],
                theme_description=previous_theme.theme_description,
                scholarly_rationale=framework["scholarly_rationale"],
                exhibition_sections=exhibition_sections,
                opening_wall_text=framework["opening_wall_text"],
                key_questions=framework["key_questions"],
                contemporary_relevance=framework["contemporary_relevance"],
                visitor_takeaway=framework["visitor_takeaway"],
                wall_text_strategy=framework["wall_text_strategy"],
                educational_angles=framework.get("educational_angles", []),
                validated_concepts=previous_theme.validated_concepts,  # Reuse
                primary_focus=previous_theme.primary_focus,  # Reuse
                secondary_themes=previous_theme.secondary_themes,  # Reuse
                research_backing=previous_theme.research_backing,  # Reuse
                target_audience_refined=previous_theme.target_audience_refined,  # Reuse
                complexity_level=previous_theme.complexity_level,  # Reuse
                estimated_duration=previous_theme.estimated_duration,  # Reuse
                space_recommendations=previous_theme.space_recommendations,  # Reuse
                refinement_confidence=previous_theme.refinement_confidence,  # Keep same
                iteration_count=previous_theme.iteration_count + 1,  # Increment
                created_at=datetime.utcnow(),
                agent_version=self.agent_version
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Theme re-refinement completed in {processing_time:.2f}s")

            return refined_theme

        except Exception as e:
            logger.error(f"Re-refinement failed: {e}")
            # Return previous theme unchanged
            return previous_theme

    async def _validate_and_enrich_concepts(self, concepts: List[str]) -> List[ConceptValidation]:
        """
        Validate concepts against Getty AAT and enrich with art historical data (P2-Medium enhancement)

        PRP Improvements:
        - Direct SPARQL queries to Getty AAT as fallback
        - AAT hierarchy for related concepts
        - Enhanced confidence scoring based on match quality
        - Target: ≥0.70 confidence score
        """

        validations = []

        for concept in concepts:
            logger.debug(f"Validating concept: {concept}")

            try:
                # ATTEMPT 1: Search Getty AAT via client (primary method)
                getty_results = await self.data_client._search_getty(concept, "concept")

                if getty_results and len(getty_results) > 0:
                    # Found valid concept
                    best_match = getty_results[0]

                    # Get additional context from Wikipedia
                    wikipedia_context = await self._get_concept_context(concept)

                    # Calculate match quality for confidence score
                    match_quality = self._calculate_match_quality(concept, best_match.get('label', ''))

                    validation = ConceptValidation(
                        original_concept=concept,
                        refined_concept=best_match.get('label', concept),
                        getty_aat_uri=best_match.get('uri', ''),
                        getty_aat_id=best_match.get('id', ''),
                        definition=best_match.get('definition', 'Art historical concept'),
                        confidence_score=min(0.9, 0.7 + (match_quality * 0.2)),  # 0.7-0.9 based on match quality
                        historical_context=wikipedia_context,
                        related_concepts=[r.get('label', '') for r in getty_results[1:4]]  # Related terms
                    )

                else:
                    # ATTEMPT 2: Wikipedia-only fallback with enhanced scoring (Getty SPARQL removed - too slow/unreliable)
                    wikipedia_context = await self._get_concept_context(concept)

                    # Check if Wikipedia context indicates art historical validity
                    art_indicators = ['art', 'artist', 'painting', 'movement', 'style', 'period']
                    context_lower = wikipedia_context.lower()
                    has_art_indicators = sum(1 for indicator in art_indicators if indicator in context_lower)

                    # Enhanced confidence based on Wikipedia validation
                    wikipedia_confidence = 0.5 + (has_art_indicators * 0.05)  # 0.5-0.75 based on indicators
                    wikipedia_confidence = min(0.75, wikipedia_confidence)

                    validation = ConceptValidation(
                        original_concept=concept,
                        refined_concept=concept.title(),
                        getty_aat_uri='',
                        getty_aat_id='',
                        definition=f'Art concept: {concept}',
                        confidence_score=wikipedia_confidence,
                        historical_context=wikipedia_context,
                        related_concepts=[]
                    )

                validations.append(validation)
                logger.info(f"Concept '{concept}' validated with confidence {validation.confidence_score:.2f}")

            except Exception as e:
                logger.error(f"Error validating concept '{concept}': {e}")
                # Create minimal validation even on error
                validations.append(ConceptValidation(
                    original_concept=concept,
                    refined_concept=concept.title(),
                    getty_aat_uri='',
                    getty_aat_id='',
                    definition=f'Art concept: {concept}',
                    confidence_score=0.2,
                    historical_context='',
                    related_concepts=[]
                ))

        avg_confidence = sum(v.confidence_score for v in validations) / len(validations) if validations else 0.0
        logger.info(f"Validated {len(validations)} concepts with avg confidence: {avg_confidence:.2f}")

        return validations

    def _calculate_match_quality(self, original: str, matched: str) -> float:
        """Calculate match quality score (0.0-1.0) between original and matched terms"""
        original_lower = original.lower().strip()
        matched_lower = matched.lower().strip()

        # Exact match
        if original_lower == matched_lower:
            return 1.0

        # Contains match
        if original_lower in matched_lower or matched_lower in original_lower:
            return 0.8

        # Word overlap
        original_words = set(original_lower.split())
        matched_words = set(matched_lower.split())
        if original_words & matched_words:  # Has intersection
            overlap_ratio = len(original_words & matched_words) / max(len(original_words), len(matched_words))
            return 0.5 + (overlap_ratio * 0.3)

        # Default for other matches
        return 0.5

    async def _query_getty_aat_sparql(self, concept: str) -> Optional[Dict[str, Any]]:
        """
        Query Getty AAT directly via SPARQL (P2-Medium enhancement)
        Fallback method when client search fails
        """
        try:
            import httpx

            sparql_endpoint = "http://vocab.getty.edu/sparql"

            # Build SPARQL query for concept search
            sparql_query = f"""
            PREFIX gvp: <http://vocab.getty.edu/ontology#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX aat: <http://vocab.getty.edu/aat/>

            SELECT ?concept ?label ?definition ?broader ?broaderLabel
            WHERE {{
              ?concept a skos:Concept ;
                       skos:inScheme aat: ;
                       skos:prefLabel ?label .

              FILTER(REGEX(?label, "{concept}", "i"))

              OPTIONAL {{
                ?concept skos:definition ?definition .
              }}

              OPTIONAL {{
                ?concept skos:broader ?broader .
                ?broader skos:prefLabel ?broaderLabel .
              }}
            }}
            LIMIT 5
            """

            headers = {
                'Accept': 'application/sparql-results+json',
                'User-Agent': 'AI-Curator-Assistant/1.0 (Educational Project)'
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    sparql_endpoint,
                    data={'query': sparql_query},
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    bindings = data.get('results', {}).get('bindings', [])

                    if bindings:
                        # Use best result
                        best = bindings[0]

                        uri = best.get('concept', {}).get('value', '')
                        label = best.get('label', {}).get('value', concept)
                        definition = best.get('definition', {}).get('value', 'Art historical concept')

                        # Extract ID from URI
                        aat_id = uri.split('/')[-1] if uri else ''

                        # Get related concepts from broader terms
                        related = []
                        if 'broaderLabel' in best:
                            related.append(best['broaderLabel']['value'])

                        return {
                            'uri': uri,
                            'id': aat_id,
                            'label': label,
                            'definition': definition,
                            'related': related
                        }

        except Exception as e:
            logger.warning(f"Getty AAT SPARQL query failed for '{concept}': {e}")

        return None

    async def _get_concept_context(self, concept: str) -> str:
        """Get art historical context for a concept from Wikipedia"""
        try:
            # Search Wikipedia for art-specific information about the concept
            wikipedia_results = await self.data_client._search_wikipedia(f"{concept} art", "art history")

            if wikipedia_results and len(wikipedia_results) > 0:
                # Extract relevant context from the first result
                first_result = wikipedia_results[0]
                content = first_result.get('extract', '')

                # Return first 200 characters as context
                if len(content) > 200:
                    context = content[:200] + "..."
                else:
                    context = content

                return context or f"Art historical movement/concept: {concept}"

        except Exception as e:
            logger.warning(f"Could not fetch Wikipedia context for '{concept}': {e}")

        return f"Art historical concept: {concept}"

    async def _conduct_research(self, brief: CuratorBrief, validations: List[ConceptValidation]) -> ThemeResearch:
        """Conduct comprehensive research to back the exhibition theme"""

        # Gather Wikipedia sources for each validated concept
        wikipedia_sources = []
        key_developments = []

        for validation in validations:
            if validation.confidence_score > 0.5:  # Only research high-confidence concepts
                try:
                    # Get detailed Wikipedia articles
                    wiki_results = await self.data_client._search_wikipedia(
                        validation.refined_concept, "art history"
                    )

                    for result in wiki_results[:2]:  # Top 2 results per concept
                        wikipedia_sources.append({
                            'concept': validation.refined_concept,
                            'title': result.get('title', ''),
                            'extract': result.get('extract', '')[:500],  # First 500 chars
                            'url': result.get('url', ''),
                            'relevance': 'primary' if result == wiki_results[0] else 'secondary'
                        })

                        # Extract key developments
                        extract = result.get('extract', '')
                        if 'century' in extract.lower() or 'movement' in extract.lower():
                            key_developments.append(f"{validation.refined_concept}: {extract[:100]}...")

                except Exception as e:
                    logger.warning(f"Could not research concept '{validation.refined_concept}': {e}")

        # Generate comprehensive art historical context
        art_historical_context = self._synthesize_historical_context(validations, wikipedia_sources)

        # Generate scholarly background
        scholarly_background = self._generate_scholarly_background(brief, validations)

        # Research current discourse using Brave Search
        current_discourse = await self._research_current_discourse(brief, validations)

        # Determine scope
        chronological_scope = self._determine_chronological_scope(validations, wikipedia_sources)
        geographical_scope = self._determine_geographical_scope(brief, validations)

        # Calculate research confidence
        research_confidence = self._calculate_research_confidence(wikipedia_sources, validations)

        return ThemeResearch(
            wikipedia_sources=wikipedia_sources,
            art_historical_context=art_historical_context,
            scholarly_background=scholarly_background,
            current_discourse=current_discourse,
            key_developments=key_developments,
            chronological_scope=chronological_scope,
            geographical_scope=geographical_scope,
            research_confidence=research_confidence
        )

    def _synthesize_historical_context(self, validations: List[ConceptValidation], sources: List[Dict]) -> str:
        """Synthesize art historical context from research"""

        if not validations:
            return "This exhibition explores contemporary artistic practices and their historical foundations."

        # Extract key themes
        primary_concepts = [v.refined_concept for v in validations if v.confidence_score > 0.7]

        if not primary_concepts:
            primary_concepts = [v.refined_concept for v in validations[:2]]  # Take first two if none are high confidence

        # Generate context based on concepts
        if any('impression' in concept.lower() for concept in primary_concepts):
            context = "This exhibition examines the revolutionary artistic movement that emerged in late 19th-century France, fundamentally transforming how artists approached light, color, and the representation of modern life."
        elif any('renaissance' in concept.lower() for concept in primary_concepts):
            context = "This exhibition explores the artistic rebirth that swept through Europe from the 14th to 17th centuries, marking a profound shift in artistic techniques, subject matter, and cultural values."
        elif any('modern' in concept.lower() or 'contemporary' in concept.lower() for concept in primary_concepts):
            context = "This exhibition investigates the radical artistic innovations of the 20th and 21st centuries, tracing how artists have responded to technological, social, and cultural transformations."
        else:
            # Generic but scholarly context
            context = f"This exhibition traces the development of {', '.join(primary_concepts[:2])}, examining how these artistic concepts have shaped creative expression and cultural understanding throughout history."

        return context

    def _generate_scholarly_background(self, brief: CuratorBrief, validations: List[ConceptValidation]) -> str:
        """Generate scholarly background for the exhibition"""

        # Extract validated concepts
        valid_concepts = [v.refined_concept for v in validations if v.confidence_score > 0.5]

        if not valid_concepts:
            return "This exhibition draws upon recent scholarship in art history, museum studies, and cultural analysis to present a comprehensive examination of the selected artworks and their historical significance."

        # Generate scholarly framework
        background = f"Recent scholarship on {', '.join(valid_concepts[:3])} has emphasized the importance of contextualizing artistic production within broader cultural, social, and economic frameworks. "

        background += "This exhibition builds upon interdisciplinary research that examines how artistic practices both reflect and shape their historical moments, offering visitors new insights into the complex relationships between creativity, culture, and society."

        if brief.reference_artists:
            background += f" Drawing upon extensive research on {', '.join(brief.reference_artists[:2])} and their contemporaries, the exhibition presents a nuanced understanding of artistic innovation and cultural exchange."

        return background

    async def _research_current_discourse(self, brief: CuratorBrief, validations: List[ConceptValidation]) -> str:
        """Research current scholarly and public discourse using Brave Search"""

        try:
            # Create search query for current academic discourse
            concepts = [v.refined_concept for v in validations if v.confidence_score > 0.5]
            if concepts:
                search_query = f"{concepts[0]} art exhibition 2023 2024"
            else:
                search_query = f"{brief.theme_title} art exhibition recent"

            # Search for current discourse
            brave_results = await self.data_client._search_brave(search_query, "art exhibition")

            if brave_results and len(brave_results) > 0:
                # Extract current trends from search results
                current_topics = []
                for result in brave_results[:3]:
                    title = result.get('title', '')
                    description = result.get('description', '')
                    if 'exhibition' in title.lower() or 'museum' in title.lower():
                        current_topics.append(f"{title}: {description[:100]}...")

                if current_topics:
                    discourse = "Current exhibitions and scholarly discussions highlight: " + "; ".join(current_topics[:2])
                else:
                    discourse = "This exhibition contributes to ongoing conversations about the role of art in contemporary culture and the importance of historical perspective in understanding artistic innovation."
            else:
                discourse = "This exhibition engages with current scholarly debates about the interpretation and presentation of art historical material in museum contexts."

        except Exception as e:
            logger.warning(f"Could not research current discourse: {e}")
            discourse = "This exhibition contributes to contemporary discussions about art, culture, and historical interpretation."

        return discourse

    async def _generate_exhibition_title(self, brief: CuratorBrief, validations: List[ConceptValidation], research: ThemeResearch) -> Tuple[str, Optional[str]]:
        """Generate compelling exhibition title and subtitle using LLM or templates"""

        # Try LLM-based generation first
        if self.openai_client:
            try:
                return await self._generate_title_with_llm(brief, validations, research)
            except Exception as e:
                logger.warning(f"LLM title generation failed: {e}, falling back to templates")

        # Fallback to template-based generation
        return self._generate_title_with_templates(brief, validations)

    def _generate_title_with_templates(self, brief: CuratorBrief, validations: List[ConceptValidation]) -> Tuple[str, Optional[str]]:
        """Template-based title generation (fallback)"""
        # Extract key elements
        primary_concepts = [v.refined_concept for v in validations if v.confidence_score > 0.7]
        if not primary_concepts:
            primary_concepts = [v.refined_concept for v in validations[:2]]

        # Create sophisticated titles based on art historical conventions
        if brief.reference_artists and len(brief.reference_artists) <= 3:
            # Artist-focused exhibition
            if len(brief.reference_artists) == 1:
                title = f"{brief.reference_artists[0]}: {primary_concepts[0] if primary_concepts else 'Masterworks'}"
                subtitle = "A Comprehensive Retrospective"
            else:
                title = f"{', '.join(brief.reference_artists[:2])} and Contemporaries"
                subtitle = f"Exploring {primary_concepts[0] if primary_concepts else 'Artistic Innovation'}"

        elif primary_concepts:
            # Concept-focused exhibition
            if len(primary_concepts) == 1:
                title = f"The Art of {primary_concepts[0]}"
                subtitle = "Innovation and Tradition in Historical Perspective"
            else:
                title = f"{primary_concepts[0]} and {primary_concepts[1]}"
                subtitle = "Artistic Movements in Dialogue"

        else:
            # Fallback to original brief title, refined
            title = brief.theme_title
            subtitle = "An Art Historical Examination"

        # Ensure title is appropriately scholarly but accessible
        if len(title) > 60:
            # Shorten if too long
            words = title.split()
            title = ' '.join(words[:8]) + ("..." if len(words) > 8 else "")

        return title, subtitle

    async def _generate_title_with_llm(self, brief: CuratorBrief, validations: List[ConceptValidation], research: ThemeResearch) -> Tuple[str, Optional[str]]:
        """Generate exhibition title using OpenAI GPT-4"""

        # Build context for LLM
        concepts_str = ', '.join([v.refined_concept for v in validations[:5]])
        artists_str = ', '.join(brief.reference_artists[:3]) if brief.reference_artists else "Various artists"

        prompt = f"""You are a curator at Museum Van Bommel Van Dam, a leading modern art museum in the Netherlands known for its focus on contemporary and 20th-century art, particularly abstract and conceptual movements.

Your museum's identity:
- Focus: Modern and contemporary art (1900-present)
- Specialty: Abstract art, geometric abstraction, conceptualism
- Audience: Art enthusiasts, collectors, and general public in the Netherlands and Belgium
- Voice: Direct, intellectually engaging, avoiding pretension
- Philosophy: Making modern art accessible while maintaining scholarly rigor

Create an exhibition title that reflects Van Bommel Van Dam's curatorial voice.

Exhibition Brief:
- Theme: {brief.theme_title}
- Key Concepts: {concepts_str}
- Featured Artists: {artists_str}
- Target Audience: {brief.target_audience}
- Duration: {brief.duration_weeks} weeks

Art Historical Context:
{research.art_historical_context[:300]}

Requirements:
1. Title must feel contemporary and fresh, not academic or stuffy
2. Maximum 50 characters for main title (shorter is better!)
3. Subtitle should add clarity and intrigue
4. Use direct, engaging language appropriate for a modern art museum
5. Avoid clichés like "Journey Through", "Exploring", "Rediscovering"
6. Consider that many visitors are Dutch/Belgian - avoid overly complex English
7. Think: What would catch attention in a museum newsletter or Instagram post?

Format your response EXACTLY as:
TITLE: [exhibition title]
SUBTITLE: [subtitle or NONE if not needed]"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=200,
            temperature=0.7,  # Slightly creative for titles
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.choices[0].message.content.strip()

        # Parse response
        title = brief.theme_title  # fallback
        subtitle = None

        if "TITLE:" in response_text:
            title_line = response_text.split("TITLE:")[1].split("\n")[0].strip()
            title = title_line if title_line else brief.theme_title

        if "SUBTITLE:" in response_text:
            subtitle_line = response_text.split("SUBTITLE:")[1].split("\n")[0].strip()
            if subtitle_line and subtitle_line.upper() != "NONE":
                subtitle = subtitle_line

        logger.info(f"LLM generated title: '{title}' / subtitle: '{subtitle}'")
        return title, subtitle

    async def _generate_curatorial_statement(self, brief: CuratorBrief, validations: List[ConceptValidation], research: ThemeResearch) -> str:
        """Generate professional curatorial statement using LLM or templates"""

        # Try LLM-based generation first
        if self.openai_client:
            try:
                return await self._generate_statement_with_llm(brief, validations, research)
            except Exception as e:
                logger.warning(f"LLM statement generation failed: {e}, falling back to templates")

        # Fallback to template-based generation
        return self._generate_statement_with_templates(brief, validations, research)

    def _generate_statement_with_templates(self, brief: CuratorBrief, validations: List[ConceptValidation], research: ThemeResearch) -> str:
        """Template-based curatorial statement (fallback)"""
        # Start with strong opening
        statement = f"This exhibition presents a comprehensive examination of {brief.theme_title.lower()}, "

        # Add scholarly context
        if research.art_historical_context:
            statement += research.art_historical_context.split('.')[0] + ". "

        # Incorporate validated concepts
        valid_concepts = [v.refined_concept for v in validations if v.confidence_score > 0.5]
        if valid_concepts:
            statement += f"Through the lens of {', '.join(valid_concepts[:3])}, visitors will explore how artistic innovation emerges from the intersection of tradition and experimentation. "

        # Add research backing
        if brief.reference_artists:
            statement += f"Featuring works by {', '.join(brief.reference_artists[:3])}, the exhibition demonstrates how individual artistic vision contributes to broader cultural movements. "

        # Conclude with visitor experience
        if brief.target_audience == "general":
            statement += "Designed for both art enthusiasts and newcomers to the field, this exhibition offers multiple levels of engagement through carefully selected artworks, interpretive materials, and interactive elements."
        elif brief.target_audience == "scholarly":
            statement += "This scholarly exhibition contributes new insights to art historical discourse through rigorous research, innovative display strategies, and critical examination of canonical narratives."
        else:
            statement += "This exhibition provides an accessible yet sophisticated exploration of artistic achievement, encouraging visitors to develop their own interpretive frameworks."

        return statement

    async def _generate_statement_with_llm(self, brief: CuratorBrief, validations: List[ConceptValidation], research: ThemeResearch) -> str:
        """Generate curatorial statement using OpenAI GPT-4"""

        # Build rich context for LLM
        concepts_str = ', '.join([v.refined_concept for v in validations[:5]])
        artists_str = ', '.join(brief.reference_artists[:5]) if brief.reference_artists else "various artists"

        prompt = f"""You are writing a curatorial statement for Museum Van Bommel Van Dam, a modern art museum in the Netherlands.

Museum Van Bommel Van Dam's Curatorial Philosophy:
- We champion modern and contemporary art that challenges conventional seeing
- We connect historical avant-garde movements to contemporary practice
- We believe abstract art reveals essential truths about form, color, and space
- We make intellectual content accessible without dumbing down
- We address both serious collectors and curious visitors
- Our voice is confident, direct, and passionate about modern art

Write a curatorial statement that embodies this philosophy.

Exhibition Details:
- Theme: {brief.theme_title}
- Key Concepts: {concepts_str}
- Featured Artists: {artists_str}
- Target Audience: {brief.target_audience}
- Duration: {brief.duration_weeks} weeks

Art Historical Context:
{research.art_historical_context}

Current Discourse:
{research.current_discourse[:200]}

Requirements:
1. Write 200-250 words in an engaging, direct voice
2. Start strong - capture attention immediately
3. Explain why THIS exhibition at THIS moment matters
4. Connect historical movements to contemporary relevance
5. Use "we" and "our" - speak as the museum
6. Avoid academic jargon while maintaining intellectual depth
7. No clichés like "invites viewers to explore" or "takes us on a journey"
8. End with what visitors will experience/discover
9. Think: This will be read by collectors, art students, and curious locals

Write the curatorial statement for Museum Van Bommel Van Dam:"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=400,
            temperature=0.5,  # Balanced creativity and precision
            messages=[{"role": "user", "content": prompt}]
        )

        statement = response.choices[0].message.content.strip()
        logger.info(f"LLM generated curatorial statement ({len(statement)} chars)")
        return statement

    async def _generate_scholarly_rationale(self, brief: CuratorBrief, research: ThemeResearch) -> str:
        """Generate scholarly rationale using LLM or templates"""

        # Try LLM-based generation first
        if self.openai_client:
            try:
                return await self._generate_rationale_with_llm(brief, research)
            except Exception as e:
                logger.warning(f"LLM rationale generation failed: {e}, falling back to templates")

        # Fallback to template-based generation
        return self._generate_rationale_with_templates(brief, research)

    def _generate_rationale_with_templates(self, brief: CuratorBrief, research: ThemeResearch) -> str:
        """Template-based scholarly rationale (fallback)"""
        rationale = f"The scholarly foundation for this exhibition rests upon {research.scholarly_background} "

        # Add methodological approach
        rationale += "The curatorial methodology emphasizes interdisciplinary analysis, drawing upon art history, cultural studies, and museum theory to create a comprehensive interpretive framework. "

        # Include research confidence
        if research.research_confidence > 0.7:
            rationale += "Extensive research in primary and secondary sources provides robust scholarly support for the exhibition's central arguments. "

        # Add contribution to field
        rationale += "This exhibition contributes to contemporary art historical discourse by offering new perspectives on familiar material while introducing lesser-known works that expand our understanding of the period and its cultural significance."

        return rationale

    async def _generate_rationale_with_llm(self, brief: CuratorBrief, research: ThemeResearch) -> str:
        """Generate scholarly rationale using OpenAI GPT-4"""

        prompt = f"""You are the chief curator at Museum Van Bommel Van Dam writing the scholarly rationale for an exhibition proposal. This document will be read by the museum board, potential lenders, and academic peers.

Museum Van Bommel Van Dam's Scholarly Positioning:
- We are a research-focused institution specializing in modern and contemporary art
- We have particular expertise in geometric abstraction, De Stijl, and Dutch modernism
- We contribute to international discourse on abstract art and its contemporary relevance
- We balance rigorous scholarship with public accessibility
- We are known for discovering overlooked connections between historical and contemporary practice

Write a scholarly rationale that positions this exhibition within our museum's mission and expertise.

Exhibition Theme: {brief.theme_title}

Art Historical Context:
{research.art_historical_context}

Scholarly Background:
{research.scholarly_background}

Key Developments:
{', '.join(research.key_developments[:5]) if research.key_developments else 'Various artistic developments'}

Geographical Scope: {research.geographical_scope}
Chronological Scope: {research.chronological_scope}

Requirements:
1. Write 150-200 words in scholarly but clear language
2. Begin by establishing the exhibition's art historical significance
3. Explain how this fits Museum Van Bommel Van Dam's collection strengths
4. Justify the curatorial approach and methodology
5. Mention potential loans or collection highlights we can leverage
6. Address how this contributes to scholarship on modern art
7. Reference recent developments in art historical discourse when relevant
8. End with the exhibition's unique contribution to the field
9. Write for an audience of museum professionals and art historians

Write the scholarly rationale:"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=350,
            temperature=0.3,  # More conservative for scholarly text
            messages=[{"role": "user", "content": prompt}]
        )

        rationale = response.choices[0].message.content.strip()
        logger.info(f"LLM generated scholarly rationale ({len(rationale)} chars)")
        return rationale

    async def _generate_comprehensive_exhibition_framework(
        self,
        brief: CuratorBrief,
        validations: List[ConceptValidation]
    ) -> Dict[str, Any]:
        """
        Generate complete exhibition framework in ONE LLM call
        Returns all new fields as structured JSON
        """
        if not self.openai_client:
            # Fallback to template-based generation
            return self._generate_framework_with_templates(brief, validations)

        concepts_str = ', '.join([v.refined_concept for v in validations[:5]])
        artists_str = ', '.join(brief.reference_artists[:5]) if brief.reference_artists else "various artists"

        prompt = f"""You are the chief curator at Museum Van Bommel Van Dam designing a complete exhibition framework.

Museum Van Bommel Van Dam Identity:
- Leading modern art museum in the Netherlands
- Specializes in abstract art, geometric abstraction, conceptualism
- Known for: Making modern art accessible while maintaining scholarly rigor
- Voice: Direct, intellectually engaging, passionate about modern art
- Audience: Collectors, students, art enthusiasts, curious locals

Design a COMPLETE exhibition framework as JSON.

Exhibition Brief:
- Title: {brief.theme_title}
- Description: {brief.theme_description}
- Key Concepts: {concepts_str}
- Reference Artists: {artists_str}
- Target Audience: {brief.target_audience}
- Duration: {brief.duration_weeks} weeks

Return JSON with this EXACT structure:
{{
  "exhibition_title": "Compelling, contemporary title (max 50 chars)",
  "subtitle": "Clarifying subtitle or null",
  "central_argument": "One sentence thesis - why this exhibition matters",
  "curatorial_statement": "250-300 words explaining the exhibition's vision and approach",
  "scholarly_rationale": "150-200 words on art historical significance",
  "exhibition_sections": [
    {{
      "title": "Section 1 Title",
      "focus": "What this section explores",
      "artist_emphasis": ["Artist name hints if relevant"],
      "estimated_artwork_count": 8
    }},
    {{
      "title": "Section 2 Title",
      "focus": "What this section explores",
      "artist_emphasis": [],
      "estimated_artwork_count": 10
    }},
    {{
      "title": "Section 3 Title",
      "focus": "What this section explores",
      "artist_emphasis": [],
      "estimated_artwork_count": 8
    }}
  ],
  "opening_wall_text": "First text visitors read (MAX 50 words)",
  "key_questions": [
    "Question 1 the exhibition explores?",
    "Question 2 about the theme?",
    "Question 3 for visitors to consider?"
  ],
  "contemporary_relevance": "Why this exhibition matters NOW (100-150 words)",
  "visitor_takeaway": "What visitors should remember after leaving",
  "wall_text_strategy": "Tone and approach for labels (e.g., 'Direct and accessible, avoiding jargon')",
  "educational_angles": [
    "Tour theme 1",
    "Workshop idea 2",
    "Educational program 3"
  ]
}}

Requirements:
1. Create 3-5 exhibition sections that build a narrative arc
2. Exhibition title must feel contemporary, not academic
3. Central argument must be ONE powerful sentence
4. Opening wall text MUST be under 50 words
5. Sections should have clear focus and flow logically
6. Contemporary relevance must connect historical art to today
7. Educational angles should be specific and actionable
8. Use Van Bommel Van Dam's voice: confident, direct, passionate

Return ONLY valid JSON, no markdown formatting."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=2000,
                temperature=0.6,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}]
            )

            framework_json = response.choices[0].message.content.strip()
            framework = json.loads(framework_json)

            logger.info(f"LLM generated comprehensive exhibition framework")
            return framework

        except Exception as e:
            logger.error(f"LLM framework generation failed: {e}")
            return self._generate_framework_with_templates(brief, validations)

    def _generate_framework_with_templates(
        self,
        brief: CuratorBrief,
        validations: List[ConceptValidation]
    ) -> Dict[str, Any]:
        """Template-based framework generation (fallback)"""
        primary_concepts = [v.refined_concept for v in validations if v.confidence_score > 0.7]
        if not primary_concepts:
            primary_concepts = [v.refined_concept for v in validations[:2]]

        return {
            "exhibition_title": brief.theme_title,
            "subtitle": "An Exploration of Artistic Innovation",
            "central_argument": f"This exhibition examines how {', '.join(primary_concepts[:2])} transformed artistic practice.",
            "curatorial_statement": f"This exhibition presents a comprehensive examination of {brief.theme_title.lower()}, exploring how artistic innovation emerges from tradition and experimentation.",
            "scholarly_rationale": "This exhibition contributes to art historical discourse through rigorous research and innovative display strategies.",
            "exhibition_sections": [
                {
                    "title": "Origins and Context",
                    "focus": "Historical foundations and early developments",
                    "artist_emphasis": brief.reference_artists[:2] if brief.reference_artists else [],
                    "estimated_artwork_count": 8
                },
                {
                    "title": "Innovation and Expression",
                    "focus": "Key artistic innovations and breakthroughs",
                    "artist_emphasis": brief.reference_artists[2:4] if len(brief.reference_artists) > 2 else [],
                    "estimated_artwork_count": 12
                },
                {
                    "title": "Legacy and Influence",
                    "focus": "Contemporary resonance and ongoing impact",
                    "artist_emphasis": [],
                    "estimated_artwork_count": 8
                }
            ],
            "opening_wall_text": f"This exhibition explores {brief.theme_title.lower()}, revealing how artists transformed their vision into groundbreaking work.",
            "key_questions": [
                f"How did {primary_concepts[0] if primary_concepts else 'artistic innovation'} challenge traditional approaches?",
                "What makes these works significant today?",
                "How do individual artistic voices contribute to broader movements?"
            ],
            "contemporary_relevance": f"In an era of rapid change, this exhibition offers insights into how artists navigate tradition and innovation, making it highly relevant to contemporary cultural discourse.",
            "visitor_takeaway": "A deeper understanding of how artistic innovation shapes culture.",
            "wall_text_strategy": "Direct and accessible language that respects visitors' intelligence while avoiding academic jargon",
            "educational_angles": [
                "Guided tours focusing on artistic techniques",
                "Workshops on artistic interpretation",
                "Lectures connecting historical and contemporary practice"
            ]
        }

    def _analyze_theme_focus(self, validations: List[ConceptValidation]) -> Tuple[str, List[str]]:
        """Analyze theme to determine primary focus and secondary themes"""

        if not validations:
            return "artistic innovation", ["cultural context", "historical significance"]

        # Sort by confidence score
        sorted_validations = sorted(validations, key=lambda x: x.confidence_score, reverse=True)

        # Primary focus is highest confidence concept
        primary_focus = sorted_validations[0].refined_concept

        # Secondary themes are remaining high-confidence concepts
        secondary_themes = [v.refined_concept for v in sorted_validations[1:4] if v.confidence_score > 0.5]

        # Add generic themes if we don't have enough
        if len(secondary_themes) < 2:
            generic_themes = ["artistic technique", "cultural context", "historical significance", "aesthetic innovation"]
            for theme in generic_themes:
                if theme not in secondary_themes and len(secondary_themes) < 3:
                    secondary_themes.append(theme)

        return primary_focus, secondary_themes

    def _determine_complexity(self, brief: CuratorBrief, validations: List[ConceptValidation], research: ThemeResearch) -> str:
        """Determine exhibition complexity level"""

        complexity_score = 0

        # Check concept validation success
        high_confidence_concepts = sum(1 for v in validations if v.confidence_score > 0.7)
        if high_confidence_concepts >= 3:
            complexity_score += 1

        # Check research depth
        if research.research_confidence > 0.7:
            complexity_score += 1

        # Check target audience
        if brief.target_audience == "academic":
            complexity_score += 2
        elif brief.target_audience == "specialists":
            complexity_score += 1

        # Check number of artists
        if brief.reference_artists and len(brief.reference_artists) > 5:
            complexity_score += 1

        # Check international scope
        if brief.include_international:
            complexity_score += 1

        if complexity_score >= 4:
            return "scholarly"
        elif complexity_score >= 2:
            return "intermediate"
        else:
            return "accessible"

    def _generate_space_recommendations(self, brief: CuratorBrief, validations: List[ConceptValidation]) -> List[str]:
        """Generate space and installation recommendations"""

        recommendations = []

        # Based on space type
        if brief.space_type == "main":
            recommendations.append("Utilize main gallery spaces for maximum impact and visitor flow")
        elif brief.space_type == "contemporary":
            recommendations.append("Leverage contemporary gallery features for modern display techniques")

        # Based on concepts
        valid_concepts = [v.refined_concept.lower() for v in validations if v.confidence_score > 0.5]

        if any('light' in concept or 'impression' in concept for concept in valid_concepts):
            recommendations.append("Natural lighting considerations essential for Impressionist works")
            recommendations.append("Flexible lighting systems to demonstrate time-of-day effects")

        if any('sculpture' in concept for concept in valid_concepts):
            recommendations.append("Central floor space required for three-dimensional works")
            recommendations.append("Multiple viewing angles and circulation paths")

        if any('drawing' in concept or 'print' in concept for concept in valid_concepts):
            recommendations.append("Controlled lighting levels to protect light-sensitive works")
            recommendations.append("Intimate viewing spaces for detailed examination")

        # Default recommendations
        if not recommendations:
            recommendations = [
                "Flexible wall systems for various artwork sizes",
                "Climate-controlled environment for artwork preservation",
                "Clear sight lines and accessible pathways"
            ]

        return recommendations[:5]  # Limit to 5 recommendations

    def _refine_target_audience(self, brief: CuratorBrief, complexity_level: str) -> str:
        """Refine target audience based on complexity analysis"""

        if complexity_level == "scholarly":
            return "Academic researchers, graduate students, museum professionals, and serious art enthusiasts"
        elif complexity_level == "intermediate":
            return "Art-interested public, undergraduate students, cultural tourists, and lifelong learners"
        else:
            return "General public, families, school groups, and newcomers to art appreciation"

    def _estimate_duration(self, brief: CuratorBrief) -> str:
        """Estimate recommended exhibition duration"""

        if brief.duration_weeks:
            if brief.duration_weeks >= 20:
                return "Long-term exhibition (5-6 months) suitable for comprehensive treatment"
            elif brief.duration_weeks >= 12:
                return "Standard exhibition duration (3-4 months) for thorough exploration"
            elif brief.duration_weeks >= 8:
                return "Focused exhibition (2-3 months) for concentrated themes"
            else:
                return "Short-term exhibition (6-8 weeks) for targeted presentations"

        # Default estimation based on complexity
        return "Standard exhibition duration (3-4 months) recommended for comprehensive treatment"

    def _determine_chronological_scope(self, validations: List[ConceptValidation], sources: List[Dict]) -> str:
        """Determine chronological scope from research"""

        # Look for time period indicators in research
        time_indicators = []
        for source in sources:
            extract = source.get('extract', '').lower()
            if 'century' in extract:
                # Extract century references
                import re
                centuries = re.findall(r'\d+th century', extract)
                time_indicators.extend(centuries)

        # Look for specific periods in concept names
        for validation in validations:
            concept = validation.refined_concept.lower()
            if 'renaissance' in concept:
                time_indicators.append('15th-16th century')
            elif 'baroque' in concept:
                time_indicators.append('17th-18th century')
            elif 'impression' in concept:
                time_indicators.append('19th century')
            elif 'modern' in concept:
                time_indicators.append('20th century')
            elif 'contemporary' in concept:
                time_indicators.append('21st century')

        if time_indicators:
            return f"Primarily {time_indicators[0]}, with broader historical context"
        else:
            return "Historical to contemporary, emphasizing artistic continuity"

    def _determine_geographical_scope(self, brief: CuratorBrief, validations: List[ConceptValidation]) -> str:
        """Determine geographical scope"""

        if brief.include_international:
            return "International scope with emphasis on cross-cultural artistic exchange"

        # Check for regional indicators in concepts
        for validation in validations:
            concept = validation.refined_concept.lower()
            if 'french' in concept or 'paris' in concept:
                return "Primarily French, with European context"
            elif 'italian' in concept or 'florence' in concept:
                return "Primarily Italian, with Mediterranean context"
            elif 'dutch' in concept or 'netherlands' in concept:
                return "Primarily Dutch, with Northern European context"
            elif 'american' in concept:
                return "Primarily American, with transatlantic connections"

        return "Regional focus with international comparative perspectives"

    def _calculate_research_confidence(self, sources: List[Dict], validations: List[ConceptValidation]) -> float:
        """Calculate confidence in research backing"""

        # Base score from concept validations
        if validations:
            avg_concept_confidence = sum(v.confidence_score for v in validations) / len(validations)
        else:
            avg_concept_confidence = 0.3

        # Boost from research sources
        source_boost = min(len(sources) * 0.1, 0.3)  # Up to 0.3 boost from sources

        # Quality boost from high-value sources
        quality_boost = 0
        for source in sources:
            if source.get('relevance') == 'primary':
                quality_boost += 0.05

        total_confidence = min(avg_concept_confidence + source_boost + quality_boost, 1.0)
        return round(total_confidence, 2)

    def _calculate_refinement_confidence(self, validations: List[ConceptValidation], research: ThemeResearch) -> float:
        """Calculate overall confidence in theme refinement"""

        # Concept validation confidence (60% weight)
        if validations:
            concept_confidence = sum(v.confidence_score for v in validations) / len(validations)
        else:
            concept_confidence = 0.3

        # Research confidence (40% weight)
        research_confidence = research.research_confidence

        # Calculate weighted average
        overall_confidence = (concept_confidence * 0.6) + (research_confidence * 0.4)

        return round(overall_confidence, 2)