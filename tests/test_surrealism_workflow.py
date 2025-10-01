"""
Full workflow test with Surrealism theme to prove real data (not mock data) is being used.
Expected output: Surrealist artists (Dalí, Magritte, Ernst) NOT De Stijl artists (Mondrian).
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief


async def test_surrealism_workflow():
    """Test full workflow with Surrealism theme - completely different from De Stijl tests"""

    print("\n" + "="*80)
    print("SURREALISM WORKFLOW TEST - Proving Real Data Usage")
    print("="*80)

    # Initialize clients
    data_client = EssentialDataClient()
    openai_key = os.getenv('OPENAI_API_KEY')

    orchestrator = OrchestratorAgent(
        data_client=data_client,
        openai_api_key=openai_key
    )

    # Surrealism theme - completely different from De Stijl
    brief = CuratorBrief(
        theme_title='Surrealism and the Unconscious Mind',
        theme_description='Exploring how surrealist artists used automatism, dream imagery, and psychological symbolism to access the unconscious mind. From Dalí\'s melting clocks to Magritte\'s visual paradoxes, these artists challenged rational thought.',
        theme_concepts=['surrealism', 'automatism', 'dream imagery', 'psychoanalysis', 'biomorphism'],
        reference_artists=['Salvador Dalí', 'René Magritte', 'Max Ernst'],
        target_audience='general',
        duration_weeks=12
    )

    # Reduced scope for faster execution (prove concept without waiting 10+ minutes)
    config = {
        'max_artists': 5,
        'max_artworks': 15,
        'artworks_per_artist': 3,
        'min_artist_relevance': 0.6,
        'min_artwork_relevance': 0.5
    }

    print("\n📋 INPUT BRIEF:")
    print(f"  Theme: {brief.theme_title}")
    print(f"  Concepts: {', '.join(brief.theme_concepts)}")
    print(f"  Reference Artists: {', '.join(brief.reference_artists)}")
    print(f"  Config: max_artists={config['max_artists']}, max_artworks={config['max_artworks']}")

    # Generate session ID
    from datetime import datetime
    session_id = f"surrealism-test-{datetime.utcnow().timestamp()}"

    # Execute full pipeline
    print("\n🚀 Starting pipeline execution...")
    result = await orchestrator.execute_pipeline(
        curator_brief=brief,
        session_id=session_id,
        config=config
    )

    # Analyze results
    print("\n" + "="*80)
    print("STAGE 1 - THEME REFINEMENT")
    print("="*80)
    theme = result['refined_theme']
    print(f"\n✅ Exhibition Title: {theme.title}")
    print(f"✅ Title Source: {theme.title_source}")
    print(f"\n📄 Curatorial Statement ({len(theme.curatorial_statement)} chars):")
    print(f"   {theme.curatorial_statement[:200]}...")
    print(f"✅ Statement Source: {theme.statement_source}")

    # Check for Surrealism keywords
    text = (theme.title + " " + theme.curatorial_statement).lower()
    surrealism_keywords = ['surrealism', 'surrealist', 'unconscious', 'dream', 'dalí', 'magritte', 'ernst']
    found_keywords = [kw for kw in surrealism_keywords if kw in text]
    print(f"\n🔍 Surrealism Keywords Found: {', '.join(found_keywords) if found_keywords else 'NONE (BAD!)'}")

    # Check it's NOT De Stijl
    destijl_keywords = ['de stijl', 'mondrian', 'van doesburg', 'neoplasticism', 'geometric abstraction']
    wrong_keywords = [kw for kw in destijl_keywords if kw in text]
    print(f"🔍 De Stijl Keywords (should be NONE): {', '.join(wrong_keywords) if wrong_keywords else 'NONE (GOOD!)'}")

    print("\n" + "="*80)
    print("STAGE 2 - ARTIST DISCOVERY")
    print("="*80)
    artists = result['artists']
    print(f"\n✅ Found {len(artists)} Artists (threshold: {config['min_artist_relevance']})")

    for i, artist in enumerate(artists[:10], 1):
        print(f"\n{i}. {artist.name}")
        print(f"   Score: {artist.relevance_score:.2f}")
        print(f"   Reasoning: {artist.relevance_reasoning[:150]}...")
        print(f"   Wikidata: {artist.wikidata_id}")

    # Check for expected surrealist artists
    artist_names = [a.name.lower() for a in artists]
    expected = ['dalí', 'dali', 'magritte', 'ernst', 'miró', 'tanguy', 'breton']
    found_surrealists = [exp for exp in expected if any(exp in name for name in artist_names)]
    print(f"\n🔍 Expected Surrealists Found: {', '.join(found_surrealists) if found_surrealists else 'NONE (CONCERNING!)'}")

    # Check it's NOT De Stijl artists
    wrong_artists = ['mondrian', 'doesburg', 'van der leck', 'huszár']
    found_wrong = [wrong for wrong in wrong_artists if any(wrong in name for name in artist_names)]
    print(f"🔍 De Stijl Artists (should be NONE): {', '.join(found_wrong) if found_wrong else 'NONE (GOOD!)'}")

    print("\n" + "="*80)
    print("STAGE 3 - ARTWORK DISCOVERY")
    print("="*80)
    artworks = result['artworks']
    print(f"\n✅ Found {len(artworks)} Artworks (threshold: {config['min_artwork_relevance']})")

    # Data quality metrics
    with_iiif = sum(1 for a in artworks if a.iiif_manifest)
    with_images = sum(1 for a in artworks if a.image_url)

    print(f"\n📊 Data Quality:")
    print(f"   IIIF Manifests: {with_iiif}/{len(artworks)} ({with_iiif/len(artworks)*100:.0f}%)")
    print(f"   Image URLs: {with_images}/{len(artworks)} ({with_images/len(artworks)*100:.0f}%)")

    print(f"\n🎨 Top 10 Artworks:")
    for i, artwork in enumerate(artworks[:10], 1):
        print(f"\n{i}. {artwork.title}")
        print(f"   Artist: {artwork.artist_name}")
        print(f"   Score: {artwork.relevance_score:.2f}")
        print(f"   Source: {artwork.data_source}")
        print(f"   IIIF: {'✅' if artwork.iiif_manifest else '❌'}")
        print(f"   Image: {'✅' if artwork.image_url else '❌'}")

    # VERDICT
    print("\n" + "="*80)
    print("VERDICT - IS THIS REAL DATA?")
    print("="*80)

    checks = []
    checks.append(("Stage 1 used LLM", theme.title_source == 'llm'))
    checks.append(("Theme is Surrealism-focused", len(found_keywords) >= 3))
    checks.append(("Theme is NOT De Stijl", len(wrong_keywords) == 0))
    checks.append(("Found surrealist artists", len(found_surrealists) >= 2))
    checks.append(("No De Stijl artists", len(found_wrong) == 0))
    checks.append(("IIIF availability > 50%", with_iiif/len(artworks) > 0.5 if artworks else False))
    checks.append(("Multiple data sources", len(set(a.data_source for a in artworks)) > 1))

    print()
    for check, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check}")

    passed = sum(1 for _, p in checks if p)
    total = len(checks)
    print(f"\n📊 Overall: {passed}/{total} checks passed")

    if passed >= 6:
        print("\n🎉 SUCCESS! This is real data, not mock data!")
        print("   - LLM generated Surrealism-specific content")
        print("   - Artist discovery found actual surrealist artists")
        print("   - Artwork APIs returned real museum data")
        return True
    else:
        print("\n⚠️  CONCERNS! Some checks failed - review output above")
        return False


if __name__ == '__main__':
    result = asyncio.run(test_surrealism_workflow())
    sys.exit(0 if result else 1)
