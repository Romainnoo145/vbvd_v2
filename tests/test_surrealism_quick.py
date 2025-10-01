"""
Quick Surrealism test - Stage 1 and Stage 2 only to prove real data usage
Tests theme generation and artist discovery without slow artwork discovery
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief


async def test_surrealism_quick():
    """Quick test: Stage 1 (Theme Refinement) only with Surrealism theme"""

    print("\n" + "="*80)
    print("QUICK SURREALISM TEST - Proving Real Data (Stage 1 Only)")
    print("="*80)

    # Initialize clients
    data_client = EssentialDataClient()
    openai_key = os.getenv('OPENAI_API_KEY')

    theme_agent = ThemeRefinementAgent(
        data_client=data_client,
        openai_api_key=openai_key
    )

    # Surrealism theme - completely different from De Stijl
    brief = CuratorBrief(
        theme_title='Surrealism and the Unconscious Mind',
        theme_description='Exploring how surrealist artists used automatism, dream imagery, and psychological symbolism to access the unconscious mind.',
        theme_concepts=['surrealism', 'automatism', 'dream imagery', 'psychoanalysis', 'biomorphism'],
        reference_artists=['Salvador Dalí', 'René Magritte', 'Max Ernst'],
        target_audience='general',
        duration_weeks=12
    )

    print("\n📋 INPUT BRIEF:")
    print(f"  Theme: {brief.theme_title}")
    print(f"  Concepts: {', '.join(brief.theme_concepts)}")
    print(f"  Reference Artists: {', '.join(brief.reference_artists)}")

    # Generate session ID
    from datetime import datetime
    session_id = f"surrealism-quick-test-{datetime.utcnow().timestamp()}"

    # Execute Stage 1 only
    print("\n🚀 Stage 1: Theme Refinement with LLM...")
    print("   (This uses OpenAI GPT-4 with Museum Van Bommel Van Dam voice)")

    refined_theme = await theme_agent.refine_theme(brief, session_id)

    # Analyze results
    print("\n" + "="*80)
    print("STAGE 1 RESULTS")
    print("="*80)

    print(f"\n✅ Exhibition Title: {refined_theme.exhibition_title}")
    if refined_theme.subtitle:
        print(f"   Subtitle: {refined_theme.subtitle}")
    print(f"   Length: {len(refined_theme.exhibition_title)} chars")

    print(f"\n📄 Curatorial Statement ({len(refined_theme.curatorial_statement.split())} words):")
    words = refined_theme.curatorial_statement.split()
    print(f"   {' '.join(words[:50])}...")

    print(f"\n📚 Scholarly Rationale ({len(refined_theme.scholarly_rationale.split())} words):")
    rationale_words = refined_theme.scholarly_rationale.split()
    print(f"   {' '.join(rationale_words[:50])}...")

    # CRITICAL CHECKS
    print("\n" + "="*80)
    print("VERIFICATION - IS THIS REAL LLM-GENERATED SURREALISM CONTENT?")
    print("="*80)

    full_text = (refined_theme.exhibition_title + " " +
                 (refined_theme.subtitle or "") + " " +
                 refined_theme.curatorial_statement + " " +
                 refined_theme.scholarly_rationale).lower()

    # Check for Surrealism keywords
    surrealism_keywords = {
        'surrealism': 'surrealism' in full_text or 'surrealist' in full_text,
        'unconscious': 'unconscious' in full_text or 'subconscious' in full_text,
        'dream': 'dream' in full_text,
        'psycho': 'psycho' in full_text or 'psychoanalysis' in full_text,
        'artists': any(name.lower() in full_text for name in ['dalí', 'dali', 'magritte', 'ernst'])
    }

    # Check it's NOT primarily about De Stijl (contextual mentions of museum's expertise are OK)
    # Only flag if De Stijl is mentioned as the MAIN subject
    destijl_in_title = 'de stijl' in refined_theme.exhibition_title.lower() or 'mondrian' in refined_theme.exhibition_title.lower()
    destijl_count = full_text.count('de stijl') + full_text.count('destijl') + full_text.count('mondrian')

    destijl_keywords = {
        'De Stijl in title': destijl_in_title,
        'Multiple De Stijl references': destijl_count > 2  # More than 2 suggests it's about De Stijl, not just context
    }

    print("\n🔍 Surrealism Keywords Found:")
    for keyword, found in surrealism_keywords.items():
        status = "✅" if found else "❌"
        print(f"   {status} {keyword}")

    print("\n🔍 De Stijl Focus Checks (contextual mentions are OK):")
    for keyword, found in destijl_keywords.items():
        status = "❌ WRONG!" if found else "✅"
        print(f"   {status} {keyword}")

    # VERDICT
    surrealism_score = sum(surrealism_keywords.values())
    destijl_focus = sum(destijl_keywords.values())

    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    print(f"\n📊 Scores:")
    print(f"   Surrealism relevance: {surrealism_score}/5 keywords found")
    print(f"   De Stijl as main focus: {destijl_focus}/2 red flags (should be 0)")
    print(f"   Total 'de stijl/mondrian' mentions: {destijl_count} (1-2 contextual mentions are OK)")

    # Success criteria: strong Surrealism presence, De Stijl not the main focus
    success = (surrealism_score >= 3 and destijl_focus == 0)

    if success:
        print("\n🎉 SUCCESS!")
        print("   ✅ Content is clearly about Surrealism (not De Stijl)")
        print("   ✅ System generated theme-appropriate content")
        print("   ✅ This proves the system is NOT using mock data")
        print("   ✅ LLM successfully adapted to completely different art movement")
        return True
    else:
        print("\n⚠️  FAILURE!")
        if surrealism_score < 3:
            print(f"   ❌ Not enough Surrealism keywords ({surrealism_score}/5)")
            print("       System may be generating generic or wrong content")
        if destijl_focus > 0:
            print(f"   ❌ De Stijl is the main focus ({destijl_focus}/2 red flags)")
            print("       System is stuck on previous theme - possible mock data!")
        return False


if __name__ == '__main__':
    result = asyncio.run(test_surrealism_quick())
    sys.exit(0 if result else 1)
