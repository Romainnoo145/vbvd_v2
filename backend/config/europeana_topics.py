"""
Europeana Topics and Search Term Mapping

This configuration provides prior knowledge about Europeana's topic taxonomy and search terms
to improve search relevance when querying the Europeana API for exhibition curation.

Based on Europeana's Art History Collection and topic categorization.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EuropeanaTopicMapping:
    """Mapping between exhibition themes and Europeana search parameters"""
    topic_id: Optional[int]
    search_terms: List[str]
    art_movements: List[str]
    media_types: List[str]
    time_periods: List[str]
    qf_filters: Dict[str, List[str]]  # Query facet filters


# Main Europeana Topics
EUROPEANA_TOPICS = {
    'art': 190,
    'contemporary_art': 97,
    'fashion': None,  # Has dedicated collection
    'music': None,
    'archaeology': None,
    'newspapers': None,
    'sport': None,
}


# Art Movements recognized by Europeana
ART_MOVEMENTS = {
    # Historical
    'mannerism': ['Mannerism', 'Mannerist'],
    'baroque': ['Baroque', 'Barock'],
    'rococo': ['Rococo', 'Rokoko'],
    'neoclassicism': ['Neo-Classicism', 'Neoclassical', 'Classicism'],
    'romanticism': ['Romanticism', 'Romantic'],

    # 19th Century
    'impressionism': ['Impressionism', 'Impressionist'],
    'post_impressionism': ['Post-Impressionism', 'Post-Impressionist'],
    'symbolism': ['Symbolism', 'Symbolist'],
    'art_nouveau': ['Art Nouveau', 'Jugendstil'],

    # Early 20th Century
    'expressionism': ['Expressionism', 'Expressionist', 'German Expressionism'],
    'cubism': ['Cubism', 'Cubist', 'Analytical Cubism', 'Synthetic Cubism'],
    'futurism': ['Futurism', 'Futurist'],
    'dadaism': ['Dadaism', 'Dada'],
    'surrealism': ['Surrealism', 'Surrealist'],
    'de_stijl': ['De Stijl', 'Neo-Plasticism'],
    'bauhaus': ['Bauhaus', 'Bauhausschule'],

    # Mid-Late 20th Century
    'art_deco': ['Art Deco', 'Art Déco'],
    'abstract_expressionism': ['Abstract Expressionism', 'Action Painting', 'Color Field'],
    'pop_art': ['Pop Art', 'Pop'],
    'minimalism': ['Minimalism', 'Minimalist'],
    'conceptual_art': ['Conceptual Art', 'Conceptualism'],

    # Contemporary
    'contemporary': ['Contemporary Art', 'Contemporary', 'Modern Contemporary'],
}


# Media Types (for proxy_dc_type or proxy_dc_format queries)
MEDIA_TYPES = {
    'painting': ['painting', 'paintings', 'oil painting', 'watercolor', 'acrylic'],
    'sculpture': ['sculpture', 'sculptures', 'statue', 'statues', 'carved', 'sculpted'],
    'drawing': ['drawing', 'drawings', 'sketch', 'sketches'],
    'print': ['print', 'prints', 'etching', 'lithograph', 'woodcut', 'engraving'],
    'photography': ['photography', 'photograph', 'photo', 'photographic'],
    'installation': ['installation', 'installation art', 'assemblage'],
    'mixed_media': ['mixed media', 'multimedia', 'collage'],
    'textile': ['textile', 'tapestry', 'fabric art', 'fiber art'],
    'ceramic': ['ceramic', 'ceramics', 'pottery', 'porcelain'],
    'video_art': ['video art', 'video installation', 'moving image'],
    'performance_art': ['performance art', 'performance', 'happening'],
}


# Time Periods for date filtering (simplified for Van Bommel van Dam focus)
TIME_PERIODS = {
    'contemporary': {'start': 1970, 'end': 2025},  # Hedendaags - Van Bommel core
    'post_war': {'start': 1945, 'end': 1970},      # Na-oorlogs - default
    'early_modern': {'start': 1900, 'end': 1945},  # Modern
    'historical': {'start': 1400, 'end': 1900},    # Historisch (voor musea met oudere collecties)
}


# Predefined exhibition theme mappings
EXHIBITION_THEME_MAPPINGS = {
    'surrealism': EuropeanaTopicMapping(
        topic_id=190,  # Art topic
        search_terms=['surrealism', 'surrealist', 'surreal', 'dream', 'subconscious'],
        art_movements=['Surrealism', 'Surrealist'],
        media_types=['painting', 'sculpture', 'drawing', 'photography', 'print'],
        time_periods=['1920-1945', '1945-1970'],
        qf_filters={
            'proxy_dc_type': ['painting', 'sculpture', 'drawing'],
            'YEAR': ['1920', '1945'],
        }
    ),

    'dutch_modernism': EuropeanaTopicMapping(
        topic_id=190,
        search_terms=['De Stijl', 'Dutch modernism', 'Netherlands modern art', 'Dutch abstract'],
        art_movements=['De Stijl', 'Neo-Plasticism', 'Cubism'],
        media_types=['painting', 'sculpture', 'mixed_media'],
        time_periods=['1910-1940'],
        qf_filters={
            'COUNTRY': ['Netherlands', 'Nederland'],
            'YEAR': ['1910', '1940'],
        }
    ),

    'contemporary_sculpture': EuropeanaTopicMapping(
        topic_id=97,  # Contemporary Art
        search_terms=['contemporary sculpture', 'modern sculpture', '3D art', 'installation'],
        art_movements=['Contemporary Art', 'Minimalism', 'Conceptual Art'],
        media_types=['sculpture', 'installation', 'mixed_media', 'ceramic'],
        time_periods=['1970-2025'],
        qf_filters={
            'proxy_dc_type': ['sculpture', 'installation'],
            'YEAR': ['1970', '2025'],
        }
    ),

    'abstract_expressionism': EuropeanaTopicMapping(
        topic_id=190,
        search_terms=['abstract expressionism', 'action painting', 'color field', 'abstract art'],
        art_movements=['Abstract Expressionism', 'Abstract Art'],
        media_types=['painting', 'drawing', 'print'],
        time_periods=['1945-1970'],
        qf_filters={
            'proxy_dc_type': ['painting'],
            'YEAR': ['1945', '1970'],
        }
    ),

    'photography_modern': EuropeanaTopicMapping(
        topic_id=190,
        search_terms=['modern photography', 'contemporary photography', 'photographic art'],
        art_movements=['Contemporary Art', 'Surrealism', 'Dadaism'],
        media_types=['photography'],
        time_periods=['1920-2025'],
        qf_filters={
            'TYPE': ['IMAGE'],
            'proxy_dc_format': ['photograph', 'photography'],
        }
    ),

    'european_modern_art': EuropeanaTopicMapping(
        topic_id=190,
        search_terms=['European modern art', 'modernism', 'modern art movement'],
        art_movements=['Cubism', 'Expressionism', 'Surrealism', 'Dadaism', 'Futurism'],
        media_types=['painting', 'sculpture', 'drawing', 'print'],
        time_periods=['1900-1970'],
        qf_filters={
            'YEAR': ['1900', '1970'],
        }
    ),

    'installation_art': EuropeanaTopicMapping(
        topic_id=97,
        search_terms=['installation art', 'assemblage', 'environment art', 'spatial art'],
        art_movements=['Contemporary Art', 'Conceptual Art', 'Minimalism'],
        media_types=['installation', 'mixed_media', 'sculpture'],
        time_periods=['1960-2025'],
        qf_filters={
            'proxy_dc_type': ['installation', 'assemblage'],
            'YEAR': ['1960', '2025'],
        }
    ),
}


def get_europeana_search_params(theme_keyword: str) -> Optional[EuropeanaTopicMapping]:
    """
    Get Europeana search parameters for a given theme keyword.

    Args:
        theme_keyword: Exhibition theme keyword (e.g., 'surrealism', 'dutch_modernism')

    Returns:
        EuropeanaTopicMapping object or None if not found
    """
    theme_key = theme_keyword.lower().replace(' ', '_').replace('-', '_')
    return EXHIBITION_THEME_MAPPINGS.get(theme_key)


def find_best_theme_match(description: str) -> Optional[EuropeanaTopicMapping]:
    """
    Find the best matching theme based on exhibition description.

    Args:
        description: Exhibition description or theme text

    Returns:
        Best matching EuropeanaTopicMapping or None
    """
    description_lower = description.lower()

    # Check for direct matches in exhibition themes
    for theme_key, mapping in EXHIBITION_THEME_MAPPINGS.items():
        if theme_key.replace('_', ' ') in description_lower:
            return mapping

        # Check for movement matches
        for movement in mapping.art_movements:
            if movement.lower() in description_lower:
                return mapping

    # Default to European modern art for broad queries
    return EXHIBITION_THEME_MAPPINGS.get('european_modern_art')


def build_europeana_query(
    base_query: str,
    theme: Optional[str] = None,
    media_type: Optional[str] = None,
    time_period: Optional[str] = None,
) -> Dict[str, any]:
    """
    Build enhanced Europeana API query parameters with theme-based filtering.

    Args:
        base_query: Base search query (artist name, artwork title, etc.)
        theme: Exhibition theme keyword
        media_type: Specific media type filter
        time_period: Time period keyword

    Returns:
        Dictionary of API parameters including query and qf filters
    """
    params = {
        'query': base_query,
        'qf': []
    }

    # Add theme-based filters
    if theme:
        mapping = get_europeana_search_params(theme)
        if mapping:
            # Add movement filters
            if mapping.art_movements:
                movement_filter = ' OR '.join([f'"{m}"' for m in mapping.art_movements])
                params['query'] += f' AND ({movement_filter})'

            # Add qf filters
            for field, values in mapping.qf_filters.items():
                for value in values:
                    params['qf'].append(f'{field}:{value}')

    # Add media type filter
    if media_type and media_type.lower() in MEDIA_TYPES:
        media_terms = MEDIA_TYPES[media_type.lower()]
        for term in media_terms[:3]:  # Use top 3 terms
            params['qf'].append(f'proxy_dc_type.en:"{term}"')

    # Add time period filter
    if time_period and time_period.lower() in TIME_PERIODS:
        period = TIME_PERIODS[time_period.lower()]
        params['qf'].append(f'YEAR:[{period["start"]} TO {period["end"]}]')

    return params


# Export main components
__all__ = [
    'EUROPEANA_TOPICS',
    'ART_MOVEMENTS',
    'MEDIA_TYPES',
    'TIME_PERIODS',
    'EXHIBITION_THEME_MAPPINGS',
    'EuropeanaTopicMapping',
    'get_europeana_search_params',
    'find_best_theme_match',
    'build_europeana_query',
]
