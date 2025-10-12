#!/usr/bin/env python3
"""
V6: Riddle-Focused Knowledge Graph Question Generator

Combines V5's ultra-difficulty chain generation with truly oblique,
riddle-like question design.

Goal: 9.0+ riddle quality score
Target: "Deliberately oblique, riddle-like information retrieval questions"
        that test lateral thinking (per README.md)
"""

import json
import os
import random
import sys

# Import V5's chain generation infrastructure
sys.path.insert(0, os.path.dirname(__file__))
from generate_kg_questions_v5 import (
    build_entity_pool,
    generate_v5_chain,
    DIFFICULTY_HOPS,
    client
)

# ============================================================================
# RIDDLE GENERATION TECHNIQUES
# ============================================================================

RIDDLE_TECHNIQUES = [
    {
        "name": "role_metaphor",
        "description": "Describe entity's function/role using unexpected modern analogy",
        "examples": [
            "Manager who prefers wearable tech for surveillance → Sauron",
            "Oval Office tenant who couldn't tell a lie about cherry trees → Washington",
            "Mathematician who proved you can't prove everything → Gödel"
        ]
    },
    {
        "name": "anachronistic_tech",
        "description": "Describe historical/abstract thing using modern technology terms",
        "examples": [
            "Ancient crowdsourced construction project visible from orbit → Great Wall",
            "Pre-digital social network limited to 150 connections → Dunbar's Number",
            "Original viral loop featuring forbidden fruit → Garden of Eden"
        ]
    },
    {
        "name": "occupational_disguise",
        "description": "Reduce entity to humble job description or role",
        "examples": [
            "Carpenter's son who went into the family business of redemption → Jesus",
            "Patent clerk who revolutionized commute times → Einstein",
            "Apple farmer who discovered gravity during lunch break → Newton"
        ]
    },
    {
        "name": "minimalist_clue",
        "description": "Ultra-concise, poetic phrasing with layered meanings",
        "examples": [
            "Circular jewelry and walking → Lord of the Rings",
            "Flying boy who never aged → Peter Pan",
            "Wooden puppet who lied his way to humanity → Pinocchio"
        ]
    },
    {
        "name": "chain_metaphor",
        "description": "Trace the chain using metaphorical transformations",
        "examples": [
            "When tribal limits met Hollywood math → Small-World Network",
            "From ivory towers through absurdist philosophy to frozen matter → Negative thermal expansion"
        ]
    },
    {
        "name": "property_riddle",
        "description": "Describe through paradoxical or unusual properties",
        "examples": [
            "Theory that insists you can't be certain about position and speed → Heisenberg Uncertainty",
            "The only number that's afraid of being eaten → 7 (seven ate nine)",
            "Material that shrinks when heated → Negative thermal expansion"
        ]
    }
]

# ============================================================================
# RIDDLE QUESTION GENERATOR
# ============================================================================

def generate_riddle_question_v6(chain: dict) -> dict:
    """
    Generate deliberately oblique, riddle-like question from chain.

    Targets 9.0+ riddle quality by emphasizing:
    - Obliqueness (metaphors, indirect language)
    - Lateral thinking (abstract → concrete mapping)
    - Misdirection (clever red herrings)
    - Conciseness (20 words or less ideal)
    - Multiple layered clues
    """

    entities = chain['entities']
    answer = entities[-1]
    start_entity = entities[0]
    domains = chain['domains']

    # Build relation context
    relations_text = "\n".join([
        f"{i+1}. {rel['relation']}"
        for i, rel in enumerate(chain['relations'])
    ])

    # Select riddle techniques
    techniques_text = "\n".join([
        f"- {t['name'].upper()}: {t['description']}\n  Examples: {'; '.join(t['examples'][:2])}"
        for t in random.sample(RIDDLE_TECHNIQUES, 3)
    ])

    system_prompt = """You are a master riddle creator for Riddler Bench.

VISION: "Deliberately oblique, riddle-like information retrieval questions that test
lateral thinking and the ability to connect abstract clues to concrete knowledge."

GOLD STANDARD EXAMPLE:
  Question: "Manager who prefers wearable tech for surveillance"
  Answer: Sauron
  Why excellent:
    • OBLIQUE: "Manager" = Dark Lord (job title metaphor)
    • METAPHORICAL: "wearable tech" = Ring (anachronistic)
    • LATERAL THINKING: Must map modern corporate → fantasy evil
    • CONCISE: 7 words
    • MISDIRECTION: Sounds like tech startup CEO
    • REWARD: "Aha!" moment when solved

YOUR MISSION: Create riddles that score 9.0+ on riddle quality by maximizing:
- Obliqueness (indirect, metaphorical language)
- Lateral thinking requirement
- Elegant misdirection
- Conciseness (under 25 words)
- Multiple layered clues"""

    user_prompt = f"""Create a riddle-like question for this knowledge chain:

CHAIN: {' → '.join(entities)}
DOMAINS: {' → '.join(domains)}
ANSWER: {answer}

RELATIONS (how entities connect):
{relations_text}

RIDDLE TECHNIQUES (use 1-2):
{techniques_text}

REQUIREMENTS:
1. DO NOT mention the answer directly
2. DO NOT use obvious academic language ("theoretical framework", "concept", etc.)
3. USE metaphors, role disguises, anachronisms
4. REQUIRE lateral thinking to decode
5. KEEP IT CONCISE (under 25 words ideal, 30 max)
6. HINT at the chain without revealing intermediate entities
7. CREATE "aha!" moment potential

EXAMPLES OF GOOD RIDDLE STYLE:
• "When tribal limits met Hollywood parlor games, what paradox explained global proximity?"
• "From clockmaker's God through absurdist science to matter that rebels against heat?"
• "Shoemaker whose sibling rivalry split the fastest feet in the world?"

BAD (too direct):
• "Which theoretical framework emerged from network theory?"
• "What concept in sociology describes interconnectedness?"

Respond with ONLY the riddle question, nothing else. No quotes, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,  # Higher for creativity
            max_tokens=100
        )

        question = response.choices[0].message.content.strip().strip('"').strip("'")

        # Verify it's not too long
        word_count = len(question.split())
        if word_count > 35:
            print(f"    ⚠️  Question too long ({word_count} words), retrying...")
            return None

        return {
            'question': question,
            'answer': answer,
            'chain': entities,
            'domains': chain['domains'],
            'num_hops': chain['num_hops'],
            'difficulty': chain['difficulty'],
            'has_abstract': chain['has_abstract'],
            'cross_domain_count': chain['cross_domain_count'],
            'avg_obscurity': sum(chain['obscurity_scores']) / len(chain['obscurity_scores']),
            'relations': chain['relations'],
            'word_count': word_count
        }

    except Exception as e:
        print(f"    Error generating riddle: {e}")
        return None


def refine_riddle_with_feedback(question_data: dict, attempt: int = 1) -> dict:
    """
    Use LLM to critique and refine the riddle if it's not oblique enough.
    """

    question = question_data['question']
    answer = question_data['answer']

    system_prompt = """You improve riddles to be more oblique and clever.

