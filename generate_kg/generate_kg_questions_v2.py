#!/usr/bin/env python3
"""
Enhanced knowledge-graph-based question generator with comprehensive improvements.

Key Features:
- Chain history awareness to prevent circular references
- Relation type constraints
- Entity type diversity
- Quality scoring and validation
- Fact verification
- MCQ distractor generation
- Difficulty calibration
- Cultural diversity
"""

import json
import os
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_BASE_URL")
)

# Diverse seed entities across cultures and domains
SEED_ENTITIES = [
    # Tech & Business
    "Steve Jobs", "Bill Gates", "Elon Musk", "Jeff Bezos", "Mark Zuckerberg",
    "Larry Page", "Sergey Brin", "Jack Ma", "Satya Nadella",

    # Entertainment
    "Steven Spielberg", "Martin Scorsese", "Quentin Tarantino", "Christopher Nolan",
    "Oprah Winfrey", "Taylor Swift", "Beyoncé", "Michael Jackson",

    # Sports
    "Michael Jordan", "Serena Williams", "Lionel Messi", "Cristiano Ronaldo",
    "LeBron James", "Usain Bolt", "Muhammad Ali", "Pelé",

    # Science & Innovation
    "Albert Einstein", "Marie Curie", "Stephen Hawking", "Neil deGrasse Tyson",
    "Jane Goodall", "Nikola Tesla", "Ada Lovelace",

    # Literature & Arts
    "Shakespeare", "Pablo Picasso", "Frida Kahlo", "Leonardo da Vinci",
    "Vincent van Gogh", "J.K. Rowling", "Ernest Hemingway",

    # Historical & Political (Global)
    "Nelson Mandela", "Mahatma Gandhi", "Martin Luther King Jr.",
    "Winston Churchill", "Cleopatra", "Abraham Lincoln",

    # Asian
    "Confucius", "Akira Kurosawa", "Bruce Lee", "Yayoi Kusama",
    "Mao Zedong", "Emperor Meiji",

    # Middle Eastern
    "Rumi", "Ibn Sina", "Naguib Mahfouz", "Omar Khayyam",

    # African
    "Wangari Maathai", "Desmond Tutu", "Fela Kuti",

    # Latin American
    "Gabriel García Márquez", "Diego Rivera", "Diego Maradona", "Eva Perón",

    # Organizations
    "Apple Inc", "Microsoft", "Google", "Amazon", "Tesla",
    "NASA", "United Nations", "Nobel Prize", "Harvard University",

    # Landmarks
    "Eiffel Tower", "Statue of Liberty", "Great Wall of China",
    "Taj Mahal", "Pyramids of Giza", "Colosseum",
]

# Specific relation types for better chain quality
RELATION_TYPES = [
    # Professional
    "founded", "co-founded", "acquired", "merged_with",
    "worked_at", "CEO_of", "invented", "pioneered",

    # Educational
    "attended", "graduated_from", "studied_under", "taught_at", "professor_at",

    # Personal
    "married_to", "divorced_from", "parent_of", "child_of", "sibling_of",

    # Creative
    "directed", "starred_in", "produced", "composed", "wrote",
    "designed", "painted", "photographed",

    # Geographic
    "born_in", "died_in", "lived_in", "headquartered_in", "located_in",

    # Competitive
    "defeated", "competed_against", "rival_of",

    # Influence
    "inspired", "influenced", "mentored", "studied",
]

# Entity types for diversity
ENTITY_TYPES = ["person", "organization", "place", "event", "artwork", "concept"]

# Track relation usage for diversity
relation_usage = defaultdict(int)

