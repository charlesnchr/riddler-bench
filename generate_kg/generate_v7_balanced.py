#!/usr/bin/env python3
"""
V7 Balanced: 3-4 hop chains with toned-down metaphorical style
Goal: Difficult but not impossible (20-50% success rate)
"""

import json
import os
import statistics
import time
import random

from generate_kg_questions_v5 import build_entity_pool, generate_v5_chain

# Toned-down riddle templates - less abstract, more direct clues
RIDDLE_TEMPLATES = [
    "From {clue1} through {clue2}, what connects to {answer_hint}?",
    "Starting with {clue1}, passing through {clue2}, what is {answer_hint}?",
    "{clue1} leads to {clue2}, ultimately reaching what {answer_hint}?",
    "What {answer_hint} is reached from {clue1} via {clue2}?",
    "Beginning at {clue1} and traveling through {clue2}, what {answer_hint} emerges?",
    "Which {answer_hint} connects {clue1} to {clue2}?",
    "From {clue1} to {clue2}, what {answer_hint} lies at the end?",
]


def generate_balanced_riddle(chain_data: dict) -> dict:
    """Generate a riddle with toned-down metaphorical style."""

    entities = chain_data['entities']
    relations = chain_data['relations']

    if len(entities) < 3:
        return None

    # Get first entity clue (more direct)
    first_entity = entities[0]
    first_clue = first_entity  # Use name directly or with minor description

    # Get middle entity clue
    if len(entities) >= 4:
        middle_entity = entities[len(entities)//2]
        middle_clue = middle_entity
    else:
        middle_entity = entities[1]
        middle_clue = middle_entity

    # Answer is the last entity
    answer = entities[-1]

    # Create answer hint based on domain or type
    answer_hint = f"concept"
    if 'domains' in chain_data and chain_data['domains']:
        domain = chain_data['domains'][-1]
        domain_hints = {
            'mathematics': 'mathematical concept',
            'physics': 'physical phenomenon',
            'philosophy': 'philosophical concept',
            'biology': 'biological concept',
            'chemistry': 'chemical concept',
            'history': 'historical entity',
            'visual_art': 'artistic concept',
            'music': 'musical concept',
            'literature': 'literary concept',
            'computer_science': 'computational concept',
        }
        answer_hint = domain_hints.get(domain, 'concept')

    # Add brief descriptions instead of heavy metaphors
    first_desc = get_brief_description(first_entity, relations[0] if relations else None)
    middle_desc = get_brief_description(middle_entity, relations[len(entities)//2] if len(relations) > len(entities)//2 else None)

    # Create clues
    clue1 = first_desc if first_desc else first_entity
    clue2 = middle_desc if middle_desc else middle_entity

    # Pick template
    template = random.choice(RIDDLE_TEMPLATES)

    question = template.format(
        clue1=clue1,
        clue2=clue2,
        answer_hint=answer_hint
    )

    word_count = len(question.split())

    return {
        'question': question,
        'answer': answer,
        'chain': entities,
        'domains': chain_data.get('domains', []),
        'num_hops': len(entities),
        'word_count': word_count,
        'difficulty': 'balanced',
        'relations': relations
    }


def get_brief_description(entity: str, relation: dict = None) -> str:
    """Get a brief, less metaphorical description of an entity."""

    # Simple descriptors based on entity characteristics
    descriptions = {
        # Logic/Philosophy
        "Russell's Paradox": "a logical paradox",
        "Gödel's Incompleteness Theorems": "a mathematical proof about limits",
        "Categorical Imperative": "a moral philosophy principle",

        # Mathematics
        "Kolmogorov Complexity": "algorithmic information theory",
        "Small-World Network": "network theory on connectivity",
        "Minimal Surface": "a surface minimizing area",

        # Physics
        "Hawking Radiation": "black hole radiation",
        "Symmetry Breaking": "spontaneous symmetry loss",
        "Renormalization Group": "scale transformation theory",

        # Arts
        "Bauhaus Movement": "functional design movement",
        "John Cage": "experimental composer",
        "Kazimir Malevich": "abstract painter",
    }

    # Return known description or entity name
    return descriptions.get(entity, entity)


def main():
    print("="*80)
    print("V7 BALANCED: 3-4 HOPS + TONED-DOWN METAPHORS")
    print("="*80)

    print("\nLoading entity pool...")
    start = time.time()
    entity_pool = build_entity_pool()
    print(f"Loaded {len(entity_pool)} entities in {time.time() - start:.1f}s")

    # V7 Balanced: medium difficulty (3-4 hops)
    num_samples = 10
    samples = []
    attempts = 0
    max_attempts = num_samples * 30

    print(f"\nGenerating {num_samples} V7 balanced samples...\n")

    while len(samples) < num_samples and attempts < max_attempts:
        attempts += 1

        if attempts % 5 == 0:
            print(f"  Attempt {attempts}/{max_attempts}, found {len(samples)}/{num_samples}...")

        # Use MEDIUM difficulty for 3-4 hops
        chain = generate_v5_chain("medium", entity_pool)
        if chain is None:
            continue

        # Generate balanced riddle (less metaphorical)
        question_data = generate_balanced_riddle(chain)
        if question_data is None:
            continue

        # Prefer reasonable word counts (8-25 words)
        if question_data['word_count'] < 8 or question_data['word_count'] > 25:
            continue

        # Add V7 metadata
        question_data['version'] = 'v7_balanced'
        question_data['generation_attempt'] = attempts

        samples.append(question_data)
        print(f"\n✓ V7 Sample {len(samples)}/{num_samples}:")
        print(f"  Chain ({len(question_data['chain'])} hops): {' → '.join(question_data['chain'])}")
        print(f"  Question ({question_data['word_count']} words): {question_data['question']}")
        print(f"  Answer: {question_data['answer']}")

    # Save
    output_file = 'data/knowledge_graph_questions_v7.jsonl'
    os.makedirs('data', exist_ok=True)

    with open(output_file, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')

    print("\n" + "="*80)
    print(f"✅ Generated {len(samples)} V7 balanced samples in {attempts} attempts")
    print(f"📁 Saved to: {output_file}")

    # Stats
    if samples:
        avg_hops = statistics.mean(len(s['chain']) for s in samples)
        avg_words = statistics.mean(s['word_count'] for s in samples)

        print(f"\nSTATISTICS:")
        print(f"  Avg hops: {avg_hops:.1f}")
        print(f"  Avg words: {avg_words:.1f}")
        print(f"  Success rate: {len(samples)}/{attempts} = {len(samples)/attempts*100:.1f}%")
        print(f"\nExpected difficulty: 20-50% model success rate")


if __name__ == '__main__':
    main()
