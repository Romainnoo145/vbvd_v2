"""
Debug version to see full generated text
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.agents.theme_refinement_agent import ThemeRefinementAgent
from backend.clients.essential_data_client import EssentialDataClient
from backend.models import CuratorBrief


async def test_debug():
    data_client = EssentialDataClient()
    openai_key = os.getenv('OPENAI_API_KEY')
    theme_agent = ThemeRefinementAgent(data_client=data_client, openai_api_key=openai_key)

    brief = CuratorBrief(
        theme_title='Surrealism and the Unconscious Mind',
        theme_description='Exploring how surrealist artists used automatism, dream imagery, and psychological symbolism to access the unconscious mind.',
        theme_concepts=['surrealism', 'automatism', 'dream imagery', 'psychoanalysis', 'biomorphism'],
        reference_artists=['Salvador Dalí', 'René Magritte', 'Max Ernst'],
        target_audience='general',
        duration_weeks=12
    )

    from datetime import datetime
    session_id = f"debug-{datetime.utcnow().timestamp()}"

    print("Generating theme with LLM...")
    refined_theme = await theme_agent.refine_theme(brief, session_id)

    print("\n" + "="*80)
    print("FULL EXHIBITION TITLE:")
    print("="*80)
    print(refined_theme.exhibition_title)
    if refined_theme.subtitle:
        print(f"Subtitle: {refined_theme.subtitle}")

    print("\n" + "="*80)
    print("FULL CURATORIAL STATEMENT:")
    print("="*80)
    print(refined_theme.curatorial_statement)

    print("\n" + "="*80)
    print("FULL SCHOLARLY RATIONALE:")
    print("="*80)
    print(refined_theme.scholarly_rationale)

    # Check for "de stijl"
    full_text = (refined_theme.exhibition_title + " " +
                 (refined_theme.subtitle or "") + " " +
                 refined_theme.curatorial_statement + " " +
                 refined_theme.scholarly_rationale)

    if 'de stijl' in full_text.lower() or 'destijl' in full_text.lower():
        print("\n" + "="*80)
        print("⚠️  FOUND 'DE STIJL' - Context:")
        print("="*80)
        # Find and show context
        lower_text = full_text.lower()
        pos = lower_text.find('de stijl')
        if pos == -1:
            pos = lower_text.find('destijl')
        if pos != -1:
            start = max(0, pos - 100)
            end = min(len(full_text), pos + 100)
            print(f"...{full_text[start:end]}...")


if __name__ == '__main__':
    asyncio.run(test_debug())
