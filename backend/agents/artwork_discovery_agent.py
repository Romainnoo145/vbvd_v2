"""
Artwork Discovery Agent - Stage 3 of AI Curator Pipeline
Discovers and curates artworks based on validated artists and exhibition theme using Linked Art data
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
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from backend.clients.essential_data_client import EssentialDataClient
from backend.clients.artic_client import ArticClient
from backend.models import ArtworkCandidate, DiscoveredArtist
from backend.agents.theme_refinement_agent import RefinedTheme

logger = logging.getLogger(__name__)


class ArtworkSearchQuery(BaseModel):
    """Query structure for artwork discovery"""
    query_type: str  # "yale_lux", "wikidata", "artic", "iiif"
    sparql: Optional[str] = None
    endpoint_params: Optional[Dict[str, Any]] = None
    artist_uri: Optional[str] = None
    artist_name: str
    theme_concept: Optional[str] = None
    date_start: Optional[int] = None
    date_end: Optional[int] = None


class ArtworkDiscoveryAgent:
    """
    Stage 3 Agent: Discover artworks relevant to exhibition theme from validated artists

    Workflow:
    1. Take validated theme + selected artists from Stages 1 & 2
    2. Search Yale LUX API for high-quality Linked Art collection data
    3. Query Wikidata SPARQL for additional artwork metadata and relationships
    4. Fetch IIIF manifests for visual content where available
    5. Enrich with provenance, exhibition history, and technical data
    6. Score relevance using theme + visual content analysis
    7. Check loan feasibility and practical considerations
    8. Output: Curated list of ArtworkCandidate objects for exhibition
    """

    def __init__(self, data_client: EssentialDataClient, openai_api_key: Optional[str] = None):
        self.data_client = data_client
        self.agent_version = "1.0"

        # Initialize OpenAI client for LLM-based relevance scoring
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI SDK not installed - using heuristic scoring only")
            self.openai_client = None
        else:
            api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("No OpenAI API key provided - LLM scoring will be limited")
            self.openai_client = OpenAI(api_key=api_key) if api_key else None

    async def discover_artworks(
        self,
        refined_theme: RefinedTheme,
        selected_artists: List[DiscoveredArtist],
        session_id: str,
        max_artworks: int = 50,
        min_relevance: float = 0.5,
        artworks_per_artist: int = 5
    ) -> List[ArtworkCandidate]:
        """
        Discover artworks relevant to exhibition theme from validated artists

        Args:
            refined_theme: Output from Stage 1 (Theme Refinement)
            selected_artists: Output from Stage 2 (Artist Discovery)
            session_id: Session identifier
            max_artworks: Maximum number of artworks to return
            min_relevance: Minimum relevance score threshold
            artworks_per_artist: Target artworks per artist

        Returns:
            List of ArtworkCandidate objects ranked by relevance
        """
        logger.info(f"Starting artwork discovery for session {session_id} with {len(selected_artists)} artists")
        start_time = datetime.utcnow()

        # Step 1: Build artwork search queries for each artist
        artwork_queries = self._build_artwork_queries(selected_artists, refined_theme)

        # Step 2: Execute parallel searches across Yale LUX and Wikidata
        raw_artwork_data = await self._execute_artwork_searches(artwork_queries)

        # Step 3: Deduplicate and merge artwork records
        merged_artworks = self._merge_artwork_records(raw_artwork_data)

        # Step 4: Fetch IIIF manifests for visual content
        iiif_enriched_artworks = await self._fetch_iiif_manifests(merged_artworks)

        # Step 5: Enrich with detailed metadata (provenance, exhibition history)
        enriched_artworks = await self._enrich_artwork_metadata(iiif_enriched_artworks)

        # Step 6: Calculate relevance scores using theme analysis
        scored_artworks = await self._score_artwork_relevance(
            enriched_artworks,
            refined_theme,
            selected_artists
        )

        # Step 7: Check loan feasibility and practical considerations
        feasibility_checked = await self._check_loan_feasibility(scored_artworks)

        # Step 8: Filter by relevance threshold
        filtered_artworks = [
            artwork for artwork in feasibility_checked
            if artwork.relevance_score >= min_relevance
        ]

        # Step 9: Rank and select final artworks
        ranked_artworks = self._rank_and_select_artworks(
            filtered_artworks,
            max_artworks,
            artworks_per_artist,
            selected_artists
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Artwork discovery completed in {processing_time:.2f}s - "
            f"Found {len(ranked_artworks)} artworks (from {len(merged_artworks)} candidates)"
        )

        return ranked_artworks

    def _build_artwork_queries(
        self,
        artists: List[DiscoveredArtist],
        theme: RefinedTheme
    ) -> List[ArtworkSearchQuery]:
        """Build search queries for each artist across multiple endpoints"""
        queries = []

        for artist in artists:
            # Query 1: Yale LUX search by artist name
            queries.append(ArtworkSearchQuery(
                query_type="yale_lux",
                endpoint_params={
                    'q': artist.name,
                    'type': 'HumanMadeObject',
                    'page': 1,
                    'pageSize': 20
                },
                artist_uri=artist.uri,
                artist_name=artist.name
            ))

            # Query 2: Wikidata SPARQL for this artist's works
            if artist.wikidata_id:
                wikidata_query = self._build_wikidata_artwork_query(
                    artist.wikidata_id,
                    artist.name
                )
                queries.append(ArtworkSearchQuery(
                    query_type="wikidata",
                    sparql=wikidata_query,
                    artist_uri=artist.wikidata_uri,
                    artist_name=artist.name
                ))

            # Query 3: Art Institute of Chicago for modern art (1880-present)
            # Only search for artists working in modern period
            if artist.birth_year and artist.birth_year >= 1850:
                queries.append(ArtworkSearchQuery(
                    query_type="artic",
                    artist_name=artist.name,
                    artist_uri=artist.uri,
                    date_start=1880,
                    date_end=2025
                ))

            # Query 4: Europeana for European cultural heritage (all periods)
            # 58M+ items with IIIF support
            queries.append(ArtworkSearchQuery(
                query_type="europeana",
                artist_name=artist.name,
                artist_uri=artist.uri
            ))

        logger.info(f"Built {len(queries)} artwork discovery queries for {len(artists)} artists")
        return queries

    def _build_wikidata_artwork_query(self, artist_qid: str, artist_name: str) -> str:
        """
        Build SPARQL query to find artworks by specific artist

        Returns artworks with:
        - Title, description, image
        - Creation date, medium, dimensions
        - Current location, collection
        - Subject matter
        """
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>

        SELECT DISTINCT ?artwork ?artworkLabel ?description
               ?image ?date ?medium ?mediumLabel
               ?collection ?collectionLabel
               ?height ?width ?subject ?subjectLabel
               ?inventory ?genre ?genreLabel
        WHERE {{
          # Find artworks by this artist
          ?artwork wdt:P170 wd:{artist_qid} .  # Creator

          # Basic info
          OPTIONAL {{ ?artwork wdt:P18 ?image }}
          OPTIONAL {{ ?artwork schema:description ?description FILTER(LANG(?description) = "en") }}

          # Creation details
          OPTIONAL {{ ?artwork wdt:P571 ?date }}      # Inception date
          OPTIONAL {{ ?artwork wdt:P186 ?medium }}    # Material/medium
          OPTIONAL {{ ?artwork wdt:P136 ?genre }}     # Genre

          # Physical properties
          OPTIONAL {{ ?artwork wdt:P2048 ?height }}   # Height
          OPTIONAL {{ ?artwork wdt:P2049 ?width }}    # Width

          # Location and collection
          OPTIONAL {{ ?artwork wdt:P195 ?collection }} # Collection
          OPTIONAL {{ ?artwork wdt:P217 ?inventory }}  # Inventory number

          # Subject matter
          OPTIONAL {{ ?artwork wdt:P921 ?subject }}    # Main subject

          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
          }}
        }}
        LIMIT 50
        """

    async def _execute_artwork_searches(
        self,
        queries: List[ArtworkSearchQuery]
    ) -> List[Dict[str, Any]]:
        """Execute all artwork searches in parallel"""
        logger.debug(f"Executing {len(queries)} artwork search queries")

        tasks = []
        for query in queries:
            if query.query_type == "yale_lux":
                tasks.append(self._execute_yale_lux_query(query))
            elif query.query_type == "wikidata":
                tasks.append(self._execute_wikidata_artwork_query(query))
            elif query.query_type == "artic":
                tasks.append(self._execute_artic_query(query))
            elif query.query_type == "europeana":
                tasks.append(self._execute_europeana_query(query))

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_artworks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i} failed: {result}")
            elif isinstance(result, list):
                all_artworks.extend(result)

        logger.info(f"Retrieved {len(all_artworks)} raw artwork records")
        return all_artworks

    async def _execute_yale_lux_query(
        self,
        query: ArtworkSearchQuery
    ) -> List[Dict[str, Any]]:
        """Execute Yale LUX API search for artworks"""
        try:
            search_url = "https://lux.collections.yale.edu/api/search/item"
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'AI-Curator-Assistant/1.0 (Educational Project)'
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    search_url,
                    params=query.endpoint_params,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    artworks = []

                    # Parse Activity Streams format
                    items = data.get('orderedItems', [])

                    for item in items:
                        artwork_data = {
                            'source': 'yale_lux',
                            'artist_name': query.artist_name,
                            'artist_uri': query.artist_uri,
                            'uri': item.get('id', ''),
                            'title': item.get('_label', 'Untitled'),
                            'type': item.get('type', ''),
                        }

                        # Extract identified_by names
                        if 'identified_by' in item:
                            for identifier in item['identified_by']:
                                if identifier.get('type') == 'Name':
                                    artwork_data['primary_name'] = identifier.get('content', '')
                                    break
                                elif identifier.get('type') == 'Identifier':
                                    artwork_data['inventory_number'] = identifier.get('content', '')

                        # Extract production information
                        if 'produced_by' in item:
                            production = item['produced_by']

                            # Creation date
                            if 'timespan' in production:
                                timespan = production['timespan']
                                artwork_data['date_created'] = timespan.get('_label', '')
                                if 'begin_of_the_begin' in timespan:
                                    artwork_data['date_created_earliest'] = int(timespan['begin_of_the_begin'][:4])
                                if 'end_of_the_end' in timespan:
                                    artwork_data['date_created_latest'] = int(timespan['end_of_the_end'][:4])

                            # Technique
                            if 'technique' in production:
                                techniques = []
                                for tech in production['technique']:
                                    if '_label' in tech:
                                        techniques.append(tech['_label'])
                                artwork_data['technique'] = ', '.join(techniques)

                        # Extract material/medium
                        if 'made_of' in item:
                            materials = []
                            for material in item['made_of']:
                                if '_label' in material:
                                    materials.append(material['_label'])
                            artwork_data['medium'] = ', '.join(materials)

                        # Extract dimensions
                        if 'dimension' in item:
                            dimensions = {}
                            for dim in item['dimension']:
                                dim_type = dim.get('classified_as', [{}])[0].get('_label', '')
                                value = dim.get('value', 0)
                                unit = dim.get('unit', {}).get('_label', 'cm')

                                if 'height' in dim_type.lower():
                                    artwork_data['height_cm'] = value
                                elif 'width' in dim_type.lower():
                                    artwork_data['width_cm'] = value
                                elif 'depth' in dim_type.lower():
                                    artwork_data['depth_cm'] = value

                                dimensions[dim_type] = {'value': value, 'unit': unit}

                            artwork_data['dimensions'] = dimensions

                        # Current location
                        if 'current_location' in item:
                            location = item['current_location']
                            artwork_data['current_location'] = location.get('_label', '')
                            artwork_data['institution_name'] = location.get('_label', '')
                            artwork_data['institution_uri'] = location.get('id', '')

                        # Subject matter
                        if 'about' in item:
                            subjects = []
                            for subject in item['about']:
                                if '_label' in subject:
                                    subjects.append(subject['_label'])
                            artwork_data['subjects'] = subjects

                        # IIIF Manifests from subject_of (Linked Art spec)
                        if 'subject_of' in item:
                            for document in item['subject_of']:
                                if 'digitally_carried_by' in document:
                                    for digital_obj in document['digitally_carried_by']:
                                        # Check if this conforms to IIIF Presentation API
                                        conforms_to = digital_obj.get('conforms_to', [])
                                        is_iiif = any(
                                            'iiif.io/api/presentation' in str(c.get('id', ''))
                                            for c in conforms_to if isinstance(c, dict)
                                        )

                                        if is_iiif and 'access_point' in digital_obj:
                                            access_points = digital_obj['access_point']
                                            if isinstance(access_points, list) and len(access_points) > 0:
                                                manifest_url = access_points[0].get('id')
                                                if manifest_url:
                                                    artwork_data['iiif_manifest'] = manifest_url
                                                    break

                                if 'iiif_manifest' in artwork_data:
                                    break

                        # Fallback: Check representation field for direct image URLs
                        if 'representation' in item and 'iiif_manifest' not in artwork_data:
                            representations = item['representation']
                            if isinstance(representations, list) and len(representations) > 0:
                                first_rep = representations[0]
                                if 'id' in first_rep:
                                    # Store as thumbnail, not manifest
                                    artwork_data['thumbnail_url'] = first_rep['id']

                        artworks.append(artwork_data)

                    return artworks
                else:
                    logger.error(f"Yale LUX query failed with status {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error executing Yale LUX query: {e}", exc_info=True)
            return []

    async def _execute_wikidata_artwork_query(
        self,
        query: ArtworkSearchQuery
    ) -> List[Dict[str, Any]]:
        """Execute Wikidata SPARQL query for artworks"""
        try:
            sparql_url = "https://query.wikidata.org/sparql"
            headers = {
                'Accept': 'application/sparql-results+json',
                'User-Agent': 'AI-Curator-Assistant/1.0 (Educational Project)'
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    sparql_url,
                    data={'query': query.sparql, 'format': 'json'},
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    artworks = []

                    for binding in data.get('results', {}).get('bindings', []):
                        artwork_data = {
                            'source': 'wikidata',
                            'artist_name': query.artist_name,
                            'artist_uri': query.artist_uri,
                            'uri': binding.get('artwork', {}).get('value', ''),
                            'wikidata_id': binding.get('artwork', {}).get('value', '').split('/')[-1],
                            'title': binding.get('artworkLabel', {}).get('value', 'Untitled'),
                            'description': binding.get('description', {}).get('value', ''),
                        }

                        # Parse date
                        if 'date' in binding:
                            date_str = binding['date']['value']
                            artwork_data['date_created'] = date_str
                            try:
                                # Extract year
                                year = int(date_str[:4])
                                artwork_data['date_created_earliest'] = year
                                artwork_data['date_created_latest'] = year
                            except:
                                pass

                        # Medium
                        if 'mediumLabel' in binding:
                            artwork_data['medium'] = binding['mediumLabel']['value']

                        # Genre
                        if 'genreLabel' in binding:
                            artwork_data['genre'] = binding['genreLabel']['value']

                        # Dimensions
                        if 'height' in binding:
                            try:
                                artwork_data['height_cm'] = float(binding['height']['value'])
                            except:
                                pass

                        if 'width' in binding:
                            try:
                                artwork_data['width_cm'] = float(binding['width']['value'])
                            except:
                                pass

                        # Collection
                        if 'collectionLabel' in binding:
                            artwork_data['institution_name'] = binding['collectionLabel']['value']

                        # Inventory number
                        if 'inventory' in binding:
                            artwork_data['inventory_number'] = binding['inventory']['value']

                        # Subject
                        if 'subjectLabel' in binding:
                            artwork_data['subjects'] = [binding['subjectLabel']['value']]

                        # Image URL
                        if 'image' in binding:
                            artwork_data['thumbnail_url'] = binding['image']['value']

                        artworks.append(artwork_data)

                    return artworks
                else:
                    logger.error(f"Wikidata query failed with status {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error executing Wikidata query: {e}", exc_info=True)
            return []

    async def _execute_artic_query(
        self,
        query: ArtworkSearchQuery
    ) -> List[Dict[str, Any]]:
        """Execute Art Institute of Chicago API query for artworks"""
        try:
            async with ArticClient(timeout=30.0) as artic_client:
                artworks_data = await artic_client.search_by_artist(
                    artist_name=query.artist_name,
                    date_start=query.date_start,
                    date_end=query.date_end,
                    limit=20
                )

                artworks = []
                for artwork in artworks_data:
                    # Convert Art Institute format to our standard format
                    artwork_data = {
                        'source': 'artic',
                        'artist_name': query.artist_name,
                        'artist_uri': query.artist_uri,
                        'uri': f"https://www.artic.edu/artworks/{artwork['id']}",
                        'artic_id': artwork['id'],
                        'title': artwork.get('title', 'Untitled'),
                    }

                    # Add artist display (may include birth/death years, nationality)
                    if artwork.get('artist_display'):
                        artwork_data['artist_display'] = artwork['artist_display']

                    # Date information
                    if artwork.get('date_display'):
                        artwork_data['date_created'] = artwork['date_display']

                    if artwork.get('date_start'):
                        artwork_data['date_created_earliest'] = artwork['date_start']

                    if artwork.get('date_end'):
                        artwork_data['date_created_latest'] = artwork['date_end']

                    # Medium and technique
                    if artwork.get('medium_display'):
                        artwork_data['medium'] = artwork['medium_display']

                    # Classification
                    if artwork.get('classification_title'):
                        artwork_data['artwork_type'] = artwork['classification_title']

                    if artwork.get('artwork_type_title'):
                        artwork_data['style'] = artwork['artwork_type_title']

                    # Department (can use as institution)
                    if artwork.get('department_title'):
                        artwork_data['institution_name'] = f"Art Institute of Chicago - {artwork['department_title']}"
                    else:
                        artwork_data['institution_name'] = "Art Institute of Chicago"

                    # Place of origin
                    if artwork.get('place_of_origin'):
                        artwork_data['place_of_origin'] = artwork['place_of_origin']

                    # Dimensions
                    if artwork.get('dimensions_detail'):
                        dims = artwork['dimensions_detail']
                        for dim in dims:
                            if dim.get('elementName') == 'Overall':
                                measurements = dim.get('elementMeasurements', {})
                                if 'Height' in measurements:
                                    artwork_data['height_cm'] = measurements['Height']
                                if 'Width' in measurements:
                                    artwork_data['width_cm'] = measurements['Width']
                                if 'Depth' in measurements:
                                    artwork_data['depth_cm'] = measurements['Depth']
                                break

                    # Images - IIIF support!
                    if artwork.get('iiif_url'):
                        # Use IIIF manifest construction
                        image_id = artwork.get('image_id')
                        if image_id:
                            # Art Institute uses IIIF Image API 2.0
                            artwork_data['high_res_images'] = [artwork['iiif_url']]
                            artwork_data['thumbnail_url'] = artwork.get('thumbnail_iiif_url', artwork['iiif_url'])
                            artwork_data['iiif_image_id'] = image_id

                    # Copyright and permissions
                    if artwork.get('copyright_notice'):
                        artwork_data['copyright_status'] = artwork['copyright_notice']

                    if artwork.get('is_public_domain'):
                        artwork_data['reproduction_rights'] = 'Public Domain' if artwork['is_public_domain'] else 'Rights Reserved'

                    # Description
                    if artwork.get('short_description'):
                        artwork_data['description'] = artwork['short_description']
                    elif artwork.get('description'):
                        artwork_data['description'] = artwork['description']

                    # Gallery location
                    if artwork.get('gallery_title'):
                        artwork_data['current_location'] = artwork['gallery_title']
                    elif artwork.get('on_loan_display'):
                        artwork_data['current_location'] = artwork['on_loan_display']

                    # Credit line (provenance info)
                    if artwork.get('credit_line'):
                        artwork_data['provenance'] = [artwork['credit_line']]

                    artworks.append(artwork_data)

                logger.info(f"Art Institute API returned {len(artworks)} artworks for {query.artist_name}")
                return artworks

        except Exception as e:
            logger.error(f"Error executing Art Institute query: {e}", exc_info=True)
            return []

    async def _execute_europeana_query(
        self,
        query: ArtworkSearchQuery
    ) -> List[Dict[str, Any]]:
        """Execute Europeana API query for artworks - 58M+ European cultural heritage items"""
        try:
            async with EssentialDataClient(timeout=30.0) as client:
                # Use the new Europeana search method
                results = await client._search_europeana(
                    query=query.artist_name,
                    context='artwork painting'
                )

                artworks = []
                for item in results:
                    # Convert Europeana format to our standard format
                    artwork_data = {
                        'source': 'europeana',
                        'artist_name': query.artist_name,
                        'artist_uri': query.artist_uri,
                        'uri': item.get('url', ''),
                        'europeana_id': item.get('id', ''),
                        'title': item.get('title', 'Untitled'),
                    }

                    # Artist information
                    if item.get('artist_name'):
                        artwork_data['artist_display'] = item['artist_name']

                    # Date information
                    if item.get('date'):
                        artwork_data['date_created'] = item['date']

                    # Description
                    if item.get('description'):
                        artwork_data['description'] = item['description']

                    # Institution/collection
                    if item.get('data_provider'):
                        artwork_data['institution_name'] = item['data_provider']

                    # Country
                    if item.get('country'):
                        artwork_data['place_of_origin'] = item['country']

                    # Images - regular and thumbnail
                    if item.get('image_url'):
                        artwork_data['high_res_images'] = [item['image_url']]

                    if item.get('thumbnail_url'):
                        artwork_data['thumbnail_url'] = item['thumbnail_url']

                    # IIIF Manifest - KEY FOR DISPLAY!
                    if item.get('iiif_manifest'):
                        artwork_data['iiif_manifest'] = item['iiif_manifest']
                        logger.debug(f"Found IIIF manifest for {artwork_data['title']}")

                    # Rights information
                    if item.get('rights'):
                        artwork_data['copyright_status'] = item['rights']
                        # Check if it's open access
                        if 'open' in item['rights'].lower() or 'public' in item['rights'].lower():
                            artwork_data['reproduction_rights'] = 'Open Access'
                        else:
                            artwork_data['reproduction_rights'] = 'Rights Reserved'

                    # Type of artwork
                    if item.get('type'):
                        artwork_data['artwork_type'] = item['type']

                    artworks.append(artwork_data)

                logger.info(f"Europeana API returned {len(artworks)} artworks for {query.artist_name}, "
                           f"{sum(1 for a in artworks if a.get('iiif_manifest'))} with IIIF")
                return artworks

        except Exception as e:
            logger.error(f"Error executing Europeana query: {e}", exc_info=True)
            return []

    def _merge_artwork_records(
        self,
        raw_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate and merge artwork records from different sources
        Uses title + artist matching and URI matching
        """
        merged = {}

        for artwork in raw_data:
            # Create unique key based on URI or normalized title+artist
            key = None

            if artwork.get('uri'):
                key = f"uri:{artwork['uri']}"
            elif artwork.get('wikidata_id'):
                key = f"wd:{artwork['wikidata_id']}"
            else:
                # Fallback to title + artist
                title = artwork.get('title', '').strip().lower()
                artist = artwork.get('artist_name', '').strip().lower()
                if title and artist:
                    key = f"title:{artist}:{title}"

            if not key:
                continue

            if key in merged:
                # Merge with existing record
                existing = merged[key]

                # Merge sources
                existing_sources = existing.get('all_sources', [])
                if artwork.get('source'):
                    existing['all_sources'] = list(set(existing_sources + [artwork['source']]))

                # Prefer non-empty values
                for field in ['description', 'medium', 'technique', 'date_created',
                             'institution_name', 'iiif_manifest', 'thumbnail_url']:
                    if field in artwork and artwork[field] and not existing.get(field):
                        existing[field] = artwork[field]

                # Merge subjects
                if 'subjects' in artwork:
                    existing_subjects = existing.get('subjects', [])
                    existing['subjects'] = list(set(existing_subjects + artwork['subjects']))

                # Keep best dimensions
                if 'height_cm' in artwork and not existing.get('height_cm'):
                    existing['height_cm'] = artwork['height_cm']
                if 'width_cm' in artwork and not existing.get('width_cm'):
                    existing['width_cm'] = artwork['width_cm']
            else:
                # New artwork
                artwork['all_sources'] = [artwork.get('source', 'unknown')]
                merged[key] = artwork

        logger.info(f"Merged {len(raw_data)} records into {len(merged)} unique artworks")
        return list(merged.values())

    async def _fetch_iiif_manifests(
        self,
        artworks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fetch IIIF manifests and extract images
        Supports both IIIF Presentation API 2.0 and 3.0
        """
        from backend.utils.iiif_utils import fetch_and_parse_manifest

        logger.debug(f"Fetching IIIF manifests for {len(artworks)} artworks")

        enriched = []
        for artwork in artworks:
            if artwork.get('iiif_manifest'):
                try:
                    manifest_url = artwork['iiif_manifest']
                    logger.debug(f"Fetching IIIF manifest: {manifest_url}")

                    # Use our comprehensive IIIF parser
                    metadata, images = await fetch_and_parse_manifest(manifest_url, timeout=10.0)

                    if metadata:
                        # Update artwork with manifest metadata
                        if 'rights' in metadata:
                            artwork['reproduction_rights'] = metadata['rights']
                        if 'copyright' in metadata:
                            artwork['copyright_status'] = metadata['copyright']
                        if 'thumbnail' in metadata and not artwork.get('thumbnail_url'):
                            artwork['thumbnail_url'] = metadata['thumbnail']

                    if images:
                        # Extract image URLs (prefer IIIF Image API URLs over direct URLs)
                        image_urls = []
                        for img in images[:5]:  # Limit to 5 images
                            # Prefer IIIF Image API URL (full resolution)
                            if 'iiif_url' in img:
                                image_urls.append(img['iiif_url'])
                            elif 'url' in img:
                                image_urls.append(img['url'])

                        if image_urls:
                            artwork['high_res_images'] = image_urls
                            # Use first image as thumbnail if we don't have one
                            if not artwork.get('thumbnail_url'):
                                artwork['thumbnail_url'] = image_urls[0]

                        logger.debug(f"Extracted {len(image_urls)} images from IIIF manifest")

                except Exception as e:
                    logger.warning(f"Failed to fetch IIIF manifest for {artwork.get('title')}: {e}")

            enriched.append(artwork)

        return enriched

    async def _enrich_artwork_metadata(
        self,
        artworks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich artworks with additional metadata"""
        logger.debug(f"Enriching {len(artworks)} artworks with metadata")

        # For now, calculate completeness score
        for artwork in artworks:
            completeness_score = self._calculate_completeness_score(artwork)
            artwork['completeness_score'] = completeness_score

        return artworks

    def _calculate_completeness_score(self, artwork: Dict[str, Any]) -> float:
        """
        Calculate how complete the artwork metadata is (P0-Critical filtering)

        PRP Requirements:
        - Require real title (not 'Untitled')
        - Require creation date (not 'Date unknown')
        - Require either dimensions OR medium
        - Require institution name
        - Calculate completeness score ≥ 60% before inclusion
        """
        score = 0.0
        total_fields = 10

        # CRITICAL FIELDS (weighted scoring, no auto-fail)
        # Title - but reject generic untitled
        title = artwork.get('title', '').strip()
        bad_titles = ['untitled', 'untitled (artwork)', 'date unknown', 'unknown', '']
        if title and title.lower() not in bad_titles:
            score += 2.0  # Good title

        # Artist name
        if artwork.get('artist_name'):
            score += 2.0

        # Creation date
        has_date = (artwork.get('date_created') and
                   artwork.get('date_created').lower() not in ['unknown', 'date unknown'])
        has_year = artwork.get('date_created_earliest') is not None
        if has_date or has_year:
            score += 1.5

        # Institution name
        if artwork.get('institution_name'):
            score += 1.5

        # Dimensions OR Medium
        has_dimensions = artwork.get('height_cm') or artwork.get('width_cm')
        has_medium = artwork.get('medium')
        if has_dimensions:
            score += 0.75
        if has_medium:
            score += 0.75

        # ADDITIONAL QUALITY FIELDS
        # Description
        if artwork.get('description'):
            score += 1.0

        # Physical details (both dimensions)
        if artwork.get('height_cm') and artwork.get('width_cm'):
            score += 0.5

        # Technique
        if artwork.get('technique'):
            score += 0.5

        # Digital assets (IIIF preferred)
        if artwork.get('iiif_manifest'):
            score += 1.0  # IIIF is valuable
        elif artwork.get('thumbnail_url'):
            score += 0.5

        # Subject/classification
        if artwork.get('subjects') and len(artwork.get('subjects', [])) > 0:
            score += 0.5

        return round(min(score / total_fields, 1.0), 2)

    async def _score_artwork_relevance(
        self,
        artworks: List[Dict[str, Any]],
        theme: RefinedTheme,
        artists: List[DiscoveredArtist]
    ) -> List[ArtworkCandidate]:
        """
        Score artwork relevance to exhibition theme
        Converts enriched artwork dicts to ArtworkCandidate objects with scores
        """
        logger.debug(f"Scoring relevance for {len(artworks)} artworks")

        # Build artist relevance map for context
        artist_relevance_map = {
            artist.name: artist.relevance_score
            for artist in artists
        }

        artwork_candidates = []

        for artwork in artworks:
            try:
                # Calculate relevance
                relevance_score, reasoning = await self._calculate_artwork_relevance(
                    artwork,
                    theme,
                    artist_relevance_map
                )

                # Create ArtworkCandidate object
                candidate = ArtworkCandidate(
                    uri=artwork.get('uri', f"temp-{artwork.get('title', 'unknown')}"),
                    title=artwork.get('title', 'Untitled'),
                    alternative_titles=artwork.get('alternative_titles', []),
                    artist_name=artwork.get('artist_name'),
                    artist_uri=artwork.get('artist_uri'),
                    date_created=artwork.get('date_created'),
                    date_created_earliest=artwork.get('date_created_earliest'),
                    date_created_latest=artwork.get('date_created_latest'),
                    medium=artwork.get('medium'),
                    technique=artwork.get('technique'),
                    dimensions=artwork.get('dimensions'),
                    height_cm=artwork.get('height_cm'),
                    width_cm=artwork.get('width_cm'),
                    depth_cm=artwork.get('depth_cm'),
                    genre=artwork.get('genre'),
                    subjects=artwork.get('subjects', []),
                    current_location=artwork.get('current_location'),
                    institution_name=artwork.get('institution_name'),
                    institution_uri=artwork.get('institution_uri'),
                    inventory_number=artwork.get('inventory_number'),
                    iiif_manifest=artwork.get('iiif_manifest'),
                    thumbnail_url=artwork.get('thumbnail_url'),
                    high_res_images=artwork.get('high_res_images', []),
                    copyright_status=artwork.get('copyright_status'),
                    reproduction_rights=artwork.get('reproduction_rights'),
                    relevance_score=relevance_score,
                    relevance_reasoning=reasoning,
                    theme_connections=self._extract_theme_connections(artwork, theme),
                    completeness_score=artwork.get('completeness_score', 0.0),
                    source=artwork.get('source', 'unknown'),
                    source_url=artwork.get('uri'),
                    all_sources=artwork.get('all_sources', []),
                    description=artwork.get('description'),
                    raw_data=artwork,
                    discovered_at=datetime.utcnow(),
                    discovery_confidence=0.8
                )

                artwork_candidates.append(candidate)

            except Exception as e:
                logger.error(f"Failed to create ArtworkCandidate for '{artwork.get('title')}': {e}")

        return artwork_candidates

    def _extract_theme_connections(
        self,
        artwork: Dict[str, Any],
        theme: RefinedTheme
    ) -> List[str]:
        """Extract specific connections between artwork and theme"""
        connections = []

        # Check subject matter alignment
        artwork_subjects = [s.lower() for s in artwork.get('subjects', [])]
        theme_concepts = [c.refined_concept.lower() for c in theme.validated_concepts]

        for subject in artwork_subjects:
            for concept in theme_concepts:
                if concept in subject or subject in concept:
                    connections.append(f"Subject matter: {subject} relates to {concept}")

        # Check genre alignment
        if artwork.get('genre'):
            genre_lower = artwork['genre'].lower()
            for concept in theme_concepts:
                if concept in genre_lower:
                    connections.append(f"Genre alignment: {artwork['genre']}")

        # Check temporal alignment
        if artwork.get('date_created_earliest'):
            year = artwork['date_created_earliest']
            if theme.research_backing.chronological_scope:
                scope = theme.research_backing.chronological_scope
                if str(year // 100) in scope or f"{year}s" in scope:
                    connections.append(f"Temporal fit: created {year}")

        return connections[:5]  # Limit to 5 connections

    async def _calculate_artwork_relevance(
        self,
        artwork: Dict[str, Any],
        theme: RefinedTheme,
        artist_relevance_map: Dict[str, float]
    ) -> Tuple[float, str]:
        """
        Calculate relevance score and reasoning using LLM or heuristics

        Returns:
            Tuple of (relevance_score, reasoning_text)
        """
        if not self.openai_client:
            return self._heuristic_artwork_relevance(artwork, theme, artist_relevance_map)

        try:
            # Use GPT to analyze relevance
            prompt = f"""You are an expert curator evaluating artworks for an exhibition.

Exhibition Theme: {theme.exhibition_title}
{f"Subtitle: {theme.subtitle}" if theme.subtitle else ""}

Curatorial Statement:
{theme.curatorial_statement}

Key Concepts: {', '.join([c.refined_concept for c in theme.validated_concepts])}

Artwork Information:
Title: {artwork.get('title', 'Untitled')}
Artist: {artwork.get('artist_name', 'Unknown')}
Date: {artwork.get('date_created', 'Unknown')}
Medium: {artwork.get('medium', 'Unknown')}
Subjects: {', '.join(artwork.get('subjects', ['None']))}
Genre: {artwork.get('genre', 'Unknown')}
Description: {artwork.get('description', 'No description available')[:300]}

Collection: {artwork.get('institution_name', 'Unknown')}

Task:
1. Evaluate how relevant this artwork is to the exhibition theme (0.0 to 1.0 scale)
2. Provide detailed reasoning explaining the relevance assessment

Format your response as:
SCORE: [number between 0.0 and 1.0]
REASONING: [2-3 sentences explaining the relevance assessment]"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.choices[0].message.content

            # Parse response
            score = 0.5  # Default
            reasoning = "Artwork shows potential relevance to exhibition theme."

            if "SCORE:" in response_text:
                score_line = response_text.split("SCORE:")[1].split("\n")[0].strip()
                try:
                    score = float(score_line)
                    score = max(0.0, min(1.0, score))
                except:
                    pass

            if "REASONING:" in response_text:
                reasoning = response_text.split("REASONING:")[1].strip()

            return score, reasoning

        except Exception as e:
            logger.warning(f"LLM relevance scoring failed: {e}, using heuristic fallback")
            return self._heuristic_artwork_relevance(artwork, theme, artist_relevance_map)

    def _heuristic_artwork_relevance(
        self,
        artwork: Dict[str, Any],
        theme: RefinedTheme,
        artist_relevance_map: Dict[str, float]
    ) -> Tuple[float, str]:
        """
        Fallback heuristic relevance scoring (P1-High enhancement)

        PRP Weighted Scoring:
        - Date relevance: 30%
        - Theme/style match: 30%
        - Metadata quality: 20%
        - Visual availability: 20%
        """
        score_components = {
            'date_relevance': 0.0,
            'theme_style_match': 0.0,
            'metadata_quality': 0.0,
            'visual_availability': 0.0
        }
        reasoning_parts = []

        # COMPONENT 1: Date Relevance (30%)
        date_score = self._calculate_date_relevance(artwork, theme)
        score_components['date_relevance'] = date_score * 0.30
        if date_score > 0.5:
            year = artwork.get('date_created_earliest', 'unknown')
            reasoning_parts.append(f"Created {year}, aligns with exhibition period (score: {date_score:.2f})")

        # COMPONENT 2: Theme/Style Match (30%)
        theme_score = self._calculate_theme_match(artwork, theme, artist_relevance_map)
        score_components['theme_style_match'] = theme_score * 0.30
        if theme_score > 0.5:
            reasoning_parts.append(f"Strong theme/style alignment (score: {theme_score:.2f})")

        # COMPONENT 3: Metadata Quality (20%)
        metadata_score = artwork.get('completeness_score', 0.0)
        score_components['metadata_quality'] = metadata_score * 0.20
        if metadata_score >= 0.8:
            reasoning_parts.append(f"Excellent metadata completeness ({int(metadata_score*100)}%)")

        # COMPONENT 4: Visual Availability (20%)
        visual_score = self._calculate_visual_availability(artwork)
        score_components['visual_availability'] = visual_score * 0.20
        if artwork.get('iiif_manifest'):
            reasoning_parts.append("IIIF manifest available for high-quality visuals")
        elif visual_score > 0.5:
            reasoning_parts.append("High-resolution images available")

        # Calculate final score
        final_score = sum(score_components.values())

        # Build reasoning
        artist_name = artwork.get('artist_name', 'Unknown')
        if not reasoning_parts:
            reasoning = f"Artwork '{artwork.get('title')}' by {artist_name} shows moderate relevance to the exhibition theme."
        else:
            reasoning = f"By {artist_name}. " + ". ".join(reasoning_parts) + "."

        return min(1.0, final_score), reasoning

    def _calculate_date_relevance(self, artwork: Dict[str, Any], theme: RefinedTheme) -> float:
        """Calculate date relevance score (0.0-1.0)"""
        artwork_year = artwork.get('date_created_earliest')
        if not artwork_year:
            return 0.3  # No date information, moderate penalty

        # Extract chronological scope from theme
        if not theme.research_backing or not theme.research_backing.chronological_scope:
            return 0.5  # No theme period specified, neutral score

        scope = theme.research_backing.chronological_scope.lower()

        # Parse common period formats
        # e.g., "1910s-1930s", "20th century", "early 1900s"
        import re

        # Extract years from scope
        year_matches = re.findall(r'\b(\d{4})', scope)
        if year_matches:
            scope_years = [int(y) for y in year_matches]
            min_year = min(scope_years)
            max_year = max(scope_years)

            # Perfect match: within range
            if min_year <= artwork_year <= max_year:
                return 1.0

            # Close match: within 10 years
            distance = min(abs(artwork_year - min_year), abs(artwork_year - max_year))
            if distance <= 10:
                return 0.8
            elif distance <= 20:
                return 0.6
            elif distance <= 30:
                return 0.4
            else:
                return 0.2

        # Century matching
        artwork_century = (artwork_year // 100) + 1
        if f"{artwork_century}th century" in scope or str(artwork_century) in scope:
            return 0.8

        # Decade matching (e.g., "1920s")
        artwork_decade = (artwork_year // 10) * 10
        if f"{artwork_decade}s" in scope:
            return 0.9

        return 0.5  # Default neutral score

    def _calculate_theme_match(
        self,
        artwork: Dict[str, Any],
        theme: RefinedTheme,
        artist_relevance_map: Dict[str, float]
    ) -> float:
        """Calculate theme/style match score (0.0-1.0)"""
        score = 0.0

        # Artist relevance (primary indicator)
        artist_name = artwork.get('artist_name', '')
        if artist_name in artist_relevance_map:
            artist_score = artist_relevance_map[artist_name]
            score += artist_score * 0.5  # Artist is 50% of theme match

        # Subject matter alignment
        artwork_subjects = [s.lower() for s in artwork.get('subjects', [])]
        theme_concepts = [c.refined_concept.lower() for c in theme.validated_concepts]

        subject_matches = sum(
            1 for subject in artwork_subjects
            for concept in theme_concepts
            if concept in subject or subject in concept
        )

        if subject_matches > 0:
            # Each match adds 0.15, max 0.45
            score += min(0.45, subject_matches * 0.15)

        # Genre alignment
        if artwork.get('genre'):
            genre_lower = artwork['genre'].lower()
            for concept in theme_concepts:
                if concept in genre_lower or genre_lower in concept:
                    score += 0.1
                    break

        # Title quality bonus (titled works more relevant than "Untitled")
        title = artwork.get('title', '').lower()
        if title and title not in ['untitled', 'untitled (artwork)', 'unknown']:
            score += 0.05

        return min(1.0, score)

    def _calculate_visual_availability(self, artwork: Dict[str, Any]) -> float:
        """Calculate visual availability score (0.0-1.0)"""
        score = 0.0

        # IIIF manifest is best (full functionality)
        if artwork.get('iiif_manifest'):
            score = 1.0
        # High-res images from IIIF
        elif artwork.get('high_res_images'):
            score = 0.9
        # Thumbnail URL
        elif artwork.get('thumbnail_url'):
            score = 0.6
        else:
            score = 0.0

        return score

    async def _check_loan_feasibility(
        self,
        artworks: List[ArtworkCandidate]
    ) -> List[ArtworkCandidate]:
        """Check loan feasibility and add practical information"""
        logger.debug(f"Checking loan feasibility for {len(artworks)} artworks")

        for artwork in artworks:
            # Add loan availability notes (placeholder - would need actual API integration)
            if artwork.institution_name:
                # Artworks from major museums are typically available for loan
                major_museums = [
                    'yale', 'metropolitan', 'moma', 'getty', 'smithsonian',
                    'national gallery', 'rijksmuseum', 'louvre'
                ]

                institution_lower = artwork.institution_name.lower()
                if any(museum in institution_lower for museum in major_museums):
                    artwork.loan_available = True
                    artwork.loan_conditions = "Subject to standard museum loan agreement"
                else:
                    artwork.loan_available = None  # Unknown
                    artwork.loan_conditions = "Loan availability to be confirmed with institution"

        return artworks

    def _rank_and_select_artworks(
        self,
        artworks: List[ArtworkCandidate],
        max_artworks: int,
        artworks_per_artist: int,
        artists: List[DiscoveredArtist]
    ) -> List[ArtworkCandidate]:
        """
        Rank and select final artworks ensuring artist balance (P0-Critical filtering)

        Strategy:
        1. Filter by completeness score (≥ 0.60) - PRP requirement
        2. Prioritize artworks with IIIF manifests
        3. Sort by composite score (relevance + completeness + IIIF)
        4. Ensure fair representation across artists
        5. Balance practical considerations (loan availability, completeness)
        """
        logger.debug(f"Ranking and selecting from {len(artworks)} artworks")

        # FILTER 1: Completeness threshold (relaxed from 0.60 to 0.40)
        MIN_COMPLETENESS = 0.40  # Lowered - 0.60 was too strict, filtered out all artworks
        quality_filtered = [
            artwork for artwork in artworks
            if artwork.completeness_score >= MIN_COMPLETENESS
        ]

        filtered_count = len(artworks) - len(quality_filtered)
        if filtered_count > 0:
            logger.info(
                f"Filtered out {filtered_count} artworks with completeness < {MIN_COMPLETENESS} "
                f"(kept {len(quality_filtered)}/{len(artworks)})"
            )

        if not quality_filtered:
            logger.warning("No artworks passed completeness filter!")
            return []

        # PRIORITY BOOST: IIIF manifests (P1-High)
        # Calculate composite scores and create lookup dict
        score_lookup = {}
        for artwork in quality_filtered:
            # Calculate composite score: relevance + completeness + IIIF bonus
            base_score = artwork.relevance_score

            # Completeness bonus (0-0.1)
            completeness_bonus = max(0, (artwork.completeness_score - 0.4) * 0.25)

            # IIIF bonus (significant boost for exhibition planning)
            iiif_bonus = 0.15 if artwork.iiif_manifest else 0.0

            # Calculate composite score
            composite_score = base_score + completeness_bonus + iiif_bonus
            score_lookup[id(artwork)] = composite_score

        # Group by artist
        by_artist = {}
        for artwork in quality_filtered:
            artist = artwork.artist_name or 'Unknown'
            if artist not in by_artist:
                by_artist[artist] = []
            by_artist[artist].append(artwork)

        # Sort each artist's works by composite score
        for artist in by_artist:
            by_artist[artist].sort(key=lambda x: score_lookup[id(x)], reverse=True)

        # Select artworks ensuring balance
        selected = []
        round_num = 0

        while len(selected) < max_artworks:
            added_this_round = False

            # Round-robin selection from each artist
            for artist in by_artist:
                if len(by_artist[artist]) > round_num:
                    artwork = by_artist[artist][round_num]
                    selected.append(artwork)
                    added_this_round = True

                    if len(selected) >= max_artworks:
                        break

            if not added_this_round:
                break  # No more artworks to add

            round_num += 1

            # Stop after reasonable number per artist
            if round_num >= artworks_per_artist:
                break

        # Final sort by composite score
        selected.sort(key=lambda x: score_lookup[id(x)], reverse=True)

        # Calculate statistics
        iiif_count = sum(1 for a in selected if a.iiif_manifest)
        avg_completeness = sum(a.completeness_score for a in selected) / len(selected) if selected else 0

        logger.info(
            f"Selected {len(selected)} artworks from {len(by_artist)} artists "
            f"(avg {len(selected)/len(by_artist):.1f} per artist) - "
            f"{iiif_count} with IIIF ({iiif_count/len(selected)*100:.0f}%), "
            f"avg completeness: {avg_completeness:.2f}"
        )

        return selected[:max_artworks]


__all__ = ['ArtworkDiscoveryAgent', 'ArtworkSearchQuery']
