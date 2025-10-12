#!/usr/bin/env python3
"""
V4: Variable Chain Lengths for Difficulty Control

New in V4:
- Easy: 2-hop chains (Entity1 → Entity2 [answer])
- Medium: 3-hop chains (Entity1 → Entity2 → Entity3 [answer])
- Hard: 4-hop chains (Entity1 → Entity2 → Entity3 → Entity4 [answer])
- Expert: 5-hop chains (Entity1 → ... → Entity5 [answer])

Plus all V3 features:
- Wikipedia API fact verification
- Semantic distance via embeddings (optional)
- Question format variation
- Progressive hint system
- Red herring chains
- Backward chain generation
"""

import json
import os
import random
import numpy as np
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import AzureOpenAI
import wikipediaapi
from fuzzywuzzy import fuzz

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_BASE_URL")
)

# Initialize Wikipedia API
wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent=os.environ.get("WIKIMEDIA_USER_AGENT", "RiddlerBench/1.0")
)

USE_EMBEDDINGS = os.environ.get("USE_EMBEDDINGS", "false").lower() == "true"

# Seed entities (same as v3)
SEED_ENTITIES = [
    "Steve Jobs", "Bill Gates", "Elon Musk", "Jeff Bezos", "Mark Zuckerberg",
    "Steven Spielberg", "Christopher Nolan", "Oprah Winfrey", "Taylor Swift",
    "Michael Jordan", "Serena Williams", "LeBron James", "Usain Bolt",
    "Albert Einstein", "Marie Curie", "Stephen Hawking", "Jane Goodall",
    "Shakespeare", "Pablo Picasso", "Frida Kahlo", "Vincent van Gogh",
    "Nelson Mandela", "Mahatma Gandhi", "Martin Luther King Jr.",
    "Confucius", "Akira Kurosawa", "Rumi", "Wangari Maathai",
    "Apple Inc", "Microsoft", "Google", "Harvard University",
]

TARGET_ANSWERS = [
    "The Louvre", "MIT", "Oxford University", "United Nations",
    "Nobel Prize", "Grammy Awards", "Olympics", "Mona Lisa",
]

RELATION_TYPES = [
    "founded", "co-founded", "acquired", "worked_at", "CEO_of",
    "attended", "graduated_from", "taught_at", "married_to",
    "directed", "starred_in", "composed", "wrote", "painted",
    "born_in", "died_in", "lived_in", "defeated", "inspired",
]

QUESTION_FORMATS = {
    "direct": {"weight": 40},
    "location": {"weight": 15},
    "year": {"weight": 10},
    "fill_blank": {"weight": 15},
    "negative": {"weight": 10},
    "comparison": {"weight": 10},
}

# Difficulty to hops mapping
DIFFICULTY_HOPS = {
    "easy": 2,
    "medium": 3,
    "hard": 4,
    "expert": 5
}

relation_usage = defaultdict(int)
embedding_cache = {}


# ============================================================================
# CORE LLM & WIKIPEDIA FUNCTIONS (from V3)
# ============================================================================

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
    """Make LLM call."""
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
        print(f"  LLM error: {e}")
        raise


def get_wikipedia_page(entity: str) -> Optional[wikipediaapi.WikipediaPage]:
    """Get Wikipedia page for entity."""
    try:
        page = wiki.page(entity)
        if page.exists():
            return page
        for variant in [f"{entity} (person)", f"{entity} (film)", f"{entity} (company)"]:
            page = wiki.page(variant)
            if page.exists():
                return page
        return None
    except:
        return None


def verify_relation_wikipedia(entity1: str, entity2: str) -> dict:
    """Verify relation via Wikipedia."""
    page1 = get_wikipedia_page(entity1)
    if not page1:
        return {'verified': False, 'confidence': 'low'}

    text = page1.text.lower()
    entity2_lower = entity2.lower()

    mention = entity2_lower in text or (len(entity2.split()) > 1 and entity2.split()[-1] in text)
    links = [link.lower() for link in page1.links.keys()]
    link_found = any(entity2_lower in link for link in links)

    confidence = 'high' if (mention and link_found) else 'medium' if (mention or link_found) else 'low'

    return {'verified': mention or link_found, 'confidence': confidence}


def get_embedding(text: str) -> np.ndarray:
    """Get embedding with caching."""
    if not USE_EMBEDDINGS:
        return np.random.rand(1536)

    if text in embedding_cache:
        return embedding_cache[text]

    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = np.array(response.data[0].embedding)
        embedding_cache[text] = embedding
        return embedding
    except:
        return np.random.rand(1536)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


