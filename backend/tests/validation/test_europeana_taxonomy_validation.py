"""
Test Europeana Taxonomy Validation

Verifies that the validator:
1. Validates art movements against taxonomy
2. Validates media types
3. Checks time period consistency
4. Cross-validates movement/period combinations
5. Provides helpful suggestions
"""

import sys
sys.path.insert(0, '/home/klarifai/.clientprojects/vbvd_agent_v2')

from backend.validators.europeana_taxonomy_validator import EuropeanaTaxonomyValidator


def print_validation_result(result, title):
    """Pretty print validation result"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"\nValid: {'✅ YES' if result.is_valid else '❌ NO'}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"\nValidated Movements: {', '.join(result.validated_movements) if result.validated_movements else 'None'}")
    print(f"Validated Media: {', '.join(result.validated_media) if result.validated_media else 'None'}")

    if result.issues:
        print(f"\nIssues ({len(result.issues)}):")
        for issue in result.issues:
            icon = "❌" if issue.severity == "error" else "⚠️ " if issue.severity == "warning" else "ℹ️ "
            print(f"  {icon} [{issue.field}] {issue.message}")
            if issue.suggestion:
                print(f"     💡 {issue.suggestion}")
    else:
        print("\n✅ No issues found!")


def main():
    print("="*80)
    print("EUROPEANA TAXONOMY VALIDATION TEST")
    print("="*80)

    validator = EuropeanaTaxonomyValidator()

    # Test 1: Valid input
    result1 = validator.validate_input(
        art_movements=["surrealism", "contemporary"],
        media_types=["photography", "video_art"],
        time_period="contemporary"
    )
    print_validation_result(result1, "TEST 1: Valid Contemporary Surrealism")

    # Test 2: Period mismatch (Surrealism + Medieval period)
    result2 = validator.validate_input(
        art_movements=["surrealism", "cubism"],
        media_types=["painting"],
        year_range_from=1400,
        year_range_to=1500
    )
    print_validation_result(result2, "TEST 2: Period Mismatch - Surrealism in 1400-1500")

    # Test 3: Unrecognized movements
    result3 = validator.validate_input(
        art_movements=["quantum_expressionism", "cyber_baroque"],
        media_types=["hologram"],
        time_period="contemporary"
    )
    print_validation_result(result3, "TEST 3: Unrecognized Movements and Media")

    # Test 4: Narrow year range
    result4 = validator.validate_input(
        art_movements=["impressionism"],
        media_types=["painting"],
        year_range_from=1874,
        year_range_to=1876
    )
    print_validation_result(result4, "TEST 4: Very Narrow Year Range (2 years)")

    # Test 5: Good match - Impressionism with correct period
    result5 = validator.validate_input(
        art_movements=["impressionism", "post_impressionism"],
        media_types=["painting", "drawing"],
        year_range_from=1860,
        year_range_to=1910
    )
    print_validation_result(result5, "TEST 5: Perfect Match - Impressionism 1860-1910")

    # Test 6: Mixed periods - some compatible, some not
    result6 = validator.validate_input(
        art_movements=["baroque", "pop_art"],
        media_types=["painting"],
        time_period="contemporary"
    )
    print_validation_result(result6, "TEST 6: Mixed Periods - Baroque + Pop Art in Contemporary")

    # Test 7: No movements or media
    result7 = validator.validate_input(
        art_movements=[],
        media_types=[],
        time_period="post_war"
    )
    print_validation_result(result7, "TEST 7: No Movements or Media Selected")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    results = [result1, result2, result3, result4, result5, result6, result7]
    valid_count = sum(1 for r in results if r.is_valid)
    avg_confidence = sum(r.confidence_score for r in results) / len(results)

    print(f"\nTotal Tests: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {len(results) - valid_count}")
    print(f"Average Confidence: {avg_confidence:.2f}")
    print()


if __name__ == "__main__":
    main()
