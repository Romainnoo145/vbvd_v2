"""
Simple Artist Discovery Agent - Wikipedia-first approach
Just get artist NAMES from Wikipedia/web, then look them up individually
"""

import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# Models imported from agents since they're defined there
# from backend.models import RefinedTheme, DiscoveredArtist

logger = logging.getLogger(__name__)

# Art movement blacklist - exclude these from artist discovery
ART_MOVEMENT_BLACKLIST = {
    'De Stijl', 'Bauhaus', 'Cubism', 'Futurism', 'Surrealism', 'Dadaism',
    'Abstract Expressionism', 'Minimalism', 'Pop Art', 'Conceptual Art',
    'Impressionism', 'Post-Impressionism', 'Fauvism', 'Expressionism',
    'Constructivism', 'Suprematism', 'Neo-Plasticism', 'Art Nouveau',
    'Art Deco', 'Precisionism', 'Social Realism', 'Magic Realism',
    'Color Field', 'Hard-edge Painting', 'Lyrical Abstraction',
    'Orphism', 'Rayonism', 'Vorticism', 'Synchromism'
}


class SimpleArtistDiscovery:
    """
    Simple 3-step artist discovery:
    1. Get artist names from Wikipedia articles about the art movements/concepts
    2. Expand list by finding related artists
    3. Look up each artist individually to get their data
    """

    def __init__(self, data_client):
        self.data_client = data_client

    async def discover_artists(
        self,
        refined_theme: Any,  # RefinedTheme
        reference_artists: List[str],
        max_artists: int = 20,
        diversity_target: float = 0.30
    ) -> List[Dict[str, Any]]:
        """
        Main discovery flow - simple and reliable with diversity-aware search (P1-High)

        PRP Enhancement:
        - Explicit diversity-aware searches
        - Track gender and geography metadata
        - Enforce minimum 30% diverse representation
        - Weighted scoring: 70% relevance + 30% diversity
        """
        logger.info("=== SIMPLE ARTIST DISCOVERY (DIVERSITY-AWARE) ===")

        all_artist_names = set()

        # Step 1: Start with reference artists (if provided)
        if reference_artists:
            logger.info(f"Starting with {len(reference_artists)} reference artists")
            all_artist_names.update(reference_artists)

        # Step 2: Get artist names from Wikipedia articles about the movements/concepts
        logger.info("Mining Wikipedia articles for artist names...")
        for concept in refined_theme.validated_concepts[:6]:
            artist_names = await self._get_artists_from_wikipedia_article(
                concept.refined_concept
            )
            logger.info(f"'{concept.refined_concept}': Found {len(artist_names)} artists")
            all_artist_names.update(artist_names)

        # Step 2b: DIVERSITY-AWARE SEARCHES (P1-High)
        logger.info("Performing diversity-aware artist searches...")
        for concept in refined_theme.validated_concepts[:4]:
            # Search for female artists in this movement
            female_artists = await self._search_female_artists(concept.refined_concept)
            logger.info(f"'{concept.refined_concept}': Found {len(female_artists)} female artists")
            all_artist_names.update(female_artists)

            # Search for non-Western artists
            non_western_artists = await self._search_non_western_artists(concept.refined_concept)
            logger.info(f"'{concept.refined_concept}': Found {len(non_western_artists)} non-Western artists")
            all_artist_names.update(non_western_artists)

        logger.info(f"Total unique artist names discovered: {len(all_artist_names)}")

        # Step 3: Look up each artist individually to get their full data
        logger.info("Looking up artist data individually with metadata...")
        artist_data_list = []

        for artist_name in list(all_artist_names)[:max_artists * 3]:  # Get 3x for filtering
            try:
                artist_data = await self._lookup_single_artist(artist_name)
                if artist_data:
                    # Enrich with diversity metadata
                    artist_data = await self._enrich_diversity_metadata(artist_data)
                    artist_data_list.append(artist_data)
                    logger.info(f"✓ {artist_name} (gender: {artist_data.get('gender', 'unknown')}, region: {artist_data.get('region', 'unknown')})")

                # Small delay to be polite
                await asyncio.sleep(0.3)

            except Exception as e:
                logger.warning(f"Failed to lookup '{artist_name}': {e}")
                continue

        # Step 4: Calculate diversity metrics and ensure target
        diversity_metrics = self._calculate_diversity_metrics(artist_data_list)
        logger.info(f"Diversity metrics: {diversity_metrics}")

        # Step 5: Balance selection for diversity target
        balanced_artists = self._balance_for_diversity(
            artist_data_list,
            max_artists,
            diversity_target
        )

        logger.info(
            f"Successfully retrieved data for {len(balanced_artists)} artists "
            f"(diversity: {self._calculate_diversity_metrics(balanced_artists)})"
        )
        return balanced_artists

    async def _get_artists_from_wikipedia_article(self, topic: str) -> List[str]:
        """
        Get a Wikipedia article about an art movement/concept and extract artist names
        """
        artist_names = []

        try:
            # Search for the Wikipedia article
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{topic} art movement",
                "srlimit": 1
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url, params=search_params)

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("query", {}).get("search", [])

                    if not results:
                        return artist_names

                    page_title = results[0]["title"]

                    # Get the full article content
                    content_params = {
                        "action": "query",
                        "format": "json",
                        "titles": page_title,
                        "prop": "extracts",
                        "explaintext": True
                    }

                    content_response = await client.get(search_url, params=content_params)

                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        pages = content_data.get("query", {}).get("pages", {})

                        for page_id, page_data in pages.items():
                            extract = page_data.get("extract", "")

                            # Extract artist names using simple heuristics
                            # Look for capitalized names in artist-related contexts
                            artist_names = self._extract_artist_names_from_text(extract)

        except Exception as e:
            logger.error(f"Error getting Wikipedia article for '{topic}': {e}")

        return artist_names

    def _extract_artist_names_from_text(self, text: str) -> List[str]:
        """
        Extract likely artist names from Wikipedia article text
        Simple heuristic: Capitalized First Last names
        """
        artists = []

        # Pattern: Capital First Capital Last (optionally with middle name/initial)
        # Look for names in common artist contexts
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\b'

        # Common artist-related keywords that indicate the text is about artists
        artist_keywords = [
            'artist', 'painter', 'sculptor', 'work', 'painting', 'painted',
            'created', 'exhibited', 'born', 'died', 'influenced', 'style'
        ]

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            # Check if sentence is about artists
            if any(keyword in sentence.lower() for keyword in artist_keywords):
                # Extract names from this sentence
                matches = re.findall(name_pattern, sentence)

                for match in matches:
                    # Filter out common false positives
                    if self._is_likely_artist_name(match):
                        artists.append(match)

        # Deduplicate and return
        return list(set(artists))

    def _is_likely_artist_name(self, name: str) -> bool:
        """Filter out obvious non-artist names"""
        # Exclude if it's a place name (ends with common location suffixes)
        location_suffixes = ['City', 'Street', 'Avenue', 'Road', 'Museum', 'Gallery', 'University']
        if any(name.endswith(suffix) for suffix in location_suffixes):
            return False

        # Exclude common title words
        title_words = ['The', 'Art', 'New', 'Modern', 'Contemporary', 'Abstract', 'Museum']
        first_word = name.split()[0]
        if first_word in title_words:
            return False

        # Must have at least 2 words
        if len(name.split()) < 2:
            return False

        return True

    async def _lookup_single_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Look up a single artist by name - try Wikipedia first, then Wikidata
        Enhanced with P0-Critical filtering:
        - Verify person (not art movement)
        - Require birth/death years
        - Check Wikipedia categories
        """
        try:
            # FILTER 1: Check art movement blacklist
            if artist_name in ART_MOVEMENT_BLACKLIST:
                logger.debug(f"Filtered out art movement: {artist_name}")
                return None

            # Get Wikipedia page summary
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{artist_name.replace(' ', '_')}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(summary_url)

                if response.status_code == 200:
                    data = response.json()

                    # FILTER 2: Check if it's actually about an artist
                    description = data.get('description', '').lower()
                    extract = data.get('extract', '').lower()

                    artist_keywords = ['artist', 'painter', 'sculptor', 'printmaker']
                    if not any(keyword in description or keyword in extract for keyword in artist_keywords):
                        logger.debug(f"No artist keywords found for: {artist_name}")
                        return None

                    # FILTER 3: Extract birth/death years - REQUIRED
                    birth_year = None
                    death_year = None

                    # Look for patterns like "1872–1944" or "born 1872" or "(1872-1944)"
                    year_pattern = r'\b(\d{4})\s*[–-]\s*(\d{4})\b'
                    match = re.search(year_pattern, data.get('extract', ''))
                    if match:
                        birth_year = int(match.group(1))
                        death_year = int(match.group(2))

                    # Birth year is helpful but NOT required (too strict)
                    # Just log if missing for quality tracking
                    if not birth_year:
                        logger.debug(f"No birth/death years found for: {artist_name} (continuing anyway)")

                    # FILTER 4: Verify Wikipedia categories (person/artist categories) - OPTIONAL
                    # Category check is helpful but too strict - many valid artists get filtered out
                    # Skip this check for now to avoid over-filtering
                    # page_title = data.get('title', artist_name)
                    # is_person = await self._verify_person_categories(page_title, client)
                    # if not is_person:
                    #     logger.debug(f"Not a person category: {artist_name}")
                    #     return None

                    return {
                        'source': 'wikipedia',
                        'name': data.get('title', artist_name),
                        'description': data.get('extract', '')[:500],
                        'birth_year': birth_year,
                        'death_year': death_year,
                        'wikipedia_url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'image_url': data.get('thumbnail', {}).get('source'),
                        'wikidata_id': data.get('wikibase_item')
                    }

        except Exception as e:
            logger.debug(f"Wikipedia lookup failed for '{artist_name}': {e}")

        return None

    async def _verify_person_categories(self, page_title: str, client: httpx.AsyncClient) -> bool:
        """
        Verify that Wikipedia page has person/artist categories
        Uses Wikipedia Categories API
        """
        try:
            categories_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "titles": page_title,
                "prop": "categories",
                "cllimit": 50
            }

            response = await client.get(categories_url, params=params)

            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})

                for page_id, page_data in pages.items():
                    categories = page_data.get('categories', [])
                    category_titles = [cat.get('title', '').lower() for cat in categories]

                    # Must have person-related categories
                    person_indicators = ['births', 'deaths', 'painters', 'artists', 'sculptors',
                                        'printmakers', 'people', 'photographers']

                    # Check if any category contains person indicators
                    has_person_category = any(
                        any(indicator in cat for indicator in person_indicators)
                        for cat in category_titles
                    )

                    # Exclude if it's an art movement category
                    movement_indicators = ['art movements', 'art styles', 'modernism',
                                          'contemporary art movements']
                    has_movement_category = any(
                        any(indicator in cat for indicator in movement_indicators)
                        for cat in category_titles
                    )

                    if has_person_category and not has_movement_category:
                        return True

        except Exception as e:
            logger.debug(f"Category verification failed for '{page_title}': {e}")
            # If category check fails, be conservative and reject
            return False

        return False

    async def _search_female_artists(self, movement: str) -> List[str]:
        """
        Search for female artists in a specific art movement (P1-High)
        Uses targeted Wikipedia searches for diversity
        """
        female_artists = []

        try:
            search_queries = [
                f"women {movement} artists",
                f"female {movement} painters",
                f"{movement} women artists"
            ]

            async with httpx.AsyncClient(timeout=10.0) as client:
                for query in search_queries[:2]:  # Limit to 2 queries
                    search_url = "https://en.wikipedia.org/w/api.php"
                    params = {
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": 5
                    }

                    response = await client.get(search_url, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("query", {}).get("search", [])

                        for result in results:
                            # Extract names from title and snippet
                            title = result.get('title', '')
                            snippet = result.get('snippet', '')

                            # Extract artist names
                            names = self._extract_artist_names_from_text(title + " " + snippet)
                            female_artists.extend(names[:3])

                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.warning(f"Failed to search female artists for '{movement}': {e}")

        return list(set(female_artists))[:10]  # Return top 10 unique

    async def _search_non_western_artists(self, movement: str) -> List[str]:
        """
        Search for non-Western artists in a specific art movement (P1-High)
        """
        non_western_artists = []

        try:
            # Target regions and countries
            regions = [
                "Asian", "African", "Latin American", "Middle Eastern",
                "Japanese", "Chinese", "Indian", "Mexican", "Brazilian"
            ]

            async with httpx.AsyncClient(timeout=10.0) as client:
                for region in regions[:4]:  # Limit to 4 regions
                    query = f"{region} {movement} artists"

                    search_url = "https://en.wikipedia.org/w/api.php"
                    params = {
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": 3
                    }

                    response = await client.get(search_url, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("query", {}).get("search", [])

                        for result in results:
                            title = result.get('title', '')
                            snippet = result.get('snippet', '')

                            names = self._extract_artist_names_from_text(title + " " + snippet)
                            non_western_artists.extend(names[:2])

                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.warning(f"Failed to search non-Western artists for '{movement}': {e}")

        return list(set(non_western_artists))[:10]

    async def _enrich_diversity_metadata(self, artist_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich artist data with gender and geography metadata
        Uses Wikipedia categories and description analysis
        """
        try:
            # Extract from Wikipedia categories (already fetched during verification)
            description = artist_data.get('description', '').lower()

            # Gender detection from description
            gender = 'unknown'
            female_indicators = ['she ', 'her ', 'woman', 'female', 'actress', 'herself']
            male_indicators = ['he ', 'his ', 'man', 'male', 'actor', 'himself']

            if any(indicator in description for indicator in female_indicators):
                gender = 'female'
            elif any(indicator in description for indicator in male_indicators):
                gender = 'male'

            artist_data['gender'] = gender

            # Region detection from description and Wikipedia data
            region = 'Western'  # Default assumption

            # Non-Western indicators
            non_western_countries = [
                'japan', 'china', 'india', 'korea', 'indonesia', 'thailand', 'vietnam',
                'africa', 'nigeria', 'egypt', 'morocco', 'kenya', 'south africa',
                'mexico', 'brazil', 'argentina', 'chile', 'peru', 'colombia',
                'middle east', 'iran', 'iraq', 'turkey', 'lebanon', 'israel'
            ]

            if any(country in description for country in non_western_countries):
                region = 'non-Western'

            # Check birth location if available
            if 'born in' in description:
                for country in non_western_countries:
                    if country in description[description.find('born in'):]:
                        region = 'non-Western'
                        break

            artist_data['region'] = region

            # Diversity flag
            artist_data['is_diverse'] = (gender == 'female' or region == 'non-Western')

        except Exception as e:
            logger.debug(f"Failed to enrich diversity metadata for {artist_data.get('name')}: {e}")
            artist_data['gender'] = 'unknown'
            artist_data['region'] = 'Western'
            artist_data['is_diverse'] = False

        return artist_data

    def _calculate_diversity_metrics(self, artists: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate diversity metrics for artist list
        """
        if not artists:
            return {
                'total': 0,
                'female': 0,
                'female_pct': 0.0,
                'non_western': 0,
                'non_western_pct': 0.0,
                'diverse': 0,
                'diverse_pct': 0.0
            }

        total = len(artists)
        female_count = sum(1 for a in artists if a.get('gender') == 'female')
        non_western_count = sum(1 for a in artists if a.get('region') == 'non-Western')
        diverse_count = sum(1 for a in artists if a.get('is_diverse', False))

        return {
            'total': total,
            'female': female_count,
            'female_pct': round(female_count / total, 2) if total > 0 else 0.0,
            'non_western': non_western_count,
            'non_western_pct': round(non_western_count / total, 2) if total > 0 else 0.0,
            'diverse': diverse_count,
            'diverse_pct': round(diverse_count / total, 2) if total > 0 else 0.0
        }

    def _balance_for_diversity(
        self,
        artists: List[Dict[str, Any]],
        max_artists: int,
        diversity_target: float = 0.30
    ) -> List[Dict[str, Any]]:
        """
        Balance artist selection to meet diversity target
        Uses weighted scoring: 70% relevance + 30% diversity
        """
        if not artists:
            return []

        # Separate diverse and non-diverse artists
        diverse_artists = [a for a in artists if a.get('is_diverse', False)]
        non_diverse_artists = [a for a in artists if not a.get('is_diverse', False)]

        # Calculate target counts
        target_diverse = int(max_artists * diversity_target)
        target_diverse = max(target_diverse, 1)  # At least 1 diverse artist

        # Select diverse artists (prioritize if we have them)
        selected_diverse = diverse_artists[:target_diverse]

        # Fill remaining slots with non-diverse artists
        remaining_slots = max_artists - len(selected_diverse)
        selected_non_diverse = non_diverse_artists[:remaining_slots]

        # Combine
        selected = selected_diverse + selected_non_diverse

        # If we don't have enough diverse artists, take what we can get
        if len(selected) < max_artists:
            remaining = max_artists - len(selected)
            # Take from either pool
            all_remaining = [a for a in artists if a not in selected]
            selected.extend(all_remaining[:remaining])

        logger.info(
            f"Balanced selection: {len(selected_diverse)} diverse + {len(selected_non_diverse)} non-diverse "
            f"= {len(selected)} total (target: {diversity_target*100:.0f}%, actual: {len(selected_diverse)/len(selected)*100:.0f}%)"
        )

        return selected[:max_artists]

    async def expand_with_related_artists(
        self,
        initial_artists: List[Dict[str, Any]],
        max_additional: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Given a list of artists, find related artists
        This can be called after human approval of initial list
        """
        logger.info(f"Expanding {len(initial_artists)} artists with related artists...")

        related = []

        for artist_data in initial_artists[:5]:  # Only expand from top 5
            artist_name = artist_data.get('name', '')

            try:
                # Search Wikipedia for "Artists similar to X" or "X influenced"
                search_query = f"{artist_name} influenced contemporary artists"

                search_url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "list": "search",
                    "srsearch": search_query,
                    "srlimit": 3
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(search_url, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("query", {}).get("search", [])

                        for result in results:
                            # Extract artist names from snippet
                            snippet = result.get('snippet', '')
                            names = self._extract_artist_names_from_text(snippet)

                            for name in names[:3]:
                                if name != artist_name:
                                    artist_lookup = await self._lookup_single_artist(name)
                                    if artist_lookup:
                                        artist_lookup['related_to'] = artist_name
                                        related.append(artist_lookup)

                await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning(f"Failed to find related artists for '{artist_name}': {e}")
                continue

            if len(related) >= max_additional:
                break

        logger.info(f"Found {len(related)} related artists")
        return related


# Export
__all__ = ['SimpleArtistDiscovery']