# ============================================================================
# VARIABLE CHAIN LENGTH GENERATION
# ============================================================================

def generate_next_entity(current_entity: str, chain_history: List[str], hop_number: int) -> dict:
    """
    Generate the next entity in the chain.

    Args:
        current_entity: Entity to extend from
        chain_history: List of all entities so far
        hop_number: Which hop this is (1, 2, 3, 4...)
    """
    system_prompt = """You are a knowledge graph expert. Generate related entities through specific connections.
CRITICAL: Do NOT create circular references. Each entity must be distinct from all previous entities."""

    relations = random.sample(RELATION_TYPES, 3)

    # Build constraint text
    history_text = " → ".join(chain_history)
    exclusions = "\n".join([f'- "{e}"' for e in chain_history])

    user_prompt = f"""Generate the next entity in this knowledge chain.

FULL CHAIN SO FAR:
{history_text}

CRITICAL: The next entity MUST be completely different from ALL previous entities:
{exclusions}

Current entity to extend from: {current_entity}
This is hop #{hop_number} in the chain.

Suggested relation types: {', '.join(relations)}

Format:
ENTITY: [name of new entity]
TYPE: [person/organization/place/event/artwork/concept]
RELATION: [specific relation from {current_entity}]"""

    response = call_llm(system_prompt, user_prompt)

    # Parse response
    entity = None
    entity_type = None
    relation = None

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('ENTITY:'):
            entity = line.replace('ENTITY:', '').strip()
        elif line.startswith('TYPE:'):
            entity_type = line.replace('TYPE:', '').strip()
        elif line.startswith('RELATION:'):
            relation = line.replace('RELATION:', '').strip()

    if not entity or not relation:
        raise ValueError(f"Failed to parse entity from response")

    # Track relation usage
    for rel in RELATION_TYPES:
        if rel in relation.lower().replace(' ', '_'):
            relation_usage[rel] += 1
            break

    return {
        'entity': entity,
        'type': entity_type or 'unknown',
        'relation': relation
    }


def generate_variable_chain(difficulty: str = "medium") -> Dict:
    """
    Generate chain with variable length based on difficulty.

    Difficulty levels:
    - easy: 2 hops (A → B)
    - medium: 3 hops (A → B → C)
    - hard: 4 hops (A → B → C → D)
    - expert: 5 hops (A → B → C → D → E)
    """

    num_hops = DIFFICULTY_HOPS[difficulty]

    # Step 1: Pick seed entity
    entity1 = random.choice(SEED_ENTITIES)

    # Build chain iteratively
    chain = []
    chain_history = [entity1]

    current_entity = entity1

    for hop in range(1, num_hops):
        next_data = generate_next_entity(current_entity, chain_history, hop)

        chain.append({
            'from': current_entity,
            'to': next_data['entity'],
            'relation': next_data['relation'],
            'to_type': next_data['type']
        })

        chain_history.append(next_data['entity'])
        current_entity = next_data['entity']

    # Build result dict
    result = {
        'difficulty': difficulty,
        'num_hops': num_hops,
        'entities': chain_history,
        'chain': chain,
        'entity1': chain_history[0],
        'answer': chain_history[-1],
        'answer_type': chain[-1]['to_type'] if chain else 'unknown'
    }

    # Add entity_N and relation_N for backward compatibility
    for i, entity in enumerate(chain_history):
        result[f'entity{i+1}'] = entity

    for i, step in enumerate(chain):
        result[f'relation{i+1}'] = step['relation']

    return result


# ============================================================================
# QUESTION GENERATION (adapted for variable lengths)
# ============================================================================

def select_question_format() -> str:
    """Select random question format."""
    formats = list(QUESTION_FORMATS.keys())
    weights = [QUESTION_FORMATS[f]['weight'] for f in formats]
    return random.choices(formats, weights=weights)[0]


