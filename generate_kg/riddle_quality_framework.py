#!/usr/bin/env python3
"""
Riddle-Focused Quality Assessment Framework

Aligned with Riddler Bench vision: "deliberately oblique, riddle-like information
retrieval questions" that test lateral thinking and abstract-to-concrete connections.

Three-tier assessment:
1. Chain Structure Quality (knowledge graph backbone)
2. Riddle Quality (obliqueness, clue design, lateral thinking)
3. Solvability Balance (challenging but fair)
"""

import json
import os
from typing import Dict
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

load_dotenv()

# Multi-LLM setup for discriminatory power
azure_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_BASE_URL")
)

openrouter_client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
)

groq_client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
)

RATERS = [
    {"name": "gpt-4o", "client": azure_client, "model": "gpt-4o", "weight": 1.5},
    {"name": "gpt-4o-mini", "client": azure_client, "model": "gpt-4o-mini", "weight": 1.0},
    {"name": "claude-3.5-sonnet", "client": openrouter_client, "model": "anthropic/claude-3.5-sonnet", "weight": 1.5},
]


def assess_chain_structure(chain: dict, rater: dict) -> dict:
    """
    TIER 1: Knowledge Graph Backbone Quality

    Measures the structural integrity of the chain itself.
    """

    chain_text = " → ".join(chain.get('entities', [
        chain.get('entity1', ''),
        chain.get('entity2', ''),
        chain.get('entity3', ''),
        chain.get('entity4', ''),
        chain.get('entity5', '')
    ])[:chain.get('num_hops', 3)])

    domains_text = " → ".join(chain.get('domains', [])) if 'domains' in chain else "N/A"

    system_prompt = """You evaluate knowledge graph chain quality for riddle generation.
Focus on the STRUCTURAL properties of the chain itself."""

    user_prompt = f"""Rate this knowledge chain on 5 structural dimensions (0-10):

Chain: {chain_text}
Domains: {domains_text}
Hops: {chain.get('num_hops', 3)}

1. NON-CIRCULARITY (0-10): Are all entities distinct?
   10: Completely unique entities
   5: Similar/related entities
   0: Circular (entity repeats)

2. CONNECTION STRENGTH (0-10): Are connections verifiable and meaningful?
   10: Well-documented, significant relationships
   7: Verifiable but less known
   5: Plausible but hard to verify
   0: Dubious or forced connections

3. CROSS-DOMAIN CREATIVITY (0-10): Domain diversity?
   10: Each hop switches to completely different domain
   7: Multiple domains, some adjacent
   5: Two domains mixed
   0: Single domain only

4. OBSCURITY (0-10): How specialized is the knowledge?
   10: PhD-level specialized knowledge
   7: Advanced undergraduate knowledge
   5: Well-educated generalist
   3: General knowledge
   0: Common knowledge

5. SURPRISINGNESS (0-10): Is the endpoint unexpected?
   10: Genuinely surprising yet logical
   7: Somewhat unexpected
   5: Predictable
   0: Obvious or random

Respond EXACTLY:
NON_CIRCULARITY: [score]
CONNECTION_STRENGTH: [score]
CROSS_DOMAIN: [score]
OBSCURITY: [score]
SURPRISINGNESS: [score]"""

    try:
        response = rater['client'].chat.completions.create(
            model=rater['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        content = response.choices[0].message.content.strip()
        scores = parse_scores(content)

        return {
            'scores': scores,
            'valid': len(scores) >= 4
        }
    except Exception as e:
        print(f"  {rater['name']}: Error in chain assessment: {e}")
        return {'valid': False}


def assess_riddle_quality(question: str, answer: str, chain: dict, rater: dict) -> dict:
    """
    TIER 2: Riddle Quality (Core Innovation)

    Measures how well the question embodies "deliberately oblique, riddle-like"
    qualities that require lateral thinking.
    """

    system_prompt = """You evaluate RIDDLE quality for Riddler Bench.

Vision: "Deliberately oblique, riddle-like information retrieval questions that test
lateral thinking and the ability to connect abstract clues to concrete knowledge."

Example good riddle:
  Question: "Manager who prefers wearable tech for surveillance"
  Answer: Sauron
  Why good: Oblique (manager = Dark Lord), metaphorical (ring = wearable tech),
            requires lateral thinking to connect abstract clues"""

    user_prompt = f"""Rate this riddle on 6 dimensions (0-10):

Question: "{question}"
Answer: {answer}

1. OBLIQUENESS (0-10): How indirect is the question?
   10: Highly metaphorical, requires lateral leap
   8: Uses synonyms/euphemisms cleverly
   6: Somewhat indirect descriptions
   4: Mostly direct with minor obfuscation
   0: Direct question

2. CLUE QUALITY (0-10): Are clues elegant and fair?
   10: Multiple clever clues, each meaningful
   8: Good clues with subtle misdirection
   6: Adequate clues, straightforward
   4: Clues too obvious or too vague
   0: No real clues or misleading

3. LATERAL THINKING (0-10): Does it require non-linear reasoning?
   10: Requires connecting abstract concepts to concrete answer
   8: Needs metaphorical interpretation
   6: Needs some inference
   4: Mostly logical deduction
   0: Direct recall

4. MISDIRECTION (0-10): Elegant red herrings without unfairness?
   10: Beautifully misleading yet solvable
   7: Some misdirection, still fair
   5: Straightforward, no misdirection
   3: Confusing or ambiguous
   0: Unfair tricks

5. CONCISENESS (0-10): Elegant brevity?
   10: Perfectly concise, every word matters
   7: Good length, minor verbosity
   5: Acceptable but wordy
   3: Too long or too cryptic
   0: Rambling or incomprehensible

6. UNIQUENESS (0-10): Does it point to ONE answer?
   10: Answer is unambiguous and unique
   7: Answer is clear with context
   5: Could have 2-3 possible answers
   0: Multiple valid answers or unclear

Respond EXACTLY:
OBLIQUENESS: [score]
CLUE_QUALITY: [score]
LATERAL_THINKING: [score]
MISDIRECTION: [score]
CONCISENESS: [score]
UNIQUENESS: [score]"""

    try:
        response = rater['client'].chat.completions.create(
            model=rater['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=250
        )

        content = response.choices[0].message.content.strip()
        scores = parse_scores(content)

        return {
            'scores': scores,
            'valid': len(scores) >= 5
        }
    except Exception as e:
        print(f"  {rater['name']}: Error in riddle assessment: {e}")
        return {'valid': False}


def assess_solvability_balance(question: str, answer: str, chain: dict, rater: dict) -> dict:
    """
    TIER 3: Solvability Balance

    Measures whether the riddle is challenging but fair - the sweet spot
    between impossible and trivial.
    """

    system_prompt = """You evaluate whether a riddle is SOLVABLE but CHALLENGING.

Target: Highly educated, smart people who enjoy intellectual challenges.
Sweet spot: Requires thinking but has enough clues to solve."""

    user_prompt = f"""Rate this riddle on 4 dimensions (0-10):

Question: "{question}"
Answer: {answer}
Chain: {' → '.join(chain.get('entities', [])[:chain.get('num_hops', 3)])}

1. DIFFICULTY (0-10): Challenge level for smart people?
   10: Extremely difficult, PhD-level synthesis
   8: Very challenging, requires specialized knowledge
   7: Challenging, needs strong general knowledge
   5: Moderate, educated adult level
   3: Easy, general knowledge
   0: Trivial

2. FAIRNESS (0-10): Is it solvable with the given clues?
   10: All clues are present, fair challenge
   7: Mostly fair, one clue might be obscure
   5: Requires some assumptions
   3: Missing critical information
   0: Impossible or unfair

3. REWARD (0-10): Is solving it satisfying?
   10: "Aha!" moment, feels clever to solve
   7: Satisfying to get right
   5: Neutral, just factual
   3: Solving feels arbitrary
   0: No satisfaction

4. MEMORABILITY (0-10): Will people remember this riddle?
   10: Brilliant, will share with others
   7: Interesting, memorable
   5: Acceptable, forgettable
   3: Boring or confusing
   0: Waste of time

Respond EXACTLY:
DIFFICULTY: [score]
FAIRNESS: [score]
REWARD: [score]
MEMORABILITY: [score]"""

    try:
        response = rater['client'].chat.completions.create(
            model=rater['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        content = response.choices[0].message.content.strip()
        scores = parse_scores(content)

        return {
            'scores': scores,
            'valid': len(scores) >= 3
        }
    except Exception as e:
        print(f"  {rater['name']}: Error in solvability assessment: {e}")
        return {'valid': False}


def parse_scores(content: str) -> dict:
    """Parse scores from LLM response."""
    scores = {}
    for line in content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_').replace('-', '_')
            try:
                scores[key] = float(value.strip().split()[0])
            except:
                pass
    return scores


def multi_llm_riddle_assessment(question_data: dict) -> dict:
    """
    Comprehensive multi-LLM assessment with all three tiers.
    Returns consensus scores across multiple raters.
    """

    question = question_data.get('question', '')
    answer = question_data.get('answer', '')

    # Collect ratings from multiple LLMs
    chain_ratings = []
    riddle_ratings = []
    solvability_ratings = []

    print(f"  Assessing with {len(RATERS)} raters...")

    for rater in RATERS:
        print(f"    {rater['name']}...", end=" ")

        # Tier 1: Chain structure
        chain_result = assess_chain_structure(question_data, rater)
        if chain_result['valid']:
            chain_ratings.append((chain_result['scores'], rater['weight']))

        # Tier 2: Riddle quality
        riddle_result = assess_riddle_quality(question, answer, question_data, rater)
        if riddle_result['valid']:
            riddle_ratings.append((riddle_result['scores'], rater['weight']))

        # Tier 3: Solvability
        solvability_result = assess_solvability_balance(question, answer, question_data, rater)
        if solvability_result['valid']:
            solvability_ratings.append((solvability_result['scores'], rater['weight']))

        print("✓")

    # Calculate consensus scores for each tier
    chain_consensus = calculate_consensus(chain_ratings)
    riddle_consensus = calculate_consensus(riddle_ratings)
    solvability_consensus = calculate_consensus(solvability_ratings)

    # Calculate tier averages
    tier1_avg = sum(chain_consensus.values()) / len(chain_consensus) if chain_consensus else 0
    tier2_avg = sum(riddle_consensus.values()) / len(riddle_consensus) if riddle_consensus else 0
    tier3_avg = sum(solvability_consensus.values()) / len(solvability_consensus) if solvability_consensus else 0

    # Overall weighted score
    # Tier 2 (riddle quality) is most important for this benchmark
    overall = (
        tier1_avg * 0.25 +      # Chain structure (foundation)
        tier2_avg * 0.50 +      # Riddle quality (CORE)
        tier3_avg * 0.25        # Solvability balance (important)
    )

    return {
        'tier1_chain_structure': {
            'scores': chain_consensus,
            'average': round(tier1_avg, 2)
        },
        'tier2_riddle_quality': {
            'scores': riddle_consensus,
            'average': round(tier2_avg, 2)
        },
        'tier3_solvability': {
            'scores': solvability_consensus,
            'average': round(tier3_avg, 2)
        },
        'overall': round(overall, 2),
        'num_raters': len(RATERS),
        'valid': len(chain_ratings) >= 2 and len(riddle_ratings) >= 2
    }


def calculate_consensus(ratings: list) -> dict:
    """Calculate weighted consensus from multiple ratings."""
    if not ratings:
        return {}

    all_keys = set()
    for scores, _ in ratings:
        all_keys.update(scores.keys())

    consensus = {}
    for key in all_keys:
        weighted_sum = 0
        total_weight = 0

        for scores, weight in ratings:
            if key in scores:
                weighted_sum += scores[key] * weight
                total_weight += weight

        if total_weight > 0:
            consensus[key] = round(weighted_sum / total_weight, 2)

    return consensus


def comprehensive_assessment(question_data: dict, version: str):
    """Full assessment with detailed output."""

    print(f"\n{'='*80}")
    print(f"{version} COMPREHENSIVE ASSESSMENT")
    print(f"{'='*80}")

    chain_text = " → ".join(question_data.get('entities',
        [question_data.get('entity1', ''),
         question_data.get('entity2', ''),
         question_data.get('entity3', '')]
    )[:question_data.get('num_hops', 3)])

    print(f"\nChain: {chain_text}")
    print(f"Question: \"{question_data.get('question', '')[:80]}...\"")
    print(f"Answer: {question_data.get('answer', '')}")

    result = multi_llm_riddle_assessment(question_data)

    if result['valid']:
        print(f"\n{'─'*80}")
        print("TIER 1: CHAIN STRUCTURE (Knowledge Graph Backbone)")
        print(f"{'─'*80}")
        for dim, score in result['tier1_chain_structure']['scores'].items():
            print(f"  {dim.upper():25} {score:.1f}/10")
        print(f"\n  TIER 1 AVERAGE: {result['tier1_chain_structure']['average']:.2f}/10")

        print(f"\n{'─'*80}")
        print("TIER 2: RIDDLE QUALITY (Core Assessment)")
        print(f"{'─'*80}")
        for dim, score in result['tier2_riddle_quality']['scores'].items():
            print(f"  {dim.upper():25} {score:.1f}/10")
        print(f"\n  TIER 2 AVERAGE: {result['tier2_riddle_quality']['average']:.2f}/10")

        print(f"\n{'─'*80}")
        print("TIER 3: SOLVABILITY BALANCE")
        print(f"{'─'*80}")
        for dim, score in result['tier3_solvability']['scores'].items():
            print(f"  {dim.upper():25} {score:.1f}/10")
        print(f"\n  TIER 3 AVERAGE: {result['tier3_solvability']['average']:.2f}/10")

        print(f"\n{'='*80}")
        print("OVERALL SCORE")
        print(f"{'='*80}")
        print(f"  Tier 1 (Chain): {result['tier1_chain_structure']['average']:.2f}/10 × 25% weight")
        print(f"  Tier 2 (Riddle): {result['tier2_riddle_quality']['average']:.2f}/10 × 50% weight")
        print(f"  Tier 3 (Solvability): {result['tier3_solvability']['average']:.2f}/10 × 25% weight")
        print(f"\n  FINAL: {result['overall']:.2f}/10")

        if result['overall'] >= 9.0:
            verdict = "🏆 EXCEPTIONAL"
        elif result['overall'] >= 8.0:
            verdict = "✅ EXCELLENT"
        elif result['overall'] >= 7.0:
            verdict = "👍 GOOD"
        elif result['overall'] >= 6.0:
            verdict = "⚠️  ACCEPTABLE"
        else:
            verdict = "❌ NEEDS IMPROVEMENT"

        print(f"\n  {verdict}")

    return result


def compare_all_versions():
    """Compare V1-V5 with new riddle-focused framework."""

    print("="*80)
    print("RIDDLE-FOCUSED QUALITY COMPARISON: V1 → V5")
    print("="*80)

    samples = [
        {
            'version': 'V1 (Basic LLM)',
            'chain': "Einstein → Mileva Marić → Albert Einstein",
            'entity1': 'Einstein',
            'entity2': 'Mileva Marić',
            'entity3': 'Albert Einstein',
            'entities': ['Einstein', 'Mileva Marić', 'Albert Einstein'],
            'num_hops': 3,
            'question': "This groundbreaking physicist, often associated with a cosmic 'relative,' was once married to a brilliant mathematician and physicist who shared a name with a famous Serbian scientist. Who is this theoretical powerhouse known for revolutionizing our understanding of space and time?",
            'answer': 'Albert Einstein'
        },
        {
            'version': 'V2 (Chain Context)',
            'chain': "Usain Bolt → Puma → Rudolf Dassler",
            'entity1': 'Usain Bolt',
            'entity2': 'Puma',
            'entity3': 'Rudolf Dassler',
            'entities': ['Usain Bolt', 'Puma', 'Rudolf Dassler'],
            'num_hops': 3,
            'question': "Which entrepreneurial shoemaker founded the brand famously endorsed by the world's fastest man?",
            'answer': 'Rudolf Dassler',
            'domains': ['sports', 'business', 'business']
        },
        {
            'version': 'V3 (Advanced Features)',
            'chain': "Jane Goodall → Gombe Stream National Park → In the Shadow of Man",
            'entity1': 'Jane Goodall',
            'entity2': 'Gombe Stream National Park',
            'entity3': 'In the Shadow of Man',
            'entities': ['Jane Goodall', 'Gombe Stream National Park', 'In the Shadow of Man'],
            'num_hops': 3,
            'question': "Which renowned primatologist, who studied chimpanzees in a Tanzanian national park, authored a groundbreaking book about her observations?",
            'answer': 'In the Shadow of Man',
            'domains': ['biology', 'place', 'literature']
        },
        {
            'version': 'V4 (Variable Length)',
            'chain': "Steven Spielberg → Amblin Entertainment → DreamWorks Pictures → Shrek",
            'entity1': 'Steven Spielberg',
            'entity2': 'Amblin Entertainment',
            'entity3': 'DreamWorks Pictures',
            'entity4': 'Shrek',
            'entities': ['Steven Spielberg', 'Amblin Entertainment', 'DreamWorks Pictures', 'Shrek'],
            'num_hops': 4,
            'question': "Which animated film about an ogre was produced by the studio co-founded by the director of E.T. and Jurassic Park?",
            'answer': 'Shrek',
            'domains': ['film', 'business', 'business', 'film']
        },
        {
            'version': 'V5 (Ultra-Difficulty)',
            'chain': "Dunbar's Number → Erdős–Bacon number → Six Degrees of Kevin Bacon → Small-World Network",
            'entities': ["Dunbar's Number", "Erdős–Bacon number", "Six Degrees of Kevin Bacon", "Small-World Network"],
            'num_hops': 4,
            'question': "What theoretical framework, emerging from an era captivated by the cognitive limits of human connectivity and playfully quantified chains of collaboration across disciplines and industries, ultimately formalized our understanding of the surprising proximity within vast, intricate systems?",
            'answer': 'Small-World Network',
            'domains': ['psychology', 'mathematics', 'film', 'sociology']
        }
    ]

    results = []

    for sample in samples:
        result = comprehensive_assessment(sample, sample['version'])
        results.append({
            'version': sample['version'],
            'result': result
        })

    # Summary table
    print("\n" + "="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    print(f"\n{'Version':<25} {'Chain':<8} {'Riddle':<8} {'Solvab.':<8} {'Overall':<8}")
    print("-"*80)

    for r in results:
        if r['result'].get('valid'):
            version = r['version']
            chain = r['result']['tier1_chain_structure']['average']
            riddle = r['result']['tier2_riddle_quality']['average']
            solvability = r['result']['tier3_solvability']['average']
            overall = r['result']['overall']
            print(f"{version:<25} {chain:<8.2f} {riddle:<8.2f} {solvability:<8.2f} {overall:<8.2f}")

    print()

    return results


if __name__ == '__main__':
    compare_all_versions()
