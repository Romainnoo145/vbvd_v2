"""
Test EuropeanaQueryBuilder with actual theme refinement output
"""

import sys
import json
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.query.europeana_query_builder import EuropeanaQueryBuilder
from backend.models import CuratorBrief

# Actual theme refinement output from our demo session
theme_data = {
    "exhibition_title": "Surrealisme in het Digitale Tijdperk",
    "subtitle": "De invloed van surrealistische principes op digitale kunst",
    "exhibition_sections": [
        {
            "title": "Dromen in Pixels",
            "focus": "Exploring the creation of dreamlike landscapes in digital art.",
            "artist_emphasis": ["Rafik Anadol", "Janelle Shane"],
            "estimated_artwork_count": 8
        },
        {
            "title": "De Absurditeit van het Algoritme",
            "focus": "Investigating how algorithms can produce surreal and unexpected outcomes.",
            "artist_emphasis": ["Mario Klingemann", "Anna Ridler"],
            "estimated_artwork_count": 10
        },
        {
            "title": "Het Onbewuste en de Virtuele Ruimte",
            "focus": "Examining the intersection of the unconscious mind and virtual realities.",
            "artist_emphasis": ["Casey Reas", "Sougwen Chung"],
            "estimated_artwork_count": 8
        }
    ]
}

# Actual form input from demo
curator_brief = CuratorBrief(
    theme_title="Surrealisme in het Digitale Tijdperk",
    theme_description="Een tentoonstelling die de invloed van surrealistische principes op hedendaagse digitale kunst onderzoekt.",
    art_movements=["surrealism", "contemporary"],
    media_types=["photography", "video_art", "installation"],
    time_period="contemporary",
    geographic_focus=["Netherlands", "Belgium", "Germany", "France"],
    target_audience="general",
    duration_weeks=16
)

def main():
    print("=" * 80)
    print("TESTING EUROPEANA QUERY BUILDER")
    print("=" * 80)
    print()

    # Initialize QueryBuilder
    query_builder = EuropeanaQueryBuilder(curator_brief)

    # Build queries from exhibition sections
    queries = query_builder.build_section_queries(theme_data['exhibition_sections'])

    print(f"✓ Generated {len(queries)} queries from {len(theme_data['exhibition_sections'])} sections")
    print()

    # Display results
    for i, query in enumerate(queries, 1):
        print(f"{'=' * 80}")
        print(f"SECTION {i}: {query.section_title}")
        print(f"{'=' * 80}")
        print(f"Focus: {theme_data['exhibition_sections'][i-1]['focus']}")
        print()
        print(f"Main Query: {query.query}")
        print()
        print(f"Filters ({len(query.qf)}):")
        for filter_str in query.qf:
            print(f"  - {filter_str}")
        print()
        print(f"Rows: {query.rows}")
        print(f"Section ID: {query.section_id}")
        print()

    # Export as JSON
    queries_json = [q.model_dump() for q in queries]

    print("=" * 80)
    print("JSON OUTPUT (for API integration)")
    print("=" * 80)
    print(json.dumps(queries_json, indent=2))
    print()

    # Validation checks
    print("=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    all_valid = True
    for query in queries:
        # Check 1: Main query has content
        if not query.query or len(query.query) < 10:
            print(f"❌ Section '{query.section_title}': Query too short")
            all_valid = False
        else:
            print(f"✓ Section '{query.section_title}': Query has {len(query.query.split())} terms")

        # Check 2: Has filters
        if not query.qf:
            print(f"❌ Section '{query.section_title}': No filters")
            all_valid = False
        else:
            print(f"✓ Section '{query.section_title}': {len(query.qf)} filters applied")

        # Check 3: Has TYPE:IMAGE filter
        has_type = any('TYPE:IMAGE' in f for f in query.qf)
        if has_type:
            print(f"✓ Section '{query.section_title}': TYPE:IMAGE filter present")
        else:
            print(f"❌ Section '{query.section_title}': Missing TYPE:IMAGE filter")
            all_valid = False

        # Check 4: Has YEAR filter
        has_year = any('YEAR:' in f for f in query.qf)
        if has_year:
            print(f"✓ Section '{query.section_title}': YEAR filter present")
        else:
            print(f"⚠️  Section '{query.section_title}': No YEAR filter (optional)")

        print()

    if all_valid:
        print("✅ ALL VALIDATION CHECKS PASSED")
    else:
        print("❌ SOME VALIDATION CHECKS FAILED")

    print()
    return queries

if __name__ == "__main__":
    queries = main()