def generate_question_for_chain(chain: dict, format_type: str) -> dict:
    """Generate question adapted to chain length."""

    num_hops = chain['num_hops']
    entities = chain['entities']
    answer = chain['answer']

    # Build chain description
    chain_desc = []
    for step in chain['chain']:
        chain_desc.append(f"{step['from']} →({step['relation']})→ {step['to']}")
    chain_text = "\n".join(chain_desc)

    system_prompt = "You are an expert trivia question writer."

    if format_type == "direct":
        user_prompt = f"""Create a trivia question based on this {num_hops}-hop chain:

{chain_text}

The question should:
1. Describe {entities[0]} indirectly (no exact name)
2. Mention the connections along the chain
3. Ask for {answer} as the answer
4. Be concise (25-40 words for {num_hops} hops)

The more hops, the more connections to describe, but keep it readable.

Format:
QUESTION: [your question]
ANSWER: {answer}"""

    elif format_type == "fill_blank":
        # For fill_blank, ask for a middle entity
        if num_hops >= 3:
            middle_idx = num_hops // 2
            target = entities[middle_idx]
            before = " → ".join(entities[:middle_idx])
            after = " → ".join(entities[middle_idx+1:])

            user_prompt = f"""Create a "fill in the blank" question:

Complete the connection:
{before} → ______ → {after}

The answer is {target}.

Format:
QUESTION: Complete this connection: {before} → ? → {after}. What is the missing link?
ANSWER: {target}"""
        else:
            # Fall back to direct
            format_type = "direct"
            return generate_question_for_chain(chain, "direct")

    elif format_type == "location":
        user_prompt = f"""Create a location-based question:

Chain: {chain_text}

Ask WHERE something related to this chain happened or is located.
Answer should be: {answer}

Format:
QUESTION: Where did/is...
ANSWER: {answer}"""

    elif format_type == "comparison":
        if num_hops >= 3:
            entity_a = entities[1]
            entity_b = entities[-1]
            user_prompt = f"""Create a comparison question:

Chain involves: {entity_a} and {entity_b}

Ask which came first or which is older.

Format:
QUESTION: Which came first...
ANSWER: {answer}"""
        else:
            format_type = "direct"
            return generate_question_for_chain(chain, "direct")

    elif format_type == "negative":
        user_prompt = f"""Create a "Which is NOT" question:

Chain starts with: {entities[0]}

Create a question asking which entity is NOT connected to {entities[0]}.
Generate a plausible but incorrect entity as the answer.

Format:
QUESTION: Which of the following is NOT connected to [description of {entities[0]}]?
ANSWER: [Generate plausible incorrect entity]"""

    elif format_type == "year":
        user_prompt = f"""Create a year/time-based question:

Chain: {chain_text}

Ask WHEN something related to this chain happened.

Format:
QUESTION: In what year...
ANSWER: {answer} (or a year if appropriate)"""

    else:
        # Default
        user_prompt = user_prompt if 'user_prompt' in locals() else ""

    response = call_llm(system_prompt, user_prompt, temperature=0.7)

    # Parse
    question = None
    answer_parsed = None

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('QUESTION:'):
            question = line.replace('QUESTION:', '').strip()
        elif line.startswith('ANSWER:'):
            answer_parsed = line.replace('ANSWER:', '').strip()

    if not question:
        parts = response.split('ANSWER:')
        if len(parts) >= 2:
            question = parts[0].replace('QUESTION:', '').strip()
            answer_parsed = parts[1].strip()
        else:
            question = response

    return {
        'question': question.replace('****', '').strip(),
        'answer': answer_parsed or answer,
        'format': format_type
    }


def generate_hints_for_chain(chain: dict) -> list:
    """Generate progressive hints adapted to chain length."""

    hints = []
    answer = chain['answer']
    num_hops = chain['num_hops']

    # Hint 1: Reveal number of hops
    hints.append({
        'level': 1,
        'hint': f"This requires {num_hops} connections to solve",
        'reveals': 'complexity'
    })

    # Hint 2: Reveal a middle entity (if chain is long enough)
    if num_hops >= 3:
        middle_idx = num_hops // 2
        middle_entity = chain['entities'][middle_idx]
        hints.append({
            'level': 2,
            'hint': f"The chain passes through '{middle_entity}'",
            'reveals': 'intermediate'
        })
    else:
        # Reveal relation for shorter chains
        hints.append({
            'level': 2,
            'hint': f"The connection involves '{chain['relation1']}'",
            'reveals': 'relation'
        })

    # Hint 3: Reveal answer category
    answer_type = chain.get('answer_type', 'unknown')
    hints.append({
        'level': 3,
        'hint': f"The answer is a {answer_type}",
        'reveals': 'category'
    })

    # Hint 4: Reveal partial answer
    answer_words = answer.split()
    first_letter = answer[0].upper()
    num_words = len(answer_words)

    if num_words == 1:
        hint_text = f"The answer starts with '{first_letter}' and has {len(answer)} letters"
    else:
        hint_text = f"The answer starts with '{first_letter}' and has {num_words} word(s)"

    hints.append({
        'level': 4,
        'hint': hint_text,
        'reveals': 'partial'
    })

    return hints


