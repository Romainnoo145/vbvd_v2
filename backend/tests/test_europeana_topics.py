"""
Test script for Europeana Topics Knowledge Base
Verifies that theme mappings work correctly
"""

import sys
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.config.europeana_topics import (
    find_best_theme_match,
    get_europeana_search_params,
    build_europeana_query,
    EXHIBITION_THEME_MAPPINGS,
    ART_MOVEMENTS,
    MEDIA_TYPES,
)


def test_theme_detection():
    """Test automatic theme detection from descriptions"""
    print("🎨 Testing Theme Detection\n" + "="*60)

    test_cases = [
        "Dreams & Reality: The Surrealist Revolution",
        "Dutch Modernism: De Stijl and Beyond",
        "Contemporary Sculpture from European Collections",
        "Abstract Expressionism in Post-War Europe",
        "Installation Art: Space and Experience",
    ]

    for description in test_cases:
        mapping = find_best_theme_match(description)
        if mapping:
            print(f"\n📋 Description: {description}")
            print(f"   ✅ Detected Theme: {mapping.art_movements}")
            print(f"   📅 Time Periods: {mapping.time_periods}")
            print(f"   🎭 Media Types: {mapping.media_types[:3]}...")
        else:
            print(f"\n📋 Description: {description}")
            print(f"   ❌ No theme detected")


def test_specific_theme():
    """Test getting specific theme parameters"""
    print("\n\n🔍 Testing Specific Theme Lookup\n" + "="*60)

    theme = "surrealism"
    mapping = get_europeana_search_params(theme)

    if mapping:
        print(f"\n📌 Theme: {theme}")
        print(f"   🎨 Topic ID: {mapping.topic_id}")
        print(f"   🔎 Search Terms: {mapping.search_terms}")
        print(f"   🎭 Art Movements: {mapping.art_movements}")
        print(f"   📦 Media Types: {mapping.media_types}")
        print(f"   📅 Time Periods: {mapping.time_periods}")
        print(f"   🔧 QF Filters: {mapping.qf_filters}")


def test_query_building():
    """Test building enhanced API queries"""
    print("\n\n🛠️  Testing Query Building\n" + "="*60)

    params = build_europeana_query(
        base_query="Salvador Dalí",
        theme="surrealism",
        media_type="painting",
        time_period="1920-1945"
    )

    print(f"\n🔎 Base Query: 'Salvador Dalí'")
    print(f"   🎨 Theme: surrealism")
    print(f"   🎭 Media: painting")
    print(f"   📅 Period: 1920-1945")
    print(f"\n📤 Generated Parameters:")
    print(f"   Query: {params['query']}")
    if 'qf' in params:
        print(f"   Filters: {params['qf']}")


def test_available_mappings():
    """Show all available theme mappings"""
    print("\n\n📚 Available Theme Mappings\n" + "="*60)

    for theme_key, mapping in EXHIBITION_THEME_MAPPINGS.items():
        print(f"\n🏷️  {theme_key.replace('_', ' ').title()}")
        print(f"   Movements: {', '.join(mapping.art_movements[:3])}")
        print(f"   Media: {', '.join(mapping.media_types[:3])}")
        print(f"   Periods: {', '.join(mapping.time_periods)}")


def test_art_movements_coverage():
    """Show coverage of art movements"""
    print("\n\n🎨 Art Movements Coverage\n" + "="*60)

    periods = {
        'Historical (1400-1800)': ['mannerism', 'baroque', 'rococo', 'neoclassicism'],
        '19th Century': ['romanticism', 'impressionism', 'post_impressionism', 'symbolism', 'art_nouveau'],
        'Early 20th Century (1900-1945)': ['expressionism', 'cubism', 'futurism', 'dadaism', 'surrealism', 'de_stijl', 'bauhaus'],
        'Mid-Late 20th Century (1945-2000)': ['art_deco', 'abstract_expressionism', 'pop_art', 'minimalism', 'conceptual_art'],
        'Contemporary (1970-present)': ['contemporary'],
    }

    for period, movements in periods.items():
        print(f"\n📅 {period}")
        for movement in movements:
            if movement in ART_MOVEMENTS:
                terms = ART_MOVEMENTS[movement][:3]  # Show first 3 terms
                print(f"   ✅ {movement}: {', '.join(terms)}")
            else:
                print(f"   ❌ {movement}: Not found")


def test_media_types_coverage():
    """Show coverage of media types"""
    print("\n\n🎭 Media Types Coverage\n" + "="*60)

    for media_type, terms in MEDIA_TYPES.items():
        print(f"\n🖼️  {media_type.replace('_', ' ').title()}")
        print(f"   Search terms: {', '.join(terms[:5])}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎨 EUROPEANA TOPICS KNOWLEDGE BASE TEST")
    print("="*60)

    try:
        test_theme_detection()
        test_specific_theme()
        test_query_building()
        test_available_mappings()
        test_art_movements_coverage()
        test_media_types_coverage()

        print("\n\n" + "="*60)
        print("✅ All tests completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
