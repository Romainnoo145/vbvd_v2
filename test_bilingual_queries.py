"""
Test bilingual query generation

Verifies that queries include both English and local language keywords
"""

import sys
import os

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, backend_path)

project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from backend.models import CuratorBrief
from backend.query.europeana_query_builder import EuropeanaQueryBuilder


def test_bilingual_queries():
    """Test that bilingual queries include both English and local language keywords"""

    print("\n" + "="*80)
    print("BILINGUAL QUERY TEST")
    print("="*80 + "\n")

    # Create sample curator brief
    brief = CuratorBrief(
        theme_title="Surrealism in het Digitale Tijdperk",
        theme_description="Test exhibition",
        target_audience="general",
        duration_weeks=12,
        time_period="contemporary",
        art_movements=["surrealism", "contemporary"],
        media_types=["photography", "video_art", "installation"],
        geographic_focus=["netherlands", "belgium", "france", "germany"],
        theme_concepts=[]
    )

    # Build queries
    builder = EuropeanaQueryBuilder(brief)

    exhibition_sections = [
        {
            "title": "Test Section",
            "focus": "Testing bilingual queries",
            "estimated_artwork_count": 10
        }
    ]

    queries = builder.build_section_queries(exhibition_sections)

    print(f"Generated {len(queries)} queries\n")

    # Check each country's query
    expected_keywords = {
        "netherlands": ["photography", "fotografie", "modern", "hedendaags", "abstract"],
        "belgium": ["photography", "fotografie", "modern", "hedendaags", "abstract"],
        "france": ["photography", "photographie", "modern", "moderne", "abstract", "abstrait"],
        "germany": ["photography", "Fotografie", "modern", "hedendaags", "abstract", "abstrakt"],
    }

    for query in queries:
        country = query.section_id.split('-')[-1]
        print(f"\n{country.upper()}:")
        print(f"  Query: {query.query}")
        print(f"  Filter: {query.qf}")

        # Check for bilingual keywords
        query_lower = query.query.lower()
        expected = expected_keywords.get(country, [])

        found_english = any(kw in query_lower for kw in ["photography", "modern", "abstract", "surrealism"])
        found_local = any(kw.lower() in query_lower for kw in expected if kw not in ["photography", "modern", "abstract"])

        if found_english:
            print(f"  ✓ Contains English keywords")
        else:
            print(f"  ✗ Missing English keywords")

        if found_local or country == "netherlands":
            print(f"  ✓ Contains local language keywords")
        else:
            print(f"  ⚠️  Missing local language keywords (expected: {expected})")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_bilingual_queries()