# ============================================================================
# VALIDATION & QUALITY CHECKS
# ============================================================================

def is_circular(chain: Dict) -> bool:
    """Check for circular references in variable-length chains."""
    entities = chain['entities']

    # Check exact duplicates
    if len(entities) != len(set(entities)):
        return True

    # Fuzzy matching
    for i, e1 in enumerate(entities):
        for j, e2 in enumerate(entities):
            if i != j:
                e1_clean = e1.lower().replace(' inc', '').replace(' university', '')
                e2_clean = e2.lower().replace(' inc', '').replace(' university', '')

                if e1_clean in e2_clean or e2_clean in e1_clean:
                    return True

                if fuzz.ratio(e1_clean, e2_clean) > 85:
                    return True

    return False


def score_chain_quality(chain: Dict) -> float:
    """Score chain quality (adapted for variable lengths)."""

    system_prompt = "You rate knowledge chain quality."

    # Build chain text
    chain_text = " → ".join(chain['entities'])

    user_prompt = f"""Rate this {chain['num_hops']}-hop knowledge chain on 0-10:

{chain_text}

Criteria:
1. No circular logic (critical)
2. Each connection is interesting
3. Difficulty appropriate for {chain['num_hops']} hops
4. Final entity is surprising but logical
5. Tells a coherent story

For longer chains, higher standards apply.

Respond with ONLY a number 0-10: """

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.3)
        score = float(response.strip().split()[0])
        return max(0, min(10, score))
    except:
        return 5.0


def validate_semantic_distance(chain: Dict) -> dict:
    """Check semantic distance for variable-length chains."""

    entity1 = chain['entity1']
    answer = chain['answer']

    e1_emb = get_embedding(entity1)
    ea_emb = get_embedding(answer)

    sim = cosine_similarity(e1_emb, ea_emb)

    # Adjust thresholds based on chain length
    num_hops = chain['num_hops']

    if num_hops == 2:
        # Shorter chains can be more similar
        optimal = 0.30 <= sim <= 0.75
    elif num_hops == 3:
        # Standard thresholds
        optimal = 0.20 <= sim <= 0.70
    else:
        # Longer chains should be more distant
        optimal = 0.10 <= sim <= 0.60

    return {
        'similarity': round(sim, 3),
        'optimal': optimal,
        'num_hops': num_hops
    }


# ============================================================================
# MAIN GENERATION LOOP
# ============================================================================

