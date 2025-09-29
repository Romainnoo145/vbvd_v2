#!/usr/bin/env python3
"""
Test script to verify Essential Data Sources Configuration
Run this to ensure all configurations are working correctly
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.config import data_config, validate_api_access


def test_configuration():
    """Test the essential data sources configuration"""

    print("=" * 60)
    print("AI CURATOR ASSISTANT - Configuration Test")
    print("=" * 60)

    # 1. Validate API access
    print("\n1. Validating API Configuration:")
    print("-" * 40)
    validate_api_access()

    # 2. Check all 5 essential sources
    print("\n2. Essential Data Sources:")
    print("-" * 40)
    for service, config in data_config.SOURCES.items():
        print(f"\n✅ {service.upper()}")
        print(f"   Cost: {config['cost']}")
        print(f"   Note: {config['note']}")
        if 'features' in config:
            print(f"   Features: {', '.join(config['features'][:3])}...")

    # 3. Test endpoint URL construction
    print("\n3. Testing Endpoint URL Construction:")
    print("-" * 40)

    test_urls = [
        ('wikipedia', 'summary', {'title': 'Leonardo da Vinci'}),
        ('wikidata', 'entity', {'id': 'Q762'}),
        ('getty_vocabularies', 'rest', {'vocabulary': 'aat', 'id': '300015045'}),
        ('yale_lux', 'object', {'id': '466b3d09-2fb1-45e8-a5c5-b54749495e97'}),
        ('brave_search', 'web', {})
    ]

    for service, endpoint_type, params in test_urls:
        url = data_config.get_endpoint_url(service, endpoint_type, **params)
        if url:
            print(f"   ✓ {service}: {url[:80]}...")
        else:
            print(f"   ✗ {service}: Failed to construct URL")

    # 4. Check headers
    print("\n4. Testing Service Headers:")
    print("-" * 40)
    for service in ['wikipedia', 'wikidata', 'getty_vocabularies', 'yale_lux', 'brave_search']:
        headers = data_config.get_headers(service)
        print(f"   {service}: {len(headers)} headers configured")

    # 5. Check SPARQL prefixes
    print("\n5. SPARQL Prefixes:")
    print("-" * 40)
    prefixes = data_config.get_sparql_prefixes()
    prefix_count = len([line for line in prefixes.strip().split('\n') if line.strip().startswith('PREFIX')])
    print(f"   {prefix_count} SPARQL prefixes configured")

    # 6. Summary
    print("\n" + "=" * 60)
    print("CONFIGURATION TEST COMPLETE")
    print("=" * 60)

    validation = data_config.validate_configuration()
    ready_count = sum(1 for v in validation.values() if v)
    total_count = len(validation)

    print(f"\n📊 Status: {ready_count}/{total_count} services ready")

    if ready_count == total_count:
        print("✅ All essential services configured successfully!")
    else:
        missing = [s for s, v in validation.items() if not v]
        print(f"⚠️  Missing configuration for: {', '.join(missing)}")
        print("\n💡 Tip: Copy .env.example to .env and add your API keys")

    return ready_count == total_count


if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)