Focus on:
- Replace direct language with metaphors
- Add misdirection
- Make it more concise
- Increase lateral thinking requirement"""

    user_prompt = f"""Improve this riddle to be MORE oblique and clever:

Current: "{question}"
Answer: {answer}

Issues to fix:
- Too direct/academic?
- Missing metaphors?
- Too wordy?
- Lacks misdirection?

Return ONLY the improved riddle question, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,
            max_tokens=100
        )

        improved = response.choices[0].message.content.strip().strip('"').strip("'")

        # Update question
        question_data['question'] = improved
        question_data['word_count'] = len(improved.split())
        question_data['refined'] = True
        question_data['refinement_attempts'] = attempt

        return question_data

    except Exception as e:
        print(f"    Error refining riddle: {e}")
        return question_data


# ============================================================================
# MAIN GENERATION
# ============================================================================

def main():
    print("=" * 80)
    print("V6: RIDDLE-FOCUSED KNOWLEDGE GRAPH QUESTIONS")
    print("=" * 80)
    print("\nGoal: 9.0+ riddle quality score")
    print("Vision: Deliberately oblique, riddle-like questions\n")

    # Build entity pool (reuse V5's)
    print("📚 Building enhanced entity pool...")
    entity_pool = build_entity_pool()
    print(f"   Total entities: {len(entity_pool)}")
    print(f"   Abstract concepts: {sum(1 for e in entity_pool if e.is_abstract)}")
    print(f"   High obscurity (>0.7): {sum(1 for e in entity_pool if e.obscurity_score > 0.7)}")

    # Generation targets
    questions_per_difficulty = {
        "hard": 5,
        "expert": 3,
    }

    all_questions = []

    for difficulty, target in questions_per_difficulty.items():
        print(f"\n🎯 Generating {difficulty.upper()} riddles (target: {target})...")
        print("-" * 80)

        generated = 0
        attempts = 0
        max_attempts = target * 8  # More attempts for quality

        while generated < target and attempts < max_attempts:
            attempts += 1

            if attempts % 5 == 0:
                print(f"   Attempt {attempts}/{max_attempts}, generated {generated}/{target}...")

            # Generate chain (use V5's excellent chain generation)
            chain = generate_v5_chain(difficulty, entity_pool)

            if chain is None:
                continue

            # Generate RIDDLE-style question
            question_data = generate_riddle_question_v6(chain)

            if question_data is None:
                continue

            # Quick quality check: word count
            if question_data['word_count'] > 30:
                # Try to refine
                question_data = refine_riddle_with_feedback(question_data)

            # Accept if reasonable
            generated += 1
            all_questions.append(question_data)

            print(f"   ✓ #{generated}: \"{question_data['question'][:60]}...\"")
            print(f"      Answer: {question_data['answer'][:30]}... ({question_data['word_count']} words)")

    # Save results
    output_file = 'data/knowledge_graph_questions_v6.jsonl'
    with open(output_file, 'w') as f:
        for q in all_questions:
            f.write(json.dumps(q) + '\n')

    # Summary
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nTotal riddles: {len(all_questions)}")

    if all_questions:
        avg_word_count = sum(q['word_count'] for q in all_questions) / len(all_questions)
        print(f"Average word count: {avg_word_count:.1f} words")

        refined_count = sum(1 for q in all_questions if q.get('refined', False))
        print(f"Refined riddles: {refined_count}/{len(all_questions)}")

        print(f"\nDifficulty Distribution:")
        for difficulty in ["hard", "expert"]:
            count = sum(1 for q in all_questions if q['difficulty'] == difficulty)
            print(f"  {difficulty.capitalize()}: {count}")

        print(f"\nSaved to: {output_file}")
        print("\n🎯 Next step: Run riddle_quality_framework.py to assess riddle quality!")


if __name__ == '__main__':
    main()