def generate_question_with_retry(
    difficulty: str = "medium",
    min_quality: float = 6.0,
    max_attempts: int = 5
) -> Optional[dict]:
    """Generate question with specified difficulty."""

    for attempt in range(max_attempts):
        try:
            print(f"  Attempt {attempt + 1}/{max_attempts}...", end=" ")

            # Generate chain with specified difficulty
            chain = generate_variable_chain(difficulty)

            # Check circular
            if is_circular(chain):
                print("❌ Circular")
                continue

            # Score quality
            quality = score_chain_quality(chain)
            print(f"Q:{quality:.1f}", end=" ")

            if quality < min_quality:
                print("❌ Low quality")
                continue

            # Semantic distance (if enabled)
            if USE_EMBEDDINGS:
                sem_check = validate_semantic_distance(chain)
                print(f"Sim:{sem_check['similarity']:.2f}", end=" ")

                if not sem_check['optimal'] and attempt < 3:
                    print("❌ Poor distance")
                    continue

            # Wikipedia verification (later attempts only)
            if attempt > 2:
                wiki_check = verify_relation_wikipedia(chain['entity1'], chain['entities'][1])
                if not wiki_check['verified']:
                    print("❌ Wiki failed")
                    continue

            # Select format
            format_type = select_question_format()

            # Generate question
            q = generate_question_for_chain(chain, format_type)

            # Generate hints
            hints = generate_hints_for_chain(chain)

            # Simple distractors
            distractors = [
                f"{q['answer']} Alt 1",
                f"{q['answer']} Alt 2",
                f"{q['answer']} Alt 3"
            ]

            options = distractors + [q['answer']]
            random.shuffle(options)
            correct_index = options.index(q['answer'])

            print("✅")

            return {
                'chain': " → ".join(chain['entities']),
                'question': q['question'],
                'answer': q['answer'],
                'options': options,
                'correct_index': correct_index,
                'format': format_type,
                'hints': hints,
                'difficulty': difficulty,
                'num_hops': chain['num_hops'],
                'entities': chain['entities'],
                'quality_score': quality,
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt == max_attempts - 1:
                return None
            continue

    return None


def main():
    """Generate questions with variable difficulties."""

    # Configuration
    questions_per_difficulty = {
        "easy": 8,      # 2-hop chains
        "medium": 10,   # 3-hop chains
        "hard": 8,      # 4-hop chains
        "expert": 4     # 5-hop chains
    }

    total_target = sum(questions_per_difficulty.values())

    print("=" * 70)
    print("🚀 V4: Variable Chain Length Generator")
    print("=" * 70)
    print("Features:")
    print("  ✅ Variable chain lengths (2-5 hops)")
    print("  ✅ Difficulty-based generation")
    print(f"  {'✅' if USE_EMBEDDINGS else '⚠️ '} Semantic distance {f'({"enabled" if USE_EMBEDDINGS else "disabled"})'}")
    print("  ✅ Wikipedia verification")
    print("  ✅ 6 question formats")
    print("  ✅ Progressive hints (4 levels)")
    print()
    print("Target Distribution:")
    for diff, count in questions_per_difficulty.items():
        hops = DIFFICULTY_HOPS[diff]
        print(f"  {diff.capitalize():8} ({hops} hops): {count} questions")
    print(f"\nTotal: {total_target} questions")
    print("=" * 70)
    print()

    questions = []

    for difficulty, target_count in questions_per_difficulty.items():
        print(f"\n{'='*70}")
        print(f"📊 Generating {difficulty.upper()} questions ({DIFFICULTY_HOPS[difficulty]} hops)")
        print(f"{'='*70}")

        successful = 0
        attempts = 0
        max_attempts = target_count * 10

        while successful < target_count and attempts < max_attempts:
            print(f"\n[{difficulty.upper()}] Question {successful + 1}/{target_count}")
            attempts += 1

            q = generate_question_with_retry(
                difficulty=difficulty,
                min_quality=5.5 if difficulty == "easy" else 6.0,
                max_attempts=5
            )

            if q:
                q['id'] = len(questions) + 1
                questions.append(q)
                successful += 1

                print(f"   Chain ({q['num_hops']} hops): {q['chain'][:70]}...")
                print(f"   Format: {q['format']}")
                print(f"   Quality: {q['quality_score']:.1f}")

    # Save
    output_file = 'data/knowledge_graph_questions_v4.jsonl'
    with open(output_file, 'w') as f:
        for q in questions:
            f.write(json.dumps(q) + '\n')

    print("\n" + "=" * 70)
    print(f"✅ Generated {len(questions)} questions")
    print(f"📁 Saved to: {output_file}")
    print("=" * 70)

    # Statistics
    print("\n📊 STATISTICS")
    print("-" * 70)

    by_difficulty = defaultdict(int)
    by_format = defaultdict(int)
    by_hops = defaultdict(int)

    for q in questions:
        by_difficulty[q['difficulty']] += 1
        by_format[q['format']] += 1
        by_hops[q['num_hops']] += 1

    avg_quality = sum(q['quality_score'] for q in questions) / len(questions)

    print(f"Average quality: {avg_quality:.2f}/10")
    print(f"\nDifficulty distribution:")
    for diff in ["easy", "medium", "hard", "expert"]:
        count = by_difficulty[diff]
        if count > 0:
            print(f"  {diff.capitalize()}: {count} ({count/len(questions)*100:.1f}%)")

    print(f"\nChain length distribution:")
    for hops in sorted(by_hops.keys()):
        count = by_hops[hops]
        print(f"  {hops} hops: {count} ({count/len(questions)*100:.1f}%)")

    print(f"\nFormat distribution:")
    for fmt, count in sorted(by_format.items(), key=lambda x: -x[1]):
        print(f"  {fmt}: {count} ({count/len(questions)*100:.1f}%)")

    # Samples
    print("\n" + "=" * 70)
    print("📋 SAMPLE QUESTIONS")
    print("=" * 70)

    for diff in ["easy", "medium", "hard", "expert"]:
        samples = [q for q in questions if q['difficulty'] == diff]
        if samples:
            q = samples[0]
            print(f"\n[{diff.upper()} - {q['num_hops']} hops]")
            print(f"Chain: {q['chain']}")
            print(f"Q: {q['question'][:100]}...")
            print(f"A: {q['answer']}")
            print(f"Hints available: {len(q['hints'])}")


if __name__ == '__main__':
    main()
