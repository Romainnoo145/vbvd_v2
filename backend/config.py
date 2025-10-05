"""
Data Source Configuration for Essential APIs
Provides endpoints, headers, and API keys for all data sources
"""
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()


class DataConfig:
    """Configuration for all essential data sources"""

    def __init__(self):
        # API Keys from environment
        self.brave_api_key = os.getenv('BRAVE_API_KEY')
        self.europeana_api_key = os.getenv('EUROPEANA_API_KEY')

        # User agent for all requests
        self.user_agent = 'AI-Curator-Assistant/1.0 (Educational Project; https://github.com/yourusername/vbvd_agent_v2)'

    def get_endpoint_url(self, source: str, endpoint_type: str, **kwargs) -> str:
        """
        Get endpoint URL for a specific source

        Args:
            source: Data source name
            endpoint_type: Type of endpoint
            **kwargs: Additional parameters (e.g., title for Wikipedia)

        Returns:
            Full endpoint URL
        """
        if source == 'wikipedia':
            if endpoint_type == 'api':
                # Wikipedia MediaWiki API
                return 'https://en.wikipedia.org/w/api.php'
            elif endpoint_type == 'summary':
                # Wikipedia REST API for summaries
                title = kwargs.get('title', '')
                return f'https://en.wikipedia.org/api/rest_v1/page/summary/{title}'

        elif source == 'wikidata':
            if endpoint_type == 'sparql':
                return 'https://query.wikidata.org/sparql'

        elif source == 'getty_vocabularies':
            if endpoint_type == 'sparql':
                return 'http://vocab.getty.edu/sparql'

        elif source == 'yale_lux':
            if endpoint_type == 'search':
                return 'https://lux.collections.yale.edu/api/search'

        elif source == 'brave_search':
            if endpoint_type == 'web':
                return 'https://api.search.brave.com/res/v1/web/search'

        elif source == 'europeana':
            if endpoint_type == 'search':
                return 'https://api.europeana.eu/record/v2/search.json'

        raise ValueError(f"Unknown source/endpoint: {source}/{endpoint_type}")

    def get_headers(self, source: str) -> Dict[str, str]:
        """
        Get HTTP headers for a specific source

        Args:
            source: Data source name

        Returns:
            Dictionary of headers
        """
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        }

        if source == 'brave_search':
            if self.brave_api_key:
                headers['X-Subscription-Token'] = self.brave_api_key
            headers['Accept'] = 'application/json'
            headers['Accept-Encoding'] = 'gzip'

        elif source == 'wikidata' or source == 'getty_vocabularies':
            headers['Accept'] = 'application/sparql-results+json'

        return headers

    def get_api_key(self, source: str) -> Optional[str]:
        """
        Get API key for a specific source

        Args:
            source: Data source name

        Returns:
            API key or None
        """
        if source == 'brave_search':
            return self.brave_api_key
        elif source == 'europeana':
            return self.europeana_api_key

        return None


# Global instance
data_config = DataConfig()
