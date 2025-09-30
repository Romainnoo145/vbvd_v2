"""
Artist Discovery Agent - Stage 2 of AI Curator Pipeline
Discovers and ranks artists based on exhibition theme using multiple authoritative sources
"""

import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import os

# Optional dependency - gracefully handle if not installed
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

from backend.clients.essential_data_client import EssentialDataClient
from backend.models import DiscoveredArtist
from backend.agents.theme_refinement_agent import RefinedTheme, ConceptValidation

logger = logging.getLogger(__name__)


# Known art movements mapping for fallback queries
MOVEMENT_CACHE = {
    # Major Western movements
    'impressionism': 'wd:Q40415',
    'impressionist': 'wd:Q40415',
    'post-impressionism': 'wd:Q35637',
    'expressionism': 'wd:Q40415',
    'abstract expressionism': 'wd:Q11374',
    'cubism': 'wd:Q38166',
    'surrealism': 'wd:Q39427',
    'dadaism': 'wd:Q6027',
    'futurism': 'wd:Q40415',
    'baroque': 'wd:Q37853',
    'renaissance': 'wd:Q4692',
    'rococo': 'wd:Q122960',
    'romanticism': 'wd:Q37068',
    'realism': 'wd:Q40415',
    'neoclassicism': 'wd:Q14378',
    'mannerism': 'wd:Q131808',
    'minimalism': 'wd:Q165547',
    'pop art': 'wd:Q134147',
    'abstract art': 'wd:Q162728',
    'contemporary art': 'wd:Q162728',  # Broad contemporary

    # Historical periods
    'dutch golden age': 'wd:Q1855606',  # Dutch Golden Age painting
    'italian renaissance': 'wd:Q1474884',
    'northern renaissance': 'wd:Q1474770',
    'medieval': 'wd:Q721206',

    # Genres
    'portrait': 'wd:Q134307',  # Portrait painting
    'landscape': 'wd:Q191163',  # Landscape art
    'still life': 'wd:Q170593',
    'genre painting': 'wd:Q1047337',
    'history painting': 'wd:Q742333',
}


class ArtistSearchQuery(BaseModel):
    """SPARQL query for artist discovery"""
    query_type: str  # "wikidata", "getty_ulan", "yale_lux"
    sparql: str
    concept_uri: Optional[str] = None
    concept_label: str


