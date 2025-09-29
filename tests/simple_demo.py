#!/usr/bin/env python3
"""
Simple Demo - What We Can Do Right Now
Shows practical capabilities with just Wikipedia working
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.clients import EssentialDataClient


async def curator_research_assistant():
    """
    CURRENT CAPABILITY: Curatorial Research Assistant
    What we can do right now with Wikipedia integration
    """
    print("\n" + "="*60)
    print("🎨 AI CURATOR ASSISTANT - Current Capabilities")
    print("="*60)
    print("\nWith just Wikipedia working, we can already provide:")
    print("✅ Art historical research and context")
    print("✅ Artist biographical information")
    print("✅ Art movement documentation")
    print("✅ Cultural and historical background")

    async with EssentialDataClient() as client:

        # Demo 1: Art Movement Research
        print("\n" + "-"*50)
        print("📚 DEMO 1: Art Movement Research")
        print("-"*50)

        movement = "Impressionism"
        print(f"\nResearching: {movement}")

        results = await client._search_wikipedia(movement, "art movement 19th century France")

        if results:
            print(f"\n✅ Found {len(results)} relevant articles:")
            for i, article in enumerate(results, 1):
                print(f"\n{i}. {article['title']}")
                print(f"   📄 {article['summary'][:150]}...")
                print(f"   🔗 {article['url']}")

        # Demo 2: Artist Biography Research
        print("\n" + "-"*50)
        print("👨‍🎨 DEMO 2: Artist Biography Research")
        print("-"*50)

        artist = "Claude Monet"
        print(f"\nResearching: {artist}")

        results = await client._search_wikipedia(artist, "French impressionist painter")

        if results:
            article = results[0]
            print(f"\n✅ Found biographical information:")
            print(f"   Title: {article['title']}")
            print(f"   Summary: {article['summary'][:200]}...")
            print(f"   Word Count: {article.get('word_count', 'N/A')} words")
            print(f"   Wikipedia URL: {article['url']}")

        # Demo 3: Artwork Research
        print("\n" + "-"*50)
        print("🖼️  DEMO 3: Artwork Research")
        print("-"*50)

        artwork = "Starry Night"
        print(f"\nResearching: {artwork}")

        results = await client._search_wikipedia(artwork, "Van Gogh painting artwork")

        if results:
            print(f"\n✅ Found {len(results)} related articles:")
            for article in results:
                print(f"   • {article['title']}")
                print(f"     {article['summary'][:100]}...")

        # Demo 4: Curatorial Theme Development
        print("\n" + "-"*50)
        print("💡 DEMO 4: Exhibition Theme Research")
        print("-"*50)

        theme = "Light and Shadow in Art"
        print(f"\nResearching exhibition theme: {theme}")

        # Research multiple related concepts
        concepts = ["chiaroscuro", "tenebrism", "light painting"]
        theme_research = {}

        for concept in concepts:
            print(f"\n   Researching: {concept}")
            results = await client._search_wikipedia(concept, "art technique painting")
            if results:
                theme_research[concept] = results[0]
                print(f"   ✅ Found: {results[0]['title']}")

        if theme_research:
            print(f"\n✅ Exhibition theme research complete!")
            print(f"   Gathered information on {len(theme_research)} key concepts")

            for concept, info in theme_research.items():
                print(f"\n   📖 {concept.title()}:")
                print(f"      {info['summary'][:120]}...")

    print("\n" + "="*60)
    print("🚀 WHAT'S NEXT: With AI Agents")
    print("="*60)
    print("\nWhen we add the AI agents, this research will become:")
    print("✨ Automatic theme refinement from curator input")
    print("✨ Intelligent artist discovery based on themes")
    print("✨ Artwork curation with relevance scoring")
    print("✨ Complete exhibition proposal generation")
    print("✨ Professional curatorial narratives")


async def practical_curator_workflow():
    """Show a practical workflow a real curator could use today"""

    print("\n" + "="*60)
    print("📋 PRACTICAL WORKFLOW: Planning an Exhibition")
    print("="*60)
    print("\nScenario: Curator wants to plan 'Water and Reflection in Art'")

    async with EssentialDataClient() as client:

        # Step 1: Research the core theme
        print("\n1️⃣ STEP 1: Theme Research")
        print("-" * 30)

        theme_results = await client._search_wikipedia("reflection water art", "painting technique symbolism")
        print(f"✅ Found {len(theme_results)} articles on water and reflection")

        # Step 2: Research key artists
        print("\n2️⃣ STEP 2: Artist Research")
        print("-" * 30)

        artists = ["Claude Monet", "Hokusai", "David Hockney"]
        artist_info = {}

        for artist in artists:
            results = await client._search_wikipedia(artist, "artist painter water reflection")
            if results:
                artist_info[artist] = results[0]
                print(f"✅ {artist}: {results[0]['title']}")

        # Step 3: Research specific artworks
        print("\n3️⃣ STEP 3: Artwork Research")
        print("-" * 30)

        artworks = ["Water Lilies", "Pool with Two Figures", "Great Wave"]

        for artwork in artworks:
            results = await client._search_wikipedia(artwork, "painting artwork water")
            if results:
                print(f"✅ {artwork}: Found {results[0]['title']}")
                print(f"   {results[0]['summary'][:80]}...")

        print("\n" + "="*60)
        print("📊 EXHIBITION RESEARCH SUMMARY")
        print("="*60)
        print(f"✅ Theme articles researched: {len(theme_results)}")
        print(f"✅ Artist biographies found: {len(artist_info)}")
        print(f"✅ Artwork information gathered: 3 pieces")
        print("\n💡 This research provides the foundation for:")
        print("   • Exhibition narrative development")
        print("   • Artist selection justification")
        print("   • Artwork relevance assessment")
        print("   • Curatorial statement writing")


if __name__ == "__main__":
    print("Select demo:")
    print("1. Research Assistant Capabilities")
    print("2. Practical Curator Workflow")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(curator_research_assistant())
    elif choice == "2":
        asyncio.run(practical_curator_workflow())
    else:
        print("Running default demo...")
        asyncio.run(curator_research_assistant())