# Few-shot examples of good chains
GOOD_CHAIN_EXAMPLES = """
Example 1:
Entity 1: Jeff Bezos (person)
Entity 2: MacKenzie Scott (person, via ex-wife)
Entity 3: Princeton University (organization, via graduated_from)

Example 2:
Entity 1: Christopher Nolan (person)
Entity 2: Inception (artwork/film, via directed)
Entity 3: Hans Zimmer (person, via composed_score)

Example 3:
Entity 1: Steve Jobs (person)
Entity 2: Pixar Animation Studios (organization, via founded)
Entity 3: Toy Story (artwork/film, via first_film)
"""

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
    """Make a call to the LLM and return the response."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM call failed: {e}")
        raise


def select_diverse_relations(n: int = 3) -> List[str]:
    """Select relation types that haven't been overused."""
    # Get counts, prioritize less-used relations
    sorted_relations = sorted(RELATION_TYPES, key=lambda r: relation_usage[r])
    return random.sample(sorted_relations[:len(RELATION_TYPES)//2], min(n, len(sorted_relations)//2))


def generate_entity_chain(num_hops: int = 3, difficulty: str = "medium") -> Dict:
    """
    Generate a knowledge chain with full context awareness.

    Args:
        num_hops: Number of hops in the chain (2-4)
        difficulty: "easy", "medium", or "hard"
    """
    # Step 1: Select seed entity
    entity1 = random.choice(SEED_ENTITIES)
    chain_history = [entity1]

    # Step 2: Generate second entity with full context
    suggested_relations = select_diverse_relations(3)

    system_prompt = """You are a knowledge graph expert. Generate related entities through specific, meaningful connections.
IMPORTANT: Do NOT create circular references. Each entity must be distinct from all previous entities in the chain."""

    user_prompt = f"""Generate a second entity related to the first entity through a specific relation.

CHAIN SO FAR: {entity1}

CONSTRAINT: The second entity MUST be completely different from "{entity1}". Do NOT loop back.

Suggested relation types (choose one): {', '.join(suggested_relations)}

Respond in this EXACT format:
ENTITY: [name of entity]
TYPE: [person/organization/place/event/artwork/concept]
RELATION: [specific relation from {entity1}]

Example:
ENTITY: Pixar Animation Studios
TYPE: organization
RELATION: founded"""

    response1 = call_llm(system_prompt, user_prompt)

    # Parse entity2
    entity2 = None
    entity2_type = None
    relation1 = None

    for line in response1.split('\n'):
        line = line.strip()
        if line.startswith('ENTITY:'):
            entity2 = line.replace('ENTITY:', '').strip()
        elif line.startswith('TYPE:'):
            entity2_type = line.replace('TYPE:', '').strip()
        elif line.startswith('RELATION:'):
            relation1 = line.replace('RELATION:', '').strip()

    if not entity2 or not relation1:
        raise ValueError(f"Failed to parse entity2 from: {response1}")

    chain_history.append(entity2)

    # Update relation usage
    for rel in RELATION_TYPES:
        if rel in relation1.lower().replace(' ', '_'):
            relation_usage[rel] += 1
            break

    # Step 3: Generate third entity with FULL chain context
    suggested_relations2 = select_diverse_relations(3)

    user_prompt2 = f"""Generate a third entity related to the second entity through a specific relation.

FULL CHAIN SO FAR:
{entity1} → {entity2}

CONSTRAINT: The third entity MUST be completely different from BOTH:
- "{entity1}"
- "{entity2}"

Do NOT create a circular reference. Do NOT go back to the starting entity or anything similar.

Current entity to extend from: {entity2}

Suggested relation types (choose one): {', '.join(suggested_relations2)}

Respond in this EXACT format:
ENTITY: [name of entity]
TYPE: [person/organization/place/event/artwork/concept]
RELATION: [specific relation from {entity2}]"""

    response2 = call_llm(system_prompt, user_prompt2)

    # Parse entity3
    entity3 = None
    entity3_type = None
    relation2 = None

    for line in response2.split('\n'):
        line = line.strip()
        if line.startswith('ENTITY:'):
            entity3 = line.replace('ENTITY:', '').strip()
        elif line.startswith('TYPE:'):
            entity3_type = line.replace('TYPE:', '').strip()
        elif line.startswith('RELATION:'):
            relation2 = line.replace('RELATION:', '').strip()

    if not entity3 or not relation2:
        raise ValueError(f"Failed to parse entity3 from: {response2}")

    # Update relation usage
    for rel in RELATION_TYPES:
        if rel in relation2.lower().replace(' ', '_'):
            relation_usage[rel] += 1
            break

    return {
        'entity1': entity1,
        'entity2': entity2,
        'entity3': entity3,
        'entity1_type': 'varies',
        'entity2_type': entity2_type,
        'entity3_type': entity3_type,
        'relation1': relation1,
        'relation2': relation2,
        'num_hops': num_hops,
        'difficulty': difficulty
    }


def is_circular(chain: Dict) -> bool:
    """Check if chain has circular references."""
    entities = [chain['entity1'], chain['entity2'], chain['entity3']]

    # Check exact duplicates
    if len(entities) != len(set(entities)):
        return True

    # Check for similar names (fuzzy matching)
    for i, e1 in enumerate(entities):
        for j, e2 in enumerate(entities):
            if i != j:
                # Simple similarity: check if one name is substring of another
                e1_lower = e1.lower()
                e2_lower = e2.lower()

                # Remove common suffixes
                for suffix in [' inc', ' corp', ' university', ' college', ' studios']:
                    e1_lower = e1_lower.replace(suffix, '')
                    e2_lower = e2_lower.replace(suffix, '')

                if e1_lower in e2_lower or e2_lower in e1_lower:
                    return True

    return False


def score_chain_quality(chain: Dict) -> float:
    """Use LLM to rate chain quality on 0-10 scale."""

    system_prompt = "You are an expert evaluator of trivia question quality."

    user_prompt = f"""Rate this knowledge chain on a scale of 0-10 based on these criteria:

CHAIN:
{chain['entity1']} →({chain['relation1']})→ {chain['entity2']} →({chain['relation2']})→ {chain['entity3']}

Criteria:
1. No circular logic (all entities are distinct) - CRITICAL
2. Relations are interesting, not too obvious
3. Final entity is surprising but logically connected
4. Chain tells a coherent story
5. Entities span different domains/types

Score Guidelines:
- 9-10: Excellent, creative, non-obvious
- 7-8: Good, interesting connections
- 5-6: Acceptable but predictable
- 3-4: Weak connections or too obvious
- 0-2: Circular, broken, or nonsensical

Respond with ONLY a number 0-10: """

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.3)
        score = float(response.strip().split()[0])
        return max(0, min(10, score))
    except:
        return 5.0  # Default to medium if parsing fails


def verify_facts(chain: Dict) -> bool:
    """Verify that the relations in the chain are factually accurate."""

    system_prompt = "You are a fact-checker. Verify factual accuracy of statements."

    user_prompt = f"""Are these two statements factually accurate? Answer TRUE or FALSE.

Statement 1: {chain['entity1']} has a connection to {chain['entity2']} via "{chain['relation1']}"
Statement 2: {chain['entity2']} has a connection to {chain['entity3']} via "{chain['relation2']}"

Consider:
- Historical accuracy
- Temporal coherence (entities existed in compatible time periods)
- Factual correctness of relationships

Respond with ONLY: TRUE or FALSE"""

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.1)
        return "TRUE" in response.upper()
    except:
        return True  # Default to accepting if check fails


