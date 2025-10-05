"""
Test theme relevance scoring with sample artist data
"""

import sys
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.scoring import ThemeRelevanceScorer
from backend.models import CuratorBrief

# Test data: curator brief from our demo
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

# Section keywords (from QueryBuilder extraction)
section_keywords = ["creation", "dreamlike", "landscapes", "digital"]

# Sample artworks for fictitious artists
artist_1_works = [
    {
        "title": ["Digital Dreams: Surreal Landscapes"],
        "dcDescription": ["Exploration of dreamlike imagery in digital art"],
        "dcSubject": ["Surrealism", "Digital Art", "Contemporary"],
        "type": "IMAGE",
        "dcType": ["photography"],
        "year": ["2018"],
        "country": ["Netherlands"],
        "dataProvider": ["Stedelijk Museum Amsterdam"]
    },
    {
        "title": ["Virtual Surrealism"],
        "dcDescription": ["Installation exploring unconscious mind"],
        "dcSubject": ["Surrealism", "Installation Art"],
        "type": "IMAGE",
        "dcType": ["installation"],
        "year": ["2020"],
        "country": ["Belgium"],
        "dataProvider": ["KMSKA Antwerp"]
    },
    {
        "title": ["Dreamscapes in Code"],
        "dcSubject": ["Contemporary Art", "Digital"],
        "type": "IMAGE",
        "dcType": ["photography"],
        "year": ["2019"],
        "country": ["Germany"],
        "dataProvider": ["ZKM Karlsruhe"]
    }
]

artist_2_works = [
    {
        "title": ["Abstract Painting"],
        "dcDescription": ["Abstract expressionist work"],
        "dcSubject": ["Abstract Expressionism"],
        "type": "IMAGE",
        "dcType": ["painting"],
        "year": ["1965"],
        "country": ["United States"],
        "dataProvider": ["MoMA New York"]
    },
    {
        "title": ["Untitled Sculpture"],
        "dcType": ["sculpture"],
        "type": "IMAGE",
        "year": ["1970"],
        "country": ["United States"],
        "dataProvider": ["Whitney Museum"]
    }
]

artist_3_works = [
    {
        "title": ["The Persistence of Memory"],
        "dcSubject": ["Surrealism"],
        "type": "IMAGE",
        "dcType": ["painting"],
        "year": ["1931"],
        "country": ["Spain"],
        "dataProvider": ["MoMA New York"]
    },
    {
        "title": ["Surrealist Composition"],
        "dcSubject": ["Surrealism"],
        "type": "IMAGE",
        "dcType": ["painting"],
        "year": ["1935"],
        "country": ["France"],
        "dataProvider": ["Pompidou Paris"]
    }
]

def main():
    print("=" * 80)
    print("TESTING THEME RELEVANCE SCORER")
    print("=" * 80)
    print()
    print(f"Theme: {curator_brief.theme_title}")
    print(f"Movements: {curator_brief.art_movements}")
    print(f"Media: {curator_brief.media_types}")
    print(f"Time Period: {curator_brief.time_period} (1970-2025)")
    print(f"Geography: {curator_brief.geographic_focus}")
    print(f"Keywords: {section_keywords}")
    print()

    # Initialize scorer
    scorer = ThemeRelevanceScorer(curator_brief, section_keywords)

    # Score three test artists
    artists = [
        ("Perfect Match Artist", artist_1_works),
        ("Poor Match Artist", artist_2_works),
        ("Historical Surrealist", artist_3_works)
    ]

    print("=" * 80)
    print("SCORING RESULTS")
    print("=" * 80)
    print()

    scores = []
    for artist_name, artworks in artists:
        score = scorer.score_artist(artist_name, artworks)
        scores.append(score)

        print(f"Artist: {artist_name}")
        print(f"  Total Score: {score.total_score:.1f}/100")
        print(f"  Works Analyzed: {score.works_analyzed}")
        print()
        print("  Dimension Scores:")
        print(f"    • Semantic (40%):     {score.dimensions.semantic_score:.1f}/100")
        print(f"    • Movement (25%):     {score.dimensions.movement_score:.1f}/100")
        print(f"    • Media (20%):        {score.dimensions.media_score:.1f}/100")
        print(f"    • Time Period (15%):  {score.dimensions.time_period_score:.1f}/100")
        print(f"    • Geographic Bonus:   +{score.dimensions.geographic_bonus:.1f}/10")
        print()
        print("  Match Details:")
        print(f"    • Institutions: {score.match_details['institutions_count']}")
        print(f"    • Countries: {list(score.match_details['countries'].keys())}")
        print()
        print("-" * 80)
        print()

    # Rank artists
    ranked = sorted(scores, key=lambda s: s.total_score, reverse=True)

    print("=" * 80)
    print("FINAL RANKING")
    print("=" * 80)
    print()
    for i, score in enumerate(ranked, 1):
        print(f"{i}. {score.artist_name}: {score.total_score:.1f}/100")
    print()

    # Validation
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)
    print()

    # Check if perfect match artist scores highest
    if ranked[0].artist_name == "Perfect Match Artist":
        print("✅ Perfect match artist ranked #1")
    else:
        print(f"❌ Expected 'Perfect Match Artist' at #1, got '{ranked[0].artist_name}'")

    # Check if poor match scores lowest
    if ranked[-1].artist_name == "Poor Match Artist":
        print("✅ Poor match artist ranked last")
    else:
        print(f"❌ Expected 'Poor Match Artist' last, got '{ranked[-1].artist_name}'")

    # Check score differentiation
    score_diff = ranked[0].total_score - ranked[-1].total_score
    if score_diff >= 30:
        print(f"✅ Good score differentiation ({score_diff:.1f} points)")
    else:
        print(f"⚠️  Low score differentiation ({score_diff:.1f} points)")

    print()

if __name__ == "__main__":
    main()
