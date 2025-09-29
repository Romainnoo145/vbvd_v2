"""
Backend Configuration Module
Handles all configuration for the AI Curator Assistant
"""

from .data_sources import (
    EssentialDataConfig,
    data_config,
    validate_api_access
)

__all__ = [
    'EssentialDataConfig',
    'data_config',
    'validate_api_access'
]