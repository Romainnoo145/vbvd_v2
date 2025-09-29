"""
Backend Clients Module
HTTP clients for external services
"""

from .essential_data_client import (
    EssentialDataClient,
    search_all_sources
)

__all__ = [
    'EssentialDataClient',
    'search_all_sources'
]