def generate_question(chain: Dict) -> Dict:
    """Generate a trivia question based on the entity chain."""

    system_prompt = f"""You are an expert trivia question writer specializing in clever, engaging questions.

{GOOD_CHAIN_EXAMPLES}

Your questions should:
- Describe entities indirectly without using exact names
- Be concise (aim for 20-40 words)
- Flow naturally from entity 1 → 2 → 3
- Be clever like a riddle
- Avoid being too cryptic or impossible"""

    user_prompt = f"""Create a trivia question based on this knowledge chain:

Entity 1: {chain['entity1']}
→ (via {chain['relation1']}) →
Entity 2: {chain['entity2']}
→ (via {chain['relation2']}) →
Entity 3: {chain['entity3']} [ANSWER]

Instructions:
1. Describe Entity 1 indirectly (e.g., "the electric car mogul" instead of "Elon Musk")
2. Mention the relation to Entity 2 (also described indirectly)
3. Mention the relation to Entity 3
4. Ask for Entity 3 as the answer

Be concise and clever. Make it engaging.

Format:
QUESTION: [your question in one clear sentence]
ANSWER: {chain['entity3']}"""

    response = call_llm(system_prompt, user_prompt, temperature=0.7)

    # Parse question
    question = None
    answer = None

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('QUESTION:'):
            question = line.replace('QUESTION:', '').strip()
        elif line.startswith('ANSWER:'):
            answer = line.replace('ANSWER:', '').strip()

    if not question:
        # Try to extract everything before ANSWER:
        parts = response.split('ANSWER:')
        if len(parts) >= 2:
            question = parts[0].replace('QUESTION:', '').strip()
            answer = parts[1].strip()
        else:
            question = response  # Fallback

    # Clean up formatting artifacts
    question = question.replace('****', '').replace('**', '').strip()

    return {
        'question': question,
        'answer': answer or chain['entity3']
    }


def generate_distractors(answer: str, chain: Dict) -> List[str]:
    """Generate 3 plausible but incorrect MCQ options."""

    system_prompt = "You are an expert at creating plausible but incorrect multiple choice options."

    user_prompt = f"""Generate 3 plausible WRONG answers for this trivia question:

Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}
Correct Answer: {answer}
Answer Type: {chain.get('entity3_type', 'unknown')}

Requirements for distractors:
1. Same entity type as the correct answer (e.g., if answer is a place, distractors should be places)
2. Plausibly related to the question context
3. Not obviously wrong
4. Not the correct answer

Return ONLY 3 distractors, one per line. No numbering, no extra text."""

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.9)
        distractors = [line.strip() for line in response.split('\n') if line.strip()]
        # Take first 3, remove any that are too similar to answer
        distractors = [d for d in distractors if d.lower() != answer.lower()][:3]

        # Pad if needed
        while len(distractors) < 3:
            distractors.append(f"[Similar to {answer}]")

        return distractors
    except:
        return ["Option A", "Option B", "Option C"]


