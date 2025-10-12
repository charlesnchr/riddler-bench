#!/usr/bin/env python3
"""
Assess V6 riddles with riddle quality framework
"""

import json
from riddle_quality_framework import multi_llm_riddle_assessment

def assess_v6_sample():
    """Load and assess V6 sample riddles."""

    print("="*80)
    print("V6 RIDDLE QUALITY ASSESSMENT")
    print("="*80)

    # Load V6 questions
    with open('data/knowledge_graph_questions_v6.jsonl', 'r') as f:
        v6_questions = [json.loads(line) for line in f if line.strip()]

    print(f"\nLoaded {len(v6_questions)} V6 riddles")

    # Assess first 3 riddles
    results = []

    for i, q in enumerate(v6_questions[:3], 1):
        print(f"\n{'='*80}")
        print(f"V6 RIDDLE #{i}")
        print(f"{'='*80}")
        print(f"\nQuestion: \"{q['question']}\"")
        print(f"Answer: {q['answer']}")
        print(f"Chain: {' → '.join(q['chain'])}")
        print(f"Word count: {q['word_count']}")

        result = multi_llm_riddle_assessment(q)
        results.append(result)

        if result['valid']:
            print(f"\n{'─'*80}")
            print("TIER 2: RIDDLE QUALITY (Core Assessment)")
            print(f"{'─'*80}")
            for dim, score in result['tier2_riddle_quality']['scores'].items():
                print(f"  {dim.upper():25} {score:.1f}/10")
            print(f"\n  RIDDLE QUALITY: {result['tier2_riddle_quality']['average']:.2f}/10")
            print(f"  OVERALL: {result['overall']:.2f}/10")

    # Summary
    if results:
        print("\n" + "="*80)
        print("V6 RIDDLE QUALITY SUMMARY")
        print("="*80)

        valid_results = [r for r in results if r['valid']]

        if valid_results:
            avg_riddle = sum(r['tier2_riddle_quality']['average'] for r in valid_results) / len(valid_results)
            avg_overall = sum(r['overall'] for r in valid_results) / len(valid_results)

            print(f"\nAverage Riddle Quality: {avg_riddle:.2f}/10")
            print(f"Average Overall: {avg_overall:.2f}/10")

            # Compare to V5
            print(f"\n{'─'*80}")
            print("COMPARISON: V5 vs V6")
            print(f"{'─'*80}")
            print(f"\nV5 Riddle Quality: 6.46/10")
            print(f"V6 Riddle Quality: {avg_riddle:.2f}/10")
            print(f"\nImprovement: {avg_riddle - 6.46:+.2f} points")

            if avg_riddle >= 9.0:
                print("\n🏆 GOAL ACHIEVED: 9.0+ riddle quality!")
            elif avg_riddle >= 8.0:
                print("\n✅ EXCELLENT: Close to target!")
            elif avg_riddle >= 7.0:
                print("\n👍 GOOD: Significant improvement over V5")
            else:
                print("\n⚠️  Needs more work")

if __name__ == '__main__':
    assess_v6_sample()
