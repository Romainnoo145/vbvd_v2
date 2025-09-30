"""
Essential Data Sources Configuration
Configuration for the 5 essential APIs used by the AI Curator Assistant
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class EssentialDataConfig:
    """Configuration for essential data sources (4 free + 1 paid)"""

    # Core APIs - 4 FREE + 1 PAID
    SOURCES: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'wikipedia': {
            'api': 'https://en.wikipedia.org/w/api.php',
            'summary': 'https://en.wikipedia.org/api/rest_v1/page/summary/{title}',
            'extract': 'https://en.wikipedia.org/api/rest_v1/page/extract/{title}',
            'cost': 'Free',
            'rate_limit': None,  # No official rate limit, but be respectful
            'note': 'Comprehensive art historical context',
            'features': [
                'Full text search',
                'Page summaries',
                'Extract content',
                'Multi-language support'
            ]
        },
        'wikidata': {
            'sparql': 'https://query.wikidata.org/sparql',
            'api': 'https://www.wikidata.org/w/api.php',
            'entity': 'https://www.wikidata.org/wiki/Special:EntityData/{id}.json',
            'cost': 'Free',
            'rate_limit': 'Reasonable use expected',
            'note': 'Structured data for artists and artworks',
            'features': [
                'SPARQL endpoint',
                'Structured entity data',
                'Cross-referenced identifiers',
                'Multilingual labels'
            ]
        },
        'getty_vocabularies': {
            'sparql': 'http://vocab.getty.edu/sparql.json',
            'aat_rest': 'http://vocab.getty.edu/aat/{id}.json',
            'ulan_rest': 'http://vocab.getty.edu/ulan/{id}.json',
            'tgn_rest': 'http://vocab.getty.edu/tgn/{id}.json',
            'search_aat': 'http://vocab.getty.edu/aat/search.json',
            'search_ulan': 'http://vocab.getty.edu/ulan/search.json',
            'cost': 'Free',
            'rate_limit': None,
            'status': 'OPTIONAL - SPARQL endpoint has reliability issues',
            'note': 'Professional art historical terminology - CURRENTLY DISABLED due to SPARQL query limitations. System uses Wikidata as primary authority instead.',
            'vocabularies': {
                'aat': 'Art & Architecture Thesaurus',
                'ulan': 'Union List of Artist Names',
                'tgn': 'Thesaurus of Geographic Names'
            }
        },
        'yale_lux': {
            'base': 'https://lux.collections.yale.edu/',
            'api_base': 'https://lux.collections.yale.edu/api/',
            'search': 'https://lux.collections.yale.edu/api/search',
            'sparql': 'https://lux.collections.yale.edu/api/sparql',
            'entity_patterns': {
                'object': 'data/object/{id}',
                'person': 'data/person/{id}',
                'place': 'data/place/{id}',
                'event': 'data/event/{id}',
                'set': 'data/set/{id}',
                'group': 'data/group/{id}',
                'concept': 'data/concept/{id}'
            },
            'cost': 'Free',
            'rate_limit': 'Be respectful',
            'note': 'High-quality Linked Art implementation',
            'features': [
                'Full Linked Art API',
                'Activity Streams search',
                'SPARQL endpoint',
                'IIIF manifests'
            ]
        },
        'brave_search': {
            'url': 'https://api.search.brave.com/res/v1/web/search',
            'images_url': 'https://api.search.brave.com/res/v1/images/search',
            'news_url': 'https://api.search.brave.com/res/v1/news/search',
            'cost': 'Paid (~$5/month for 2000 queries)',
            'rate_limit': '1 request per second',
            'note': 'Essential for current web intelligence',
            'features': [
                'Web search',
                'Image search',
                'News search',
                'SafeSearch',
                'Freshness control'
            ]
        }
    })

    # Fallback sources (optional, for future expansion)
    FALLBACK_SOURCES: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'rkd': {
            'sparql': 'https://data.rkd.nl/sparql',
            'api': 'https://api.rkd.nl/api/record/',
            'cost': 'Free',
            'note': 'Fallback for Dutch art history'
        },
        'europeana': {
            'api': 'https://api.europeana.eu/record/v2/',
            'search': 'https://api.europeana.eu/record/v2/search.json',
            'cost': 'Free with API key',
            'note': 'European cultural heritage'
        }
    })

    # API Configuration
    @staticmethod
    def get_api_key(service: str) -> Optional[str]:
        """Get API key from environment variables"""
        key_mapping = {
            'brave_search': 'BRAVE_API_KEY',
            'europeana': 'EUROPEANA_API_KEY',
            'serpapi': 'SERPAPI_KEY'  # For potential Google Scholar integration
        }

        env_var = key_mapping.get(service)
        if env_var:
            return os.getenv(env_var)
        return None

    @staticmethod
    def get_headers(service: str) -> Dict[str, str]:
        """Get required headers for a service"""
        headers = {
            'User-Agent': 'AI-Curator-Assistant/1.0 (https://github.com/klarifai/vbvd_agent_v2)',
            'Accept': 'application/json'
        }

        if service == 'brave_search':
            api_key = EssentialDataConfig.get_api_key('brave_search')
            if api_key:
                headers['X-Subscription-Token'] = api_key

        elif service in ['wikidata', 'getty_vocabularies']:
            headers['Accept'] = 'application/sparql-results+json'

        elif service == 'yale_lux':
            headers['Accept'] = 'application/ld+json;profile="https://linked.art/ns/v1/linked-art.json"'

        return headers

    @staticmethod
    def get_sparql_prefixes() -> str:
        """Common SPARQL prefixes for queries"""
        return """
        PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
        PREFIX la: <https://linked.art/ns/terms/>
        PREFIX aat: <http://vocab.getty.edu/aat/>
        PREFIX ulan: <http://vocab.getty.edu/ulan/>
        PREFIX tgn: <http://vocab.getty.edu/tgn/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        """

    @classmethod
    def validate_configuration(cls) -> Dict[str, bool]:
        """Validate that required API keys are present"""
        validation = {
            'wikipedia': True,  # No key required
            'wikidata': True,   # No key required
            'getty_vocabularies': True,  # No key required
            'yale_lux': True,   # No key required
            'brave_search': cls.get_api_key('brave_search') is not None
        }

        return validation

    @classmethod
    def get_endpoint_url(cls, service: str, endpoint_type: str, **kwargs) -> str:
        """Construct endpoint URL with parameters"""
        # Create an instance to access the dataclass field
        instance = cls()
        config = instance.SOURCES.get(service, {})

        if service == 'wikipedia':
            if endpoint_type == 'summary':
                title = kwargs.get('title', '').replace(' ', '_')
                return config['summary'].format(title=title)
            elif endpoint_type == 'extract':
                title = kwargs.get('title', '').replace(' ', '_')
                return config['extract'].format(title=title)
            else:
                return config['api']

        elif service == 'wikidata':
            if endpoint_type == 'entity':
                entity_id = kwargs.get('id', '')
                return config['entity'].format(id=entity_id)
            elif endpoint_type == 'sparql':
                return config['sparql']
            else:
                return config['api']

        elif service == 'getty_vocabularies':
            vocabulary = kwargs.get('vocabulary', 'aat')
            if endpoint_type == 'rest':
                entity_id = kwargs.get('id', '')
                return config[f'{vocabulary}_rest'].format(id=entity_id)
            elif endpoint_type == 'search':
                return config[f'search_{vocabulary}']
            else:
                return config['sparql']

        elif service == 'yale_lux':
            if endpoint_type in config['entity_patterns']:
                entity_id = kwargs.get('id', '')
                pattern = config['entity_patterns'][endpoint_type]
                return f"{config['api_base']}{pattern.format(id=entity_id)}"
            elif endpoint_type == 'sparql':
                return config['sparql']
            else:
                return config['search']

        elif service == 'brave_search':
            if endpoint_type == 'images':
                return config['images_url']
            elif endpoint_type == 'news':
                return config['news_url']
            else:
                return config['url']

        return ''


# Create singleton instance
data_config = EssentialDataConfig()


# Validation helper
def validate_api_access() -> None:
    """Validate API configuration on module import"""
    validation = data_config.validate_configuration()

    missing_keys = [service for service, valid in validation.items() if not valid]

    if missing_keys:
        print(f"⚠️  Warning: Missing API keys for: {', '.join(missing_keys)}")
        print(f"   Please set the following environment variables:")
        for service in missing_keys:
            if service == 'brave_search':
                print(f"   - BRAVE_API_KEY")
    else:
        print("✅ All essential API configurations validated successfully")


# Export configuration
__all__ = ['EssentialDataConfig', 'data_config', 'validate_api_access']