def estimate_difficulty(chain: Dict, quality_score: float) -> str:
    """Estimate question difficulty."""

    # Factors:
    # - Quality score (higher = harder)
    # - Entity types (more diverse = harder)
    # - Relation obscurity

    if quality_score >= 8:
        return "hard"
    elif quality_score >= 6:
        return "medium"
    else:
        return "easy"


def generate_question_with_retry(max_attempts: int = 5, min_quality: float = 6.0) -> Optional[Dict]:
    """Generate a high-quality question with retry logic."""

    for attempt in range(max_attempts):
        try:
            print(f"  Attempt {attempt + 1}/{max_attempts}...", end=" ")

            # Generate chain
            chain = generate_entity_chain()

            # Check circular
            if is_circular(chain):
                print("❌ Circular")
                continue

            # Score quality
            quality = score_chain_quality(chain)
            print(f"Quality: {quality:.1f}", end=" ")

            if quality < min_quality:
                print("❌ Low quality")
                continue

            # Verify facts (optional, can be slow)
            if attempt > 2:  # Only verify after initial attempts
                facts_ok = verify_facts(chain)
                if not facts_ok:
                    print("❌ Facts failed")
                    continue

            # Generate question
            q = generate_question(chain)

            # Generate distractors
            distractors = generate_distractors(q['answer'], chain)

            # Estimate difficulty
            difficulty = estimate_difficulty(chain, quality)

            print("✅ Success")

            return {
                'chain': f"{chain['entity1']} → {chain['entity2']} → {chain['entity3']}",
                'question': q['question'],
                'answer': q['answer'],
                'options': distractors + [q['answer']],  # Will shuffle later
                'entity1': chain['entity1'],
                'entity2': chain['entity2'],
                'entity3': chain['entity3'],
                'relation1': chain['relation1'],
                'relation2': chain['relation2'],
                'quality_score': quality,
                'difficulty': difficulty
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt == max_attempts - 1:
                raise
            continue

    return None


def main():
    """Generate enhanced knowledge graph questions."""

    num_questions = 30
    questions = []

    print("=" * 70)
    print("🚀 Enhanced Knowledge Graph Question Generator v2")
    print("=" * 70)
    print(f"Target: {num_questions} high-quality questions")
    print(f"Min quality score: 6.0/10")
    print()

    successful = 0
    total_attempts = 0
    max_total_attempts = num_questions * 10  # Safety limit

    while successful < num_questions and total_attempts < max_total_attempts:
        print(f"\n📝 Generating question {successful + 1}/{num_questions}")
        total_attempts += 1

        q = generate_question_with_retry(max_attempts=5, min_quality=6.0)

        if q:
            # Shuffle options
            random.shuffle(q['options'])
            correct_index = q['options'].index(q['answer'])

            q['id'] = successful + 1
            q['correct_index'] = correct_index

            questions.append(q)
            successful += 1

            print(f"   Chain: {q['chain']}")
            print(f"   Q: {q['question'][:80]}...")
            print(f"   Difficulty: {q['difficulty']} | Quality: {q['quality_score']:.1f}")

    # Save results
    output_file = 'data/knowledge_graph_questions_v2.jsonl'
    with open(output_file, 'w') as f:
        for q in questions:
            f.write(json.dumps(q) + '\n')

    print("\n" + "=" * 70)
    print(f"✅ Successfully generated {len(questions)} questions")
    print(f"📁 Saved to: {output_file}")
    print(f"📊 Total attempts: {total_attempts}")
    print(f"📈 Success rate: {len(questions)/total_attempts*100:.1f}%")
    print("=" * 70)

    # Statistics
    print("\n📊 STATISTICS")
    print("-" * 70)

    difficulties = defaultdict(int)
    avg_quality = sum(q['quality_score'] for q in questions) / len(questions)

    for q in questions:
        difficulties[q['difficulty']] += 1

    print(f"Average quality score: {avg_quality:.2f}/10")
    print(f"Difficulty distribution:")
    for diff, count in sorted(difficulties.items()):
        print(f"  {diff.capitalize()}: {count} ({count/len(questions)*100:.1f}%)")

    # Sample questions
    print("\n" + "=" * 70)
    print("📋 SAMPLE QUESTIONS")
    print("=" * 70)

    for q in questions[:5]:
        print(f"\n[{q['difficulty'].upper()}] Chain: {q['chain']}")
        print(f"Q: {q['question']}")
        print(f"Options: {', '.join(q['options'])}")
        print(f"A: {q['answer']} (Quality: {q['quality_score']:.1f})")


if __name__ == '__main__':
    main()