class ArtistDiscoveryAgent:
    """
    Stage 2 Agent: Discover artists relevant to exhibition theme

    Workflow:
    1. Take validated theme from Stage 1 with Getty AAT URIs
    2. Use Wikidata SPARQL to find artists connected to theme concepts
    3. Use Getty ULAN SPARQL to validate and enrich artist data
    4. Query Yale LUX for additional artist information
    5. Score artist relevance using LLM analysis
    6. Provide detailed reasoning for each artist's relevance
    7. Output: Ranked list of DiscoveredArtist objects
    """

    def __init__(self, data_client: EssentialDataClient, anthropic_api_key: Optional[str] = None):
        self.data_client = data_client
        self.agent_version = "1.0"

        # Initialize Anthropic client for LLM-based relevance scoring
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic SDK not installed - using heuristic scoring only")
            self.anthropic_client = None
        else:
            api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning("No Anthropic API key provided - LLM scoring will be limited")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key) if api_key else None

    async def discover_artists(
        self,
        refined_theme: RefinedTheme,
        session_id: str,
        max_artists: int = 20,
        min_relevance: float = 0.5,
        prioritize_diversity: bool = True,
        diversity_targets: Optional[Dict[str, int]] = None
    ) -> List[DiscoveredArtist]:
        """
        Discover artists relevant to the exhibition theme

        Args:
            refined_theme: Output from Stage 1 (Theme Refinement)
            session_id: Session identifier
            max_artists: Maximum number of artists to return
            min_relevance: Minimum relevance score threshold

        Returns:
            List of DiscoveredArtist objects ranked by relevance
        """
        logger.info(f"Starting artist discovery for session {session_id}")
        start_time = datetime.utcnow()

        # Step 1: Try Yale LUX first (faster and more reliable)
        raw_artist_data = []
        logger.info("Attempting Yale LUX artist discovery first")
        lux_artists = await self._discover_artists_from_yale_lux(refined_theme)
        if lux_artists:
            logger.info(f"Found {len(lux_artists)} artists via Yale LUX")
            raw_artist_data.extend(lux_artists)

        # Step 1b: If we have reference artists, find related artists (HIGH RELEVANCE)
        related_artists_data = []
        if hasattr(refined_theme, 'reference_artists') and refined_theme.reference_artists:
            logger.info(f"Discovering related artists for {len(refined_theme.reference_artists)} reference artists")
            related_artists_data = await self._discover_related_artists(refined_theme.reference_artists)
            if related_artists_data:
                for artist in related_artists_data:
                    artist['from_reference'] = True  # Mark for relevance boost
                raw_artist_data.extend(related_artists_data)

        # Step 2: Only use Wikidata if we don't have enough artists yet
        if len(raw_artist_data) < max_artists * 3:  # Need 3x for filtering
            logger.info(f"Supplementing with Wikidata queries ({len(raw_artist_data)} artists so far)")
            artist_queries = self._build_artist_queries(refined_theme.validated_concepts)
            wikidata_artists = await self._execute_artist_searches(artist_queries)
            raw_artist_data.extend(wikidata_artists)

        # Step 3: Deduplicate and merge artist records
        merged_artists = self._merge_artist_records(raw_artist_data)

        # Step 4: Enrich artists with Getty ULAN data
        enriched_artists = await self._enrich_with_getty_ulan(merged_artists)

        # Step 5: Get biographical data from Wikipedia via Wikidata
        biographical_artists = await self._enrich_with_biographical_data(enriched_artists)

        # Step 6: Query Yale LUX for institutional connections
        lux_enriched_artists = await self._enrich_with_yale_lux(biographical_artists)

        # Step 7: Calculate relevance scores using LLM
        scored_artists = await self._score_artist_relevance(
            lux_enriched_artists,
            refined_theme
        )

        # Step 8: Filter and rank artists
        filtered_artists = [
            artist for artist in scored_artists
            if artist.relevance_score >= min_relevance
        ]

        # Step 9: Apply diversity scoring and rerank if requested
        if prioritize_diversity:
            ranked_artists = self._rerank_for_diversity(
                filtered_artists,
                max_artists,
                diversity_targets or {}
            )
        else:
            # Sort by relevance score only (descending)
            ranked_artists = sorted(
                filtered_artists,
                key=lambda x: x.relevance_score,
                reverse=True
            )[:max_artists]

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Artist discovery completed in {processing_time:.2f}s - "
            f"Found {len(ranked_artists)} artists (from {len(merged_artists)} candidates)"
        )

        return ranked_artists

    def _build_artist_queries(self, concepts: List[ConceptValidation]) -> List[ArtistSearchQuery]:
        """Build SPARQL queries for artist discovery based on validated concepts"""
        queries = []

        for concept in concepts:
            concept_lower = concept.refined_concept.lower()

            # OPTION 1: Check if concept matches known movement (FAST & RELIABLE)
            if concept_lower in MOVEMENT_CACHE:
                logger.info(f"Using movement-based query for '{concept.refined_concept}'")
                wikidata_query = self._build_wikidata_movement_query(
                    concept.refined_concept,
                    MOVEMENT_CACHE[concept_lower]
                )
                queries.append(ArtistSearchQuery(
                    query_type="wikidata",
                    sparql=wikidata_query,
                    concept_uri=MOVEMENT_CACHE[concept_lower],
                    concept_label=concept.refined_concept
                ))
                continue

            # OPTION 2: High confidence with Getty URI (PRECISE)
            if concept.confidence_score >= 0.7 and concept.getty_aat_uri:
                logger.info(f"Using concept-based query for '{concept.refined_concept}' (high confidence)")
                wikidata_query = self._build_wikidata_concept_artist_query(
                    concept.refined_concept,
                    concept.getty_aat_uri
                )
                queries.append(ArtistSearchQuery(
                    query_type="wikidata",
                    sparql=wikidata_query,
                    concept_uri=concept.getty_aat_uri,
                    concept_label=concept.refined_concept
                ))
                continue

            # OPTION 3: Medium confidence - broader keyword search (RECALL)
            if concept.confidence_score >= 0.4:
                logger.info(f"Using broad keyword query for '{concept.refined_concept}' (medium confidence)")
                wikidata_query = self._build_wikidata_broad_keyword_query(
                    concept.refined_concept
                )
                queries.append(ArtistSearchQuery(
                    query_type="wikidata",
                    sparql=wikidata_query,
                    concept_uri=None,
                    concept_label=concept.refined_concept
                ))
                continue

            # OPTION 4: Low confidence - skip
            logger.debug(f"Skipping '{concept.refined_concept}' - confidence too low ({concept.confidence_score})")

        logger.info(f"Built {len(queries)} artist discovery queries")
        return queries

    def _build_wikidata_concept_artist_query(self, concept_label: str, getty_uri: str) -> str:
        """
        Build comprehensive Wikidata SPARQL query to find artists associated with a concept

        This query finds artists who:
        - Worked in art movements related to the concept
        - Created works of the specified type/genre
        - Are associated with the thematic concept
        """
        # Extract Getty AAT ID from URI
        getty_id = getty_uri.split('/')[-1] if getty_uri else ""

        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>

        SELECT DISTINCT ?artist ?artistLabel ?description
               ?birth ?death ?nationality ?nationalityLabel
               ?movement ?movementLabel ?image
               ?birthPlace ?birthPlaceLabel
               ?gender ?genderLabel
               ?ethnicGroup ?ethnicGroupLabel
        WHERE {{
          # Find artists (painters, sculptors, etc.)
          ?artist wdt:P106/wdt:P279* wd:Q483501 .  # Occupation: artist

          # Connect to concept via multiple paths
          {{
            # Path 1: Artist associated with art movement related to concept
            ?artist wdt:P135 ?movement .
            ?movement rdfs:label ?movementName .
            FILTER(CONTAINS(LCASE(?movementName), "{concept_label.lower()}"))
          }} UNION {{
            # Path 2: Artist created works of this genre/type
            ?artist wdt:P136 ?genre .
            ?genre rdfs:label ?genreName .
            FILTER(CONTAINS(LCASE(?genreName), "{concept_label.lower()}"))
          }} UNION {{
            # Path 3: Artist's work has subjects related to concept
            ?work wdt:P170 ?artist ;  # Creator
                  wdt:P921 ?subject .  # Main subject
            ?subject rdfs:label ?subjectName .
            FILTER(CONTAINS(LCASE(?subjectName), "{concept_label.lower()}"))
          }} UNION {{
            # Path 4: Direct text match in artist description
            ?artist schema:description ?desc .
            FILTER(CONTAINS(LCASE(?desc), "{concept_label.lower()}"))
          }}

          # Get biographical data
          OPTIONAL {{ ?artist wdt:P569 ?birth }}      # Date of birth
          OPTIONAL {{ ?artist wdt:P570 ?death }}      # Date of death
          OPTIONAL {{ ?artist wdt:P27 ?nationality }} # Country of citizenship
          OPTIONAL {{ ?artist wdt:P18 ?image }}       # Image
          OPTIONAL {{ ?artist wdt:P19 ?birthPlace }}  # Place of birth
          OPTIONAL {{ ?artist wdt:P21 ?gender }}      # Gender
          OPTIONAL {{ ?artist wdt:P172 ?ethnicGroup }} # Ethnic group
          OPTIONAL {{ ?artist schema:description ?description FILTER(LANG(?description) = "en") }}

          # Labels
          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
          }}
        }}
        LIMIT 50
        """

    def _build_wikidata_movement_query(self, movement_label: str, movement_qid: str) -> str:
        """
        Build movement-based query (FAST & HIGH RECALL)
        Gets ALL artists associated with a known movement
        """
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT DISTINCT ?artist ?artistLabel ?description
               ?birth ?death ?nationality ?nationalityLabel
               ?movement ?movementLabel ?image ?birthPlace ?birthPlaceLabel
               ?gender ?genderLabel ?ethnicGroup ?ethnicGroupLabel
        WHERE {{
          # Artist with this movement
          ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter
          ?artist wdt:P135 {movement_qid} .  # Movement

          OPTIONAL {{ ?artist wdt:P569 ?birth }}
          OPTIONAL {{ ?artist wdt:P570 ?death }}
          OPTIONAL {{ ?artist wdt:P27 ?nationality }}
          OPTIONAL {{ ?artist wdt:P135 ?movement }}
          OPTIONAL {{ ?artist wdt:P18 ?image }}
          OPTIONAL {{ ?artist wdt:P19 ?birthPlace }}
          OPTIONAL {{ ?artist wdt:P21 ?gender }}
          OPTIONAL {{ ?artist wdt:P172 ?ethnicGroup }}
          OPTIONAL {{ ?artist schema:description ?description FILTER(LANG(?description) = "en") }}

          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
          }}
        }}
        LIMIT 100
        """

    def _build_wikidata_broad_keyword_query(self, keyword: str) -> str:
        """
        Build broad keyword query (HIGH RECALL, lower precision)
        Searches in artist descriptions and labels
        """
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>

        SELECT DISTINCT ?artist ?artistLabel ?description
               ?birth ?death ?nationality ?nationalityLabel
               ?movement ?movementLabel ?image ?birthPlace ?birthPlaceLabel
               ?gender ?genderLabel ?ethnicGroup ?ethnicGroupLabel
        WHERE {{
          ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter

          # Broad text search
          {{
            ?artist rdfs:label ?label .
            FILTER(CONTAINS(LCASE(?label), "{keyword.lower()}"))
          }} UNION {{
            ?artist schema:description ?desc .
            FILTER(CONTAINS(LCASE(?desc), "{keyword.lower()}"))
          }} UNION {{
            ?artist wdt:P136 ?genre .
            ?genre rdfs:label ?genreLabel .
            FILTER(CONTAINS(LCASE(?genreLabel), "{keyword.lower()}"))
          }}

          OPTIONAL {{ ?artist wdt:P569 ?birth }}
          OPTIONAL {{ ?artist wdt:P570 ?death }}
          OPTIONAL {{ ?artist wdt:P27 ?nationality }}
          OPTIONAL {{ ?artist wdt:P135 ?movement }}
          OPTIONAL {{ ?artist wdt:P18 ?image }}
          OPTIONAL {{ ?artist wdt:P19 ?birthPlace }}
          OPTIONAL {{ ?artist wdt:P21 ?gender }}
          OPTIONAL {{ ?artist wdt:P172 ?ethnicGroup }}
          OPTIONAL {{ ?artist schema:description ?description FILTER(LANG(?description) = "en") }}

          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
          }}
        }}
        LIMIT 50
        """

    def _build_wikidata_text_artist_query(self, concept_label: str) -> str:
        """Simplified artist query using direct property search"""
        # Map concept to Wikidata movement/genre QID where possible
        movement_mapping = {
            'geometric abstraction': 'Q1661415',  # Geometric abstraction
            'color field painting': 'Q1124724',   # Color field
            'minimalism': 'Q173782',              # Minimalism
            'de stijl': 'Q47116',                 # De Stijl
            'concrete art': 'Q1124724',           # Concrete art (use color field as proxy)
            'monochrome painting': 'Q173782',     # Use minimalism as proxy
            'abstract art': 'Q162729',            # Abstract art
            'abstract expressionism': 'Q131808',   # Abstract expressionism
        }

        movement_qid = movement_mapping.get(concept_label.lower())

        if movement_qid:
            # Use direct movement query (much faster)
            return f"""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>

            SELECT DISTINCT ?artist ?artistLabel ?description
                   ?birth ?death ?nationality ?nationalityLabel
                   ?movement ?movementLabel ?image ?birthPlace ?birthPlaceLabel
                   ?gender ?genderLabel ?ethnicGroup ?ethnicGroupLabel
            WHERE {{
              ?artist wdt:P135 wd:{movement_qid} .  # Movement
              ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter (more specific)

              OPTIONAL {{ ?artist wdt:P569 ?birth }}
              OPTIONAL {{ ?artist wdt:P570 ?death }}
              OPTIONAL {{ ?artist wdt:P27 ?nationality }}
              OPTIONAL {{ ?artist wdt:P135 ?movement }}
              OPTIONAL {{ ?artist wdt:P18 ?image }}
              OPTIONAL {{ ?artist wdt:P19 ?birthPlace }}
              OPTIONAL {{ ?artist wdt:P21 ?gender }}
              OPTIONAL {{ ?artist wdt:P172 ?ethnicGroup }}
              OPTIONAL {{ ?artist schema:description ?description FILTER(LANG(?description) = "en") }}

              SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
              }}
            }}
            LIMIT 25
            """
        else:
            # Very simple fallback - just query by occupation
            return f"""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>

            SELECT DISTINCT ?artist ?artistLabel ?description
                   ?birth ?death ?nationality ?nationalityLabel
                   ?movement ?movementLabel ?image
            WHERE {{
              ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter
              ?artist wdt:P135 ?movement .     # Has movement

              OPTIONAL {{ ?artist wdt:P569 ?birth }}
              OPTIONAL {{ ?artist wdt:P570 ?death }}
              OPTIONAL {{ ?artist wdt:P27 ?nationality }}
              OPTIONAL {{ ?artist wdt:P18 ?image }}
              OPTIONAL {{ ?artist schema:description ?description FILTER(LANG(?description) = "en") }}

              SERVICE wikibase:label {{
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
              }}
            }}
            LIMIT 20
            """

    async def _execute_artist_searches(self, queries: List[ArtistSearchQuery]) -> List[Dict[str, Any]]:
        """Execute SPARQL queries sequentially with delays to avoid rate limiting"""
        logger.info(f"Executing {len(queries)} artist search queries sequentially")

        all_artists = []

        for i, query in enumerate(queries):
            if query.query_type == "wikidata":
                try:
                    logger.info(f"Executing query {i+1}/{len(queries)}: {query.concept_label}")
                    result = await self._execute_wikidata_query(query)

                    if isinstance(result, list):
                        all_artists.extend(result)
                        logger.info(f"Query {i+1} returned {len(result)} artists")

                    # Add delay between queries to avoid rate limiting (Wikidata requires this)
                    if i < len(queries) - 1:
                        await asyncio.sleep(2.0)  # 2 second delay between queries

                except Exception as e:
                    logger.error(f"Query {i+1} failed: {e}")
                    continue

        logger.info(f"Retrieved {len(all_artists)} raw artist records")
        return all_artists

    async def _execute_wikidata_query(self, query: ArtistSearchQuery) -> List[Dict[str, Any]]:
        """Execute a single Wikidata SPARQL query"""
        try:
            sparql_url = "https://query.wikidata.org/sparql"
            headers = {
                'Accept': 'application/sparql-results+json',
                'User-Agent': 'AI-Curator-Assistant/1.0 (Educational Project)'
            }

            # Use a dedicated client for SPARQL queries with longer timeout
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    sparql_url,
                    data={'query': query.sparql, 'format': 'json'},
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    artists = []

                    for binding in data.get('results', {}).get('bindings', []):
                        artist_data = {
                            'source': 'wikidata',
                            'concept_label': query.concept_label,
                            'concept_uri': query.concept_uri,
                            'wikidata_uri': binding.get('artist', {}).get('value', ''),
                            'wikidata_id': binding.get('artist', {}).get('value', '').split('/')[-1],
                            'name': binding.get('artistLabel', {}).get('value', ''),
                            'description': binding.get('description', {}).get('value', ''),
                        }

                        # Parse biographical data
                        if 'birth' in binding:
                            birth_str = binding['birth']['value']
                            try:
                                artist_data['birth_year'] = int(birth_str[:4])
                            except:
                                pass

                        if 'death' in binding:
                            death_str = binding['death']['value']
                            try:
                                artist_data['death_year'] = int(death_str[:4])
                            except:
                                pass

                        if 'nationalityLabel' in binding:
                            artist_data['nationality'] = binding['nationalityLabel']['value']

                        if 'birthPlaceLabel' in binding:
                            artist_data['birth_place'] = binding['birthPlaceLabel']['value']

                        if 'movementLabel' in binding:
                            artist_data['movements'] = [binding['movementLabel']['value']]

                        if 'image' in binding:
                            artist_data['image_url'] = binding['image']['value']

                        # Diversity data
                        if 'genderLabel' in binding:
                            artist_data['gender'] = binding['genderLabel']['value']

                        if 'ethnicGroupLabel' in binding:
                            artist_data['ethnic_group'] = binding['ethnicGroupLabel']['value']

                        artists.append(artist_data)

                    return artists
                else:
                    logger.error(f"Wikidata query failed with status {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error executing Wikidata query: {e}", exc_info=True)
            return []

    def _merge_artist_records(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate and merge artist records from different sources
        Uses fuzzy matching on names and exact matching on IDs
        """
        merged = {}

        for artist in raw_data:
            # Create unique key based on Wikidata ID or normalized name
            key = None
            if artist.get('wikidata_id'):
                key = f"wd:{artist['wikidata_id']}"
            elif artist.get('getty_ulan_id'):
                key = f"getty:{artist['getty_ulan_id']}"
            else:
                # Fallback to normalized name
                name = artist.get('name', '').strip().lower()
                if name:
                    key = f"name:{name}"

            if not key:
                continue

            if key in merged:
                # Merge with existing record
                existing = merged[key]

                # Merge movements
                if 'movements' in artist:
                    existing_movements = existing.get('movements', [])
                    existing['movements'] = list(set(existing_movements + artist['movements']))

                # Add discovery sources
                existing_sources = existing.get('discovery_sources', [])
                if artist.get('source'):
                    existing['discovery_sources'] = list(set(existing_sources + [artist['source']]))

                # Prefer non-empty values
                for field in ['description', 'nationality', 'birth_place', 'image_url']:
                    if field in artist and artist[field] and not existing.get(field):
                        existing[field] = artist[field]
            else:
                # New artist
                artist['discovery_sources'] = [artist.get('source', 'unknown')]
                merged[key] = artist

        logger.info(f"Merged {len(raw_data)} records into {len(merged)} unique artists")
        return list(merged.values())

    async def _enrich_with_getty_ulan(self, artists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich artist data with Getty ULAN authority records"""
        logger.debug(f"Enriching {len(artists)} artists with Getty ULAN data")

        enriched = []
        for artist in artists:
            try:
                # Search Getty ULAN for this artist
                getty_results = await self.data_client._search_getty(
                    artist['name'],
                    "artist person"
                )

                if getty_results and len(getty_results) > 0:
                    best_match = getty_results[0]

                    # Add Getty ULAN identifiers
                    artist['getty_ulan_uri'] = best_match.get('uri', '')
                    artist['getty_ulan_id'] = best_match.get('getty_id', '')

                    # Add scope note if available
                    if best_match.get('scope_note'):
                        artist['getty_scope_note'] = best_match['scope_note']

                    # Add to discovery sources
                    if 'discovery_sources' not in artist:
                        artist['discovery_sources'] = []
                    if 'getty' not in artist['discovery_sources']:
                        artist['discovery_sources'].append('getty')

                enriched.append(artist)

            except Exception as e:
                logger.warning(f"Failed to enrich artist '{artist['name']}' with Getty ULAN: {e}")
                enriched.append(artist)

        return enriched

    async def _enrich_with_biographical_data(self, artists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich with detailed biographical data from Wikipedia"""
        logger.debug(f"Enriching {len(artists)} artists with biographical data")

        enriched = []
        for artist in artists:
            try:
                # Search Wikipedia for biographical information
                wiki_results = await self.data_client._search_wikipedia(
                    artist['name'],
                    "artist biography"
                )

                if wiki_results and len(wiki_results) > 0:
                    bio = wiki_results[0]

                    # Add biographical summaries
                    if bio.get('summary'):
                        artist['biography_short'] = bio['summary'][:500]
                        artist['biography_long'] = bio['summary'][:5000]

                    # Add Wikipedia URL
                    if bio.get('url'):
                        artist['wikipedia_url'] = bio['url']

                    # Add to discovery sources
                    if 'discovery_sources' not in artist:
                        artist['discovery_sources'] = []
                    if 'wikipedia' not in artist['discovery_sources']:
                        artist['discovery_sources'].append('wikipedia')

                enriched.append(artist)

            except Exception as e:
                logger.warning(f"Failed to enrich artist '{artist['name']}' with biographical data: {e}")
                enriched.append(artist)

        return enriched

    async def _enrich_with_yale_lux(self, artists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich with institutional connections from Yale LUX"""
        logger.debug(f"Enriching {len(artists)} artists with Yale LUX data")

        enriched = []
        for artist in artists:
            try:
                # Search Yale LUX for this artist
                lux_results = await self.data_client._search_yale_lux(
                    artist['name'],
                    "artist person"
                )

                if lux_results and len(lux_results) > 0:
                    # Count known works
                    artist['known_works_count'] = len(lux_results)

                    # Extract institutional connections
                    institutions = set()
                    for result in lux_results:
                        if result.get('location'):
                            institutions.add(result['location'])

                    artist['institutional_connections'] = list(institutions)[:10]

                    # Add to discovery sources
                    if 'discovery_sources' not in artist:
                        artist['discovery_sources'] = []
                    if 'yale_lux' not in artist['discovery_sources']:
                        artist['discovery_sources'].append('yale_lux')

                enriched.append(artist)

            except Exception as e:
                logger.warning(f"Failed to enrich artist '{artist['name']}' with Yale LUX: {e}")
                enriched.append(artist)

        return enriched

    async def _score_artist_relevance(
        self,
        artists: List[Dict[str, Any]],
        theme: RefinedTheme
    ) -> List[DiscoveredArtist]:
        """
        Score artist relevance to exhibition theme using LLM analysis
        Converts enriched artist dicts to DiscoveredArtist objects with relevance scores
        """
        logger.debug(f"Scoring relevance for {len(artists)} artists")

        discovered_artists = []

        for artist in artists:
            try:
                # Calculate relevance using LLM
                relevance_score, reasoning = await self._calculate_artist_relevance(
                    artist, theme
                )

                # Create DiscoveredArtist object
                discovered_artist = DiscoveredArtist(
                    name=artist.get('name', 'Unknown Artist'),
                    uri=artist.get('wikidata_uri'),
                    getty_ulan_uri=artist.get('getty_ulan_uri'),
                    getty_ulan_id=artist.get('getty_ulan_id'),
                    wikidata_uri=artist.get('wikidata_uri'),
                    wikidata_id=artist.get('wikidata_id'),
                    birth_year=artist.get('birth_year'),
                    death_year=artist.get('death_year'),
                    nationality=artist.get('nationality'),
                    birth_place=artist.get('birth_place'),
                    movements=artist.get('movements', []),
                    techniques=artist.get('techniques', []),
                    themes=artist.get('themes', []),
                    genres=artist.get('genres', []),
                    institutional_connections=artist.get('institutional_connections', []),
                    relevance_score=relevance_score,
                    relevance_reasoning=reasoning,
                    known_works_count=artist.get('known_works_count'),
                    source_endpoint=artist.get('source', 'wikidata'),
                    discovery_sources=artist.get('discovery_sources', []),
                    biography_short=artist.get('biography_short'),
                    biography_long=artist.get('biography_long'),
                    raw_data=artist,
                    discovered_at=datetime.utcnow(),
                    discovery_query=artist.get('concept_label'),
                    discovery_confidence=0.8  # Base confidence
                )

                discovered_artists.append(discovered_artist)

            except Exception as e:
                logger.error(f"Failed to create DiscoveredArtist for '{artist.get('name')}': {e}")

        return discovered_artists

    async def _calculate_artist_relevance(
        self,
        artist: Dict[str, Any],
        theme: RefinedTheme
    ) -> Tuple[float, str]:
        """
        Calculate relevance score and generate reasoning using LLM

        Returns:
            Tuple of (relevance_score, reasoning_text)
        """
        # Build context for LLM
        context = self._build_relevance_context(artist, theme)

        if not self.anthropic_client:
            # Fallback to simple heuristic scoring
            return self._heuristic_relevance_score(artist, theme)

        try:
            # Use Claude to analyze relevance
            prompt = f"""You are an expert art curator evaluating artists for an exhibition.

Exhibition Theme: {theme.exhibition_title}
{f"Subtitle: {theme.subtitle}" if theme.subtitle else ""}

Curatorial Statement:
{theme.curatorial_statement}

Validated Concepts: {', '.join([c.refined_concept for c in theme.validated_concepts])}

Artist Information:
Name: {artist.get('name')}
Lifespan: {artist.get('birth_year', '?')}–{artist.get('death_year', '?')}
Nationality: {artist.get('nationality', 'Unknown')}
Movements: {', '.join(artist.get('movements', []))}
Biography: {artist.get('biography_short', 'No biography available')}

Institutional Presence: {', '.join(artist.get('institutional_connections', ['Unknown'])[:5])}
Known Works: {artist.get('known_works_count', 'Unknown')}

Discovery Context: Found through search for "{artist.get('concept_label', 'general search')}"

Task:
1. Evaluate how relevant this artist is to the exhibition theme (0.0 to 1.0 scale)
2. Provide detailed reasoning explaining the relevance

Format your response as:
SCORE: [number between 0.0 and 1.0]
REASONING: [2-3 sentences explaining the relevance assessment]"""

            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse response
            score = 0.5  # Default
            reasoning = "Artist shows potential relevance to exhibition theme."

            if "SCORE:" in response_text:
                score_line = response_text.split("SCORE:")[1].split("\n")[0].strip()
                try:
                    score = float(score_line)
                    score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                except:
                    pass

            if "REASONING:" in response_text:
                reasoning = response_text.split("REASONING:")[1].strip()

            return score, reasoning

        except Exception as e:
            logger.warning(f"LLM relevance scoring failed: {e}, using heuristic fallback")
            return self._heuristic_relevance_score(artist, theme)

    def _build_relevance_context(self, artist: Dict[str, Any], theme: RefinedTheme) -> str:
        """Build context string for relevance evaluation"""
        context_parts = [
            f"Theme: {theme.exhibition_title}",
            f"Artist: {artist.get('name')}",
            f"Movements: {', '.join(artist.get('movements', []))}",
            f"Concepts: {', '.join([c.refined_concept for c in theme.validated_concepts])}"
        ]
        return " | ".join(context_parts)

    def _heuristic_relevance_score(self, artist: Dict[str, Any], theme: RefinedTheme) -> Tuple[float, str]:
        """
        Fallback heuristic relevance scoring when LLM is unavailable
        """
        score = 0.5  # Base score
        reasoning_parts = []

        # OPTIE B: Check if artist was found via reference artist relationships (HIGH RELEVANCE)
        if artist.get('from_reference'):
            score += 0.25
            relationship = artist.get('relationship_type', 'related to')
            ref_artist = artist.get('reference_artist_name', 'reference artist')
            reasoning_parts.append(
                f"Discovered through relationship with {ref_artist} ({relationship}), indicating high thematic relevance"
            )

        # Check if artist was found via specific concept search
        if artist.get('concept_label'):
            score += 0.2
            reasoning_parts.append(
                f"Discovered through search for '{artist['concept_label']}' which is central to the exhibition theme"
            )

        # Check movement alignment
        artist_movements = [m.lower() for m in artist.get('movements', [])]
        theme_concepts = [c.refined_concept.lower() for c in theme.validated_concepts]

        movement_matches = sum(1 for movement in artist_movements if any(concept in movement for concept in theme_concepts))
        if movement_matches > 0:
            score += min(0.2, movement_matches * 0.1)
            reasoning_parts.append(
                f"Artist's movements ({', '.join(artist.get('movements', []))}) align with exhibition concepts"
            )

        # Check institutional presence
        if artist.get('known_works_count', 0) > 0:
            score += 0.1
            reasoning_parts.append(
                f"Artist has {artist['known_works_count']} known works in institutional collections"
            )

        # Check biographical data availability
        if artist.get('biography_short'):
            score += 0.05

        # Normalize score
        score = min(1.0, score)

        if not reasoning_parts:
            reasoning = f"Artist '{artist.get('name')}' shows general relevance to the exhibition theme based on available data."
        else:
            reasoning = ". ".join(reasoning_parts) + "."

        return score, reasoning

    def _rerank_for_diversity(
        self,
        artists: List[DiscoveredArtist],
        max_artists: int,
        diversity_targets: Dict[str, int]
    ) -> List[DiscoveredArtist]:
        """
        Rerank artists to prioritize diversity while maintaining relevance

        Strategy:
        1. Calculate diversity score for each artist
        2. Combine relevance (70%) + diversity (30%) for final score
        3. Use greedy selection to ensure targets are met
        4. Return balanced, diverse list

        Args:
            artists: Filtered list of discovered artists
            max_artists: Maximum number to return
            diversity_targets: Optional targets like {'min_female': 3, 'min_non_western': 2}

        Returns:
            Reranked list prioritizing diversity
        """
        logger.debug(f"Reranking {len(artists)} artists for diversity")

        # Extract diversity metrics
        for artist in artists:
            # Get gender from raw_data
            gender = artist.raw_data.get('gender', 'unknown')
            artist.raw_data['gender_normalized'] = self._normalize_gender(gender)

            # Get ethnicity/nationality as proxy for diversity
            nationality = artist.nationality or 'unknown'
            artist.raw_data['is_non_western'] = self._is_non_western(nationality)

        # Calculate diversity scores
        for artist in artists:
            diversity_score = self._calculate_diversity_score(artist)
            # Combined score: 70% relevance + 30% diversity
            artist.raw_data['combined_score'] = (artist.relevance_score * 0.7) + (diversity_score * 0.3)

        # Sort by combined score
        artists_sorted = sorted(
            artists,
            key=lambda x: x.raw_data.get('combined_score', x.relevance_score),
            reverse=True
        )

        # Greedy selection to ensure diversity targets
        selected = []
        female_count = 0
        non_western_count = 0
        min_female = diversity_targets.get('min_female', 0)
        min_non_western = diversity_targets.get('min_non_western', 0)

        # First pass: ensure minimum targets
        for artist in artists_sorted:
            if len(selected) >= max_artists:
                break

            gender = artist.raw_data.get('gender_normalized', 'unknown')
            is_non_western = artist.raw_data.get('is_non_western', False)

            # Prioritize if we need more diversity
            should_include = False

            if gender == 'female' and female_count < min_female:
                should_include = True
                female_count += 1
            elif is_non_western and non_western_count < min_non_western:
                should_include = True
                non_western_count += 1
            elif female_count >= min_female and non_western_count >= min_non_western:
                # Targets met, include based on combined score
                should_include = True

            if should_include:
                selected.append(artist)

                if gender == 'female' and not (is_non_western and non_western_count < min_non_western):
                    female_count += (1 if gender == 'female' else 0)
                if is_non_western:
                    non_western_count += 1

        # Second pass: fill remaining slots with highest combined scores
        remaining = max_artists - len(selected)
        if remaining > 0:
            for artist in artists_sorted:
                if artist not in selected:
                    selected.append(artist)
                    remaining -= 1
                    if remaining == 0:
                        break

        # Log diversity metrics
        final_female = sum(1 for a in selected if a.raw_data.get('gender_normalized') == 'female')
        final_non_western = sum(1 for a in selected if a.raw_data.get('is_non_western', False))

        logger.info(
            f"Diversity reranking complete: {len(selected)} artists selected "
            f"({final_female} female, {final_non_western} non-Western)"
        )

        return selected

    def _normalize_gender(self, gender: str) -> str:
        """Normalize gender labels from Wikidata"""
        gender_lower = gender.lower()
        if 'female' in gender_lower or 'woman' in gender_lower:
            return 'female'
        elif 'male' in gender_lower or 'man' in gender_lower:
            return 'male'
        else:
            return 'unknown'

    def _is_non_western(self, nationality: str) -> bool:
        """
        Determine if nationality is non-Western for diversity purposes

        Note: This is a simplified heuristic. In production, should use
        more nuanced geographical/cultural classification.
        """
        western_keywords = [
            'american', 'british', 'french', 'german', 'italian', 'spanish',
            'dutch', 'belgian', 'austrian', 'swiss', 'canadian', 'australian',
            'portuguese', 'irish', 'scottish', 'welsh', 'scandinavian',
            'norwegian', 'swedish', 'danish', 'finnish', 'icelandic'
        ]

        nationality_lower = nationality.lower()
        return not any(keyword in nationality_lower for keyword in western_keywords)

    def _calculate_diversity_score(self, artist: DiscoveredArtist) -> float:
        """
        Calculate diversity bonus score for an artist

        Factors:
        - Gender (bonus for underrepresented)
        - Geographic diversity (non-Western bonus)
        - Time period diversity

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0

        # Gender diversity (0.4 weight)
        gender = artist.raw_data.get('gender_normalized', 'unknown')
        if gender == 'female':
            score += 0.4  # Higher weight for underrepresented gender
        elif gender == 'male':
            score += 0.1  # Lower weight for overrepresented
        else:
            score += 0.2  # Unknown gets moderate score

        # Geographic diversity (0.4 weight)
        if artist.raw_data.get('is_non_western', False):
            score += 0.4
        else:
            score += 0.1

        # Contemporary artist bonus (0.2 weight)
        if artist.is_contemporary():
            score += 0.2
        else:
            score += 0.1

        return min(1.0, score)

    async def _discover_artists_from_yale_lux(self, refined_theme: RefinedTheme) -> List[Dict[str, Any]]:
        """
        Discover artists via Yale LUX API - much faster than Wikidata
        Uses agent type='Person' with movement/style filtering
        """
        all_artists = []

        try:
            # Build search queries for concepts
            for concept in refined_theme.validated_concepts[:4]:  # Limit to top 4 concepts
                try:
                    search_url = "https://lux.collections.yale.edu/api/search/agent"

                    # Try keyword search on concept
                    query = {
                        "q": concept.refined_concept,
                        "page": 1,
                        "_pageSize": 20
                    }

                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.get(search_url, params=query)

                        if response.status_code == 200:
                            data = response.json()
                            items = data.get('orderedItems', [])

                            for item in items:
                                # Extract basic artist data
                                artist_id = item.get('id', '')
                                artist_data = {
                                    'source': 'yale_lux',
                                    'lux_uri': artist_id,
                                    'name': '',
                                    'description': '',
                                    'birth_year': None,
                                    'death_year': None,
                                    'nationality': None
                                }

                                # Parse identified_by for name
                                identified_by = item.get('identified_by', [])
                                for identifier in identified_by:
                                    if identifier.get('type') == 'Name' and identifier.get('classified_as'):
                                        for classification in identifier.get('classified_as', []):
                                            if 'Primary' in classification.get('_label', ''):
                                                artist_data['name'] = identifier.get('content', '')
                                                break

                                # Get biographical dates
                                if 'born' in item:
                                    timespan = item['born'].get('timespan', {})
                                    begin = timespan.get('begin_of_the_begin', '')
                                    if begin:
                                        try:
                                            artist_data['birth_year'] = int(begin[:4])
                                        except:
                                            pass

                                if 'died' in item:
                                    timespan = item['died'].get('timespan', {})
                                    end = timespan.get('end_of_the_end', '')
                                    if end:
                                        try:
                                            artist_data['death_year'] = int(end[:4])
                                        except:
                                            pass

                                # Get description
                                referred_to_by = item.get('referred_to_by', [])
                                for ref in referred_to_by:
                                    if ref.get('type') == 'LinguisticObject':
                                        artist_data['description'] = ref.get('content', '')[:500]
                                        break

                                if artist_data['name']:
                                    all_artists.append(artist_data)

                            logger.info(f"Yale LUX: Found {len(items)} artists for '{concept.refined_concept}'")

                        # Small delay to be polite
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Yale LUX search failed for '{concept.refined_concept}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Yale LUX artist discovery failed: {e}")

        logger.info(f"Yale LUX: Total {len(all_artists)} artists discovered")
        return all_artists

    async def _discover_related_artists(self, reference_artists: List[str]) -> List[Dict[str, Any]]:
        """
        Discover artists related to reference artists via Wikidata relationships

        Uses:
        - influenced_by (P737)
        - student_of (P1066)
        - influenced (P738)
        - student (P802)

        Returns:
            List of artist data dicts with relationship info
        """
        logger.debug(f"Finding related artists for: {', '.join(reference_artists)}")

        all_related = []

        for ref_artist in reference_artists:
            try:
                # First, find the Wikidata QID for this artist
                qid = await self._find_artist_qid(ref_artist)

                if not qid:
                    logger.warning(f"Could not find Wikidata QID for '{ref_artist}'")
                    continue

                logger.info(f"Found QID {qid} for '{ref_artist}', searching for related artists")

                # Build query for related artists
                query = self._build_related_artists_query(qid, ref_artist)

                # Execute query
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://query.wikidata.org/sparql",
                        data={'query': query, 'format': 'json'},
                        headers={
                            'Accept': 'application/sparql-results+json',
                            'User-Agent': 'AICuratorAssistant/1.0'
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', {}).get('bindings', [])

                        for binding in results:
                            artist_data = {
                                'source': 'wikidata_related',
                                'reference_artist': ref_artist,
                                'relationship': binding.get('relationshipLabel', {}).get('value', 'related'),
                                'wikidata_uri': binding.get('relatedArtist', {}).get('value', ''),
                                'wikidata_id': binding.get('relatedArtist', {}).get('value', '').split('/')[-1],
                                'name': binding.get('relatedArtistLabel', {}).get('value', ''),
                                'description': binding.get('description', {}).get('value', ''),
                            }

                            # Parse biographical data
                            if 'birth' in binding:
                                try:
                                    artist_data['birth_year'] = int(binding['birth']['value'][:4])
                                except:
                                    pass

                            if 'death' in binding:
                                try:
                                    artist_data['death_year'] = int(binding['death']['value'][:4])
                                except:
                                    pass

                            if 'nationalityLabel' in binding:
                                artist_data['nationality'] = binding['nationalityLabel']['value']

                            if 'genderLabel' in binding:
                                artist_data['gender'] = binding['genderLabel']['value']

                            if 'movementLabel' in binding:
                                artist_data['movements'] = [binding['movementLabel']['value']]

                            all_related.append(artist_data)

                        logger.info(f"Found {len(results)} related artists for '{ref_artist}'")

            except Exception as e:
                logger.error(f"Error finding related artists for '{ref_artist}': {e}")

        logger.info(f"Total related artists discovered: {len(all_related)}")
        return all_related

    async def _find_artist_qid(self, artist_name: str) -> Optional[str]:
        """Find Wikidata QID for an artist by name"""
        # Hardcoded QIDs for common reference artists (much faster)
        ARTIST_QID_CACHE = {
            'piet mondrian': 'Q151803',
            'kazimir malevich': 'Q130777',
            'josef albers': 'Q170177',
            'wassily kandinsky': 'Q61064',
            'paul klee': 'Q44007',
            'mark rothko': 'Q152010',
            'barnett newman': 'Q374398',
            'clyfford still': 'Q579252',
            'helen frankenthaler': 'Q235281',
            'morris louis': 'Q711269',
            'kenneth noland': 'Q709176',
            'ellsworth kelly': 'Q544899',
            'frank stella': 'Q375268',
            'donald judd': 'Q378393',
            'dan flavin': 'Q560184',
            'sol lewitt': 'Q168474',
            'agnes martin': 'Q235321',
            'ad reinhardt': 'Q354398',
            'yves klein': 'Q154324',
            'theo van doesburg': 'Q157467',
            'georges vantongerloo': 'Q708459',
            'vilmos huszár': 'Q2162032',
            'robert motherwell': 'Q165275',
            'jackson pollock': 'Q37571',
        }

        name_lower = artist_name.lower().strip()
        if name_lower in ARTIST_QID_CACHE:
            return ARTIST_QID_CACHE[name_lower]

        # Otherwise do a simple label search
        query = f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?artist WHERE {{
          ?artist wdt:P106 wd:Q1028181 .  # Occupation: painter
          ?artist rdfs:label "{artist_name}"@en .
        }}
        LIMIT 1
        """

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://query.wikidata.org/sparql",
                    data={'query': query, 'format': 'json'},
                    headers={
                        'Accept': 'application/sparql-results+json',
                        'User-Agent': 'AICuratorAssistant/1.0'
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', {}).get('bindings', [])
                    if results:
                        uri = results[0].get('artist', {}).get('value', '')
                        return uri.split('/')[-1]  # Extract QID

        except Exception as e:
            logger.error(f"Error finding QID for '{artist_name}': {e}")

        return None

    def _build_related_artists_query(self, artist_qid: str, artist_name: str) -> str:
        """Build SPARQL query to find artists related to a specific artist"""
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT DISTINCT ?relatedArtist ?relatedArtistLabel ?relationship ?relationshipLabel
               ?description ?birth ?death ?nationality ?nationalityLabel
               ?gender ?genderLabel ?movement ?movementLabel
        WHERE {{
          # Find related artists through various relationships
          {{
            wd:{artist_qid} wdt:P737 ?relatedArtist .  # influenced by
            BIND("influenced by {artist_name}" AS ?relationship)
          }} UNION {{
            wd:{artist_qid} wdt:P1066 ?relatedArtist .  # student of
            BIND("studied under {artist_name}" AS ?relationship)
          }} UNION {{
            ?relatedArtist wdt:P737 wd:{artist_qid} .  # was influenced by
            BIND("influenced {artist_name}" AS ?relationship)
          }} UNION {{
            ?relatedArtist wdt:P1066 wd:{artist_qid} .  # was student of
            BIND("student of {artist_name}" AS ?relationship)
          }}

          # Ensure it's a painter
          ?relatedArtist wdt:P106 wd:Q1028181 .

          OPTIONAL {{ ?relatedArtist wdt:P569 ?birth }}
          OPTIONAL {{ ?relatedArtist wdt:P570 ?death }}
          OPTIONAL {{ ?relatedArtist wdt:P27 ?nationality }}
          OPTIONAL {{ ?relatedArtist wdt:P21 ?gender }}
          OPTIONAL {{ ?relatedArtist wdt:P135 ?movement }}
          OPTIONAL {{ ?relatedArtist schema:description ?description FILTER(LANG(?description) = "en") }}

          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
          }}
        }}
        LIMIT 30
        """


__all__ = ['ArtistDiscoveryAgent', 'ArtistSearchQuery']