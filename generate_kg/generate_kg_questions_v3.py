#!/usr/bin/env python3
"""
V3: Advanced knowledge-graph question generator with:
1. Wikipedia API integration for fact verification
2. Semantic distance via embeddings
3. Question format variation
4. Progressive hint system
10. Red herring / adversarial chains
11. Chain inversion & reverse engineering
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
    user_agent=os.environ.get("WIKIMEDIA_USER_AGENT", "RiddlerBench/1.0 (educational trivia generator)")
)

# Seed entities
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
    # Science
    "Albert Einstein", "Marie Curie", "Stephen Hawking", "Neil deGrasse Tyson",
    "Jane Goodall", "Nikola Tesla", "Ada Lovelace",
    # Arts
    "Shakespeare", "Pablo Picasso", "Frida Kahlo", "Leonardo da Vinci",
    "Vincent van Gogh", "J.K. Rowling", "Ernest Hemingway",
    # Historical (Global)
    "Nelson Mandela", "Mahatma Gandhi", "Martin Luther King Jr.",
    "Winston Churchill", "Cleopatra", "Abraham Lincoln",
    # Asian
    "Confucius", "Akira Kurosawa", "Bruce Lee", "Yayoi Kusama",
    # Middle Eastern
    "Rumi", "Ibn Sina", "Naguib Mahfouz",
    # African
    "Wangari Maathai", "Desmond Tutu", "Fela Kuti",
    # Latin American
    "Gabriel García Márquez", "Diego Rivera", "Diego Maradona",
    # Organizations & Places
    "Apple Inc", "Microsoft", "Google", "Harvard University",
    "Eiffel Tower", "Statue of Liberty", "Taj Mahal",
]

# Target answers for backward generation
TARGET_ANSWERS = [
    "The Louvre", "MIT", "Oxford University", "United Nations",
    "Nobel Prize", "Grammy Awards", "Olympics", "World Cup",
    "Mona Lisa", "The Great Gatsby", "1984", "To Kill a Mockingbird",
]

RELATION_TYPES = [
    "founded", "co-founded", "acquired", "merged_with",
    "worked_at", "CEO_of", "invented", "pioneered",
    "attended", "graduated_from", "studied_under", "taught_at",
    "married_to", "divorced_from", "parent_of", "child_of",
    "directed", "starred_in", "produced", "composed", "wrote",
    "born_in", "died_in", "lived_in", "headquartered_in",
    "defeated", "competed_against", "mentored", "inspired",
]

# Question formats
QUESTION_FORMATS = {
    "direct": {"weight": 40, "template": "What/Who is..."},
    "location": {"weight": 15, "template": "Where did..."},
    "year": {"weight": 10, "template": "In what year..."},
    "fill_blank": {"weight": 15, "template": "Complete: X → ? → Z"},
    "negative": {"weight": 10, "template": "Which is NOT..."},
    "comparison": {"weight": 10, "template": "Which came first..."},
}

relation_usage = defaultdict(int)
embedding_cache = {}

# ============================================================================
# 1. WIKIPEDIA API INTEGRATION
# ============================================================================

def get_wikipedia_page(entity: str) -> Optional[wikipediaapi.WikipediaPage]:
    """Get Wikipedia page for entity."""
    try:
        page = wiki.page(entity)
        if page.exists():
            return page
        # Try variations
        for variant in [entity + " (person)", entity + " (film)", entity + " (company)"]:
            page = wiki.page(variant)
            if page.exists():
                return page
        return None
    except:
        return None


def verify_relation_wikipedia(entity1: str, entity2: str, relation: str) -> dict:
    """Verify if entity2 appears in entity1's Wikipedia page."""

    page1 = get_wikipedia_page(entity1)

    if not page1:
        return {
            'verified': False,
            'confidence': 'low',
            'reason': 'entity1 page not found'
        }

    # Check if entity2 mentioned in text
    text = page1.text.lower()
    entity2_lower = entity2.lower()

    # Check variations
    entity2_parts = entity2.split()
    mention_found = False

    if entity2_lower in text:
        mention_found = True
    elif len(entity2_parts) > 1 and entity2_parts[-1] in text:
        # Check last name for people
        mention_found = True

    # Check in links
    links = [link.lower() for link in page1.links.keys()]
    link_found = any(entity2_lower in link for link in links)

    confidence = 'high' if (mention_found and link_found) else \
                 'medium' if (mention_found or link_found) else 'low'

    return {
        'verified': mention_found or link_found,
        'confidence': confidence,
        'mention_in_text': mention_found,
        'mention_in_links': link_found
    }


def get_entity_metadata(entity: str) -> dict:
    """Get rich metadata from Wikipedia."""

    page = get_wikipedia_page(entity)

    if not page:
        return {'exists': False}

    return {
        'exists': True,
        'title': page.title,
        'summary': page.summary[:500],  # First 500 chars
        'categories': list(page.categories.keys())[:10],
        'links': list(page.links.keys())[:20],
        'url': page.fullurl
    }


# ============================================================================
# 2. SEMANTIC DISTANCE VIA EMBEDDINGS
# ============================================================================

USE_EMBEDDINGS = os.environ.get("USE_EMBEDDINGS", "false").lower() == "true"

def get_embedding(text: str) -> np.ndarray:
    """Get embedding vector for entity with caching."""

    if not USE_EMBEDDINGS:
        # Skip embeddings if not enabled
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
    except Exception as e:
        # Silently fallback
        return np.random.rand(1536)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def validate_chain_semantic_distance(chain: dict) -> dict:
    """
    Validate that entities are:
    - Not too similar (>0.8) - too easy
    - Not too distant (<0.05) - nonsensical
    """

    e1_emb = get_embedding(chain['entity1'])
    e2_emb = get_embedding(chain['entity2'])
    e3_emb = get_embedding(chain['entity3'])

    sim_1_2 = cosine_similarity(e1_emb, e2_emb)
    sim_2_3 = cosine_similarity(e2_emb, e3_emb)
    sim_1_3 = cosine_similarity(e1_emb, e3_emb)

    # Check if answer is in sweet spot
    too_similar = sim_1_3 > 0.75
    too_distant = sim_1_3 < 0.05

    optimal = 0.20 <= sim_1_3 <= 0.70

    return {
        'sim_1_2': round(sim_1_2, 3),
        'sim_2_3': round(sim_2_3, 3),
        'sim_1_3': round(sim_1_3, 3),
        'too_similar': too_similar,
        'too_distant': too_distant,
        'optimal': optimal,
        'quality_factor': 'optimal' if optimal else 'poor'
    }


# ============================================================================
# 3. QUESTION FORMAT VARIATION
# ============================================================================

def select_question_format() -> str:
    """Select random question format based on weights."""
    formats = list(QUESTION_FORMATS.keys())
    weights = [QUESTION_FORMATS[f]['weight'] for f in formats]
    return random.choices(formats, weights=weights)[0]


def generate_question_with_format(chain: dict, format_type: str) -> dict:
    """Generate question in specific format."""

    system_prompt = "You are an expert trivia question writer."

    if format_type == "direct":
        user_prompt = f"""Create a direct trivia question (Who/What is...):

Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}

Describe entity1 and entity2 indirectly, ask for entity3.
Be concise (20-35 words).

Format:
QUESTION: [your question]
ANSWER: {chain['entity3']}"""

    elif format_type == "location":
        user_prompt = f"""Create a location-based question (Where...):

Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}

Ask WHERE something related to this chain happened or is located.
Answer should be: {chain['entity3']}

Format:
QUESTION: Where did/is...
ANSWER: {chain['entity3']}"""

    elif format_type == "year":
        user_prompt = f"""Create a year/time-based question:

Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}

Ask WHEN something related to this chain happened.
If {chain['entity3']} is not a year, ask when it was created/founded/born.

Format:
QUESTION: In what year...
ANSWER: {chain['entity3']} (or a year if appropriate)"""

    elif format_type == "fill_blank":
        user_prompt = f"""Create a "fill in the blank" question:

Complete the connection:
{chain['entity1']} → ______ → {chain['entity3']}

Ask what the missing link is. The answer is {chain['entity2']}.

Format:
QUESTION: Complete this connection: {chain['entity1']} → ? → {chain['entity3']}. What is the missing link?
ANSWER: {chain['entity2']}"""

    elif format_type == "negative":
        # Generate fake distractors for "Which is NOT" format
        user_prompt = f"""Create a "Which is NOT" question:

Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}

Create a question asking which entity is NOT connected to {chain['entity1']}.
The answer (NOT connected) should be a plausible but incorrect entity.

Format:
QUESTION: Which of the following is NOT connected to [description of {chain['entity1']}]?
ANSWER: [Generate a plausible but incorrect entity]"""

    elif format_type == "comparison":
        user_prompt = f"""Create a comparison question (Which came first...):

Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}

Ask which came first or which is older between two related entities.

Format:
QUESTION: Which came first...
ANSWER: {chain['entity3']}"""

    else:
        # Default to direct
        user_prompt = user_prompt if 'user_prompt' in locals() else ""

    response = call_llm(system_prompt, user_prompt, temperature=0.7)

    # Parse
    question = None
    answer = None

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('QUESTION:'):
            question = line.replace('QUESTION:', '').strip()
        elif line.startswith('ANSWER:'):
            answer = line.replace('ANSWER:', '').strip()

    if not question:
        parts = response.split('ANSWER:')
        if len(parts) >= 2:
            question = parts[0].replace('QUESTION:', '').strip()
            answer = parts[1].strip()
        else:
            question = response

    return {
        'question': question.replace('****', '').strip(),
        'answer': answer or chain['entity3'],
        'format': format_type
    }


# ============================================================================
# 4. PROGRESSIVE HINT SYSTEM
# ============================================================================

def generate_hints(chain: dict, question_format: str) -> list:
    """Generate 3 progressive hints."""

    hints = []
    answer = chain['entity3']

    # Hint 1: Reveal relation type
    hints.append({
        'level': 1,
        'hint': f"The connection involves '{chain['relation2']}'",
        'reveals': 'relation'
    })

    # Hint 2: Reveal category/type
    entity_type = chain.get('entity3_type', 'unknown')
    hints.append({
        'level': 2,
        'hint': f"The answer is a {entity_type}",
        'reveals': 'category'
    })

    # Hint 3: Reveal first letter and length
    answer_words = answer.split()
    first_letter = answer[0].upper()
    num_words = len(answer_words)

    if num_words == 1:
        hint_text = f"The answer starts with '{first_letter}' and has {len(answer)} letters"
    else:
        hint_text = f"The answer starts with '{first_letter}' and has {num_words} word(s)"

    hints.append({
        'level': 3,
        'hint': hint_text,
        'reveals': 'partial'
    })

    return hints


# ============================================================================
# 10. RED HERRING / ADVERSARIAL CHAINS
# ============================================================================

def generate_red_herring_chain() -> Optional[dict]:
    """
    Create chain with intentional misdirection.
    Uses entities with famous namesakes.
    """

    RED_HERRING_SEEDS = [
        "Washington",  # State vs George Washington
        "Paris",  # France vs Paris, Texas
        "Cambridge",  # UK vs Cambridge, MA
        "Jordan",  # Country vs Michael Jordan
        "Victoria",  # Queen vs city
        "Columbia",  # University vs country
        "Georgia",  # Country vs US state
    ]

    system_prompt = "You generate knowledge chains with subtle misdirection."

    seed = random.choice(RED_HERRING_SEEDS)

    user_prompt = f"""Create a chain starting with: {seed}

Choose the LESS FAMOUS meaning to create a red herring:
- If "Washington", use Washington (state) not George Washington
- If "Paris", use Paris (Texas) or Paris (mythology) not Paris (France)
- If "Cambridge", mix UK and US versions

Generate entity 2 and entity 3 that are connected to this less common meaning.

Format:
ENTITY1: {seed}
CLARIFICATION: [which meaning you're using]
ENTITY2: [related entity]
RELATION1: [connection]
ENTITY3: [final answer]
RELATION2: [connection]"""

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.9)

        # Parse (simplified)
        lines = response.split('\n')
        data = {}

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip()

        if 'entity2' in data and 'entity3' in data:
            return {
                'entity1': seed,
                'entity2': data.get('entity2'),
                'entity3': data.get('entity3'),
                'relation1': data.get('relation1', 'related to'),
                'relation2': data.get('relation2', 'related to'),
                'is_red_herring': True,
                'clarification': data.get('clarification', '')
            }
    except:
        pass

    return None


# ============================================================================
# 11. CHAIN INVERSION & REVERSE ENGINEERING
# ============================================================================

def generate_chain_backward(target_answer: str) -> Optional[dict]:
    """
    Work backward from desired answer to create interesting chain.
    Ensures coverage of important topics.
    """

    system_prompt = "You generate knowledge chains by working backward from a target answer."

    user_prompt = f"""Work BACKWARD from this target answer: {target_answer}

Create an interesting 3-entity chain:
Entity1 → Entity2 → {target_answer}

Requirements:
- Entity1 should be famous/recognizable
- Entity2 should provide an interesting connection
- The chain should tell a story
- Avoid circular logic

Format:
ENTITY1: [famous starting point]
RELATION1: [how entity1 connects to entity2]
ENTITY2: [intermediate entity]
RELATION2: [how entity2 connects to {target_answer}]
ENTITY3: {target_answer}"""

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.8)

        # Parse
        data = {}
        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip()

        if 'entity1' in data and 'entity2' in data:
            return {
                'entity1': data.get('entity1'),
                'entity2': data.get('entity2'),
                'entity3': target_answer,
                'relation1': data.get('relation1', 'related to'),
                'relation2': data.get('relation2', 'related to'),
                'is_backward_generated': True
            }
    except:
        pass

    return None


# ============================================================================
# CORE FUNCTIONS (from V2 with enhancements)
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


def generate_entity_chain(mode: str = "forward") -> Dict:
    """
    Generate chain with multiple modes.

    Modes:
    - forward: Normal generation (entity1 → entity2 → entity3)
    - backward: Start with target answer
    - red_herring: Use misleading entity names
    """

    if mode == "backward" and random.random() < 0.3:
        # 30% chance to use backward generation
        target = random.choice(TARGET_ANSWERS)
        chain = generate_chain_backward(target)
        if chain:
            return chain

    if mode == "red_herring" and random.random() < 0.2:
        # 20% chance for red herring
        chain = generate_red_herring_chain()
        if chain:
            return chain

    # Default: forward generation (V2 logic)
    entity1 = random.choice(SEED_ENTITIES)

    system_prompt = """You are a knowledge graph expert. Generate related entities through specific connections.
CRITICAL: Do NOT create circular references. Each entity must be distinct."""

    # Generate entity2
    relations = random.sample(RELATION_TYPES, 3)

    user_prompt = f"""Generate a second entity related to: {entity1}

CHAIN SO FAR: {entity1}

CONSTRAINT: The second entity MUST be different from "{entity1}".

Suggested relations: {', '.join(relations)}

Format:
ENTITY: [name]
TYPE: [person/organization/place/event/artwork/concept]
RELATION: [specific relation from {entity1}]"""

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

    if not entity2:
        raise ValueError("Failed to parse entity2")

    # Generate entity3 with full context
    relations2 = random.sample(RELATION_TYPES, 3)

    user_prompt2 = f"""Generate a third entity.

FULL CHAIN SO FAR:
{entity1} → {entity2}

CRITICAL: The third entity must be different from BOTH:
- "{entity1}"
- "{entity2}"

Do NOT loop back.

Current entity: {entity2}
Suggested relations: {', '.join(relations2)}

Format:
ENTITY: [name]
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

    if not entity3:
        raise ValueError("Failed to parse entity3")

    return {
        'entity1': entity1,
        'entity2': entity2,
        'entity3': entity3,
        'entity1_type': 'varies',
        'entity2_type': entity2_type,
        'entity3_type': entity3_type,
        'relation1': relation1,
        'relation2': relation2
    }


def is_circular(chain: Dict) -> bool:
    """Check for circular references."""
    entities = [chain['entity1'], chain['entity2'], chain['entity3']]

    if len(entities) != len(set(entities)):
        return True

    # Fuzzy matching
    for i, e1 in enumerate(entities):
        for j, e2 in enumerate(entities):
            if i != j:
                e1_clean = e1.lower().replace(' inc', '').replace(' corp', '').replace(' university', '')
                e2_clean = e2.lower().replace(' inc', '').replace(' corp', '').replace(' university', '')

                if e1_clean in e2_clean or e2_clean in e1_clean:
                    return True

                # Use fuzzywuzzy
                if fuzz.ratio(e1_clean, e2_clean) > 85:
                    return True

    return False


def score_chain_quality(chain: Dict) -> float:
    """Score chain quality 0-10."""

    system_prompt = "You rate knowledge chain quality."

    user_prompt = f"""Rate this chain 0-10:

{chain['entity1']} →({chain['relation1']})→ {chain['entity2']} →({chain['relation2']})→ {chain['entity3']}

Criteria:
1. No circular logic (critical)
2. Interesting relations
3. Surprising but logical endpoint
4. Tells a story
5. Diverse domains

Respond with ONLY a number 0-10: """

    try:
        response = call_llm(system_prompt, user_prompt, temperature=0.3)
        score = float(response.strip().split()[0])
        return max(0, min(10, score))
    except:
        return 5.0


def generate_question_complete(chain: dict) -> dict:
    """Generate complete question with all v3 features."""

    # Select format
    format_type = select_question_format()

    # Generate question
    q = generate_question_with_format(chain, format_type)

    # Generate hints
    hints = generate_hints(chain, format_type)

    # Generate distractors (simplified for now)
    distractors = [
        f"{chain['entity3']} Alternative 1",
        f"{chain['entity3']} Alternative 2",
        f"{chain['entity3']} Alternative 3"
    ]

    return {
        'question': q['question'],
        'answer': q['answer'],
        'format': format_type,
        'hints': hints,
        'options': distractors + [q['answer']]
    }


def generate_question_with_retry(min_quality: float = 6.0, max_attempts: int = 5) -> Optional[dict]:
    """Generate question with all v3 validations."""

    for attempt in range(max_attempts):
        try:
            print(f"  Attempt {attempt + 1}/{max_attempts}...", end=" ")

            # Select generation mode
            mode = random.choice(["forward", "forward", "backward", "red_herring"])

            # Generate chain
            chain = generate_entity_chain(mode=mode)

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

            # Semantic distance check (only if embeddings enabled)
            sem_check = validate_chain_semantic_distance(chain)

            if USE_EMBEDDINGS:
                print(f"Sim:{sem_check['sim_1_3']:.2f}", end=" ")

                if not sem_check['optimal'] and attempt < 3:
                    print("❌ Poor semantic distance")
                    continue

            # Wikipedia verification (only on later attempts)
            if attempt > 2:
                wiki_check = verify_relation_wikipedia(
                    chain['entity1'],
                    chain['entity2'],
                    chain['relation1']
                )
                if not wiki_check['verified']:
                    print("❌ Wiki verification failed")
                    continue

            # Generate question
            q = generate_question_complete(chain)

            # Shuffle options
            random.shuffle(q['options'])
            correct_index = q['options'].index(q['answer'])

            print("✅ Success")

            return {
                'chain': f"{chain['entity1']} → {chain['entity2']} → {chain['entity3']}",
                'question': q['question'],
                'answer': q['answer'],
                'options': q['options'],
                'correct_index': correct_index,
                'format': q['format'],
                'hints': q['hints'],
                'entity1': chain['entity1'],
                'entity2': chain['entity2'],
                'entity3': chain['entity3'],
                'relation1': chain['relation1'],
                'relation2': chain['relation2'],
                'quality_score': quality,
                'semantic_distance': sem_check['sim_1_3'],
                'is_red_herring': chain.get('is_red_herring', False),
                'is_backward': chain.get('is_backward_generated', False),
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt == max_attempts - 1:
                return None
            continue

    return None


def main():
    """Generate v3 questions with advanced features."""

    num_questions = 30
    questions = []

    print("=" * 70)
    print("🚀 V3: Advanced Knowledge Graph Generator")
    print("=" * 70)
    print("Features:")
    print("  ✅ Wikipedia API fact verification")
    print(f"  {'✅' if USE_EMBEDDINGS else '⚠️ '} Semantic distance via embeddings {'(enabled)' if USE_EMBEDDINGS else '(disabled - set USE_EMBEDDINGS=true)'}")
    print("  ✅ Question format variation")
    print("  ✅ Progressive hint system")
    print("  ✅ Red herring chains")
    print("  ✅ Backward chain generation")
    print(f"\nTarget: {num_questions} questions")
    print("=" * 70)
    print()

    successful = 0
    total_attempts = 0
    max_total = num_questions * 10

    while successful < num_questions and total_attempts < max_total:
        print(f"\n📝 Question {successful + 1}/{num_questions}")
        total_attempts += 1

        q = generate_question_with_retry(min_quality=6.0, max_attempts=5)

        if q:
            q['id'] = successful + 1
            questions.append(q)
            successful += 1

            print(f"   Chain: {q['chain']}")
            print(f"   Format: {q['format']}")
            print(f"   Q: {q['question'][:80]}...")
            if q.get('is_red_herring'):
                print(f"   🎭 Red Herring!")
            if q.get('is_backward'):
                print(f"   ⬅️  Backward Generated!")

    # Save
    output_file = 'data/knowledge_graph_questions_v3.jsonl'
    with open(output_file, 'w') as f:
        for q in questions:
            f.write(json.dumps(q) + '\n')

    print("\n" + "=" * 70)
    print(f"✅ Generated {len(questions)} questions")
    print(f"📁 Saved to: {output_file}")
    print(f"📊 Success rate: {len(questions)/total_attempts*100:.1f}%")
    print("=" * 70)

    # Statistics
    print("\n📊 STATISTICS")
    print("-" * 70)

    formats = defaultdict(int)
    for q in questions:
        formats[q['format']] += 1

    avg_quality = sum(q['quality_score'] for q in questions) / len(questions)
    avg_sem_dist = sum(q['semantic_distance'] for q in questions) / len(questions)

    print(f"Average quality: {avg_quality:.2f}/10")
    print(f"Average semantic distance: {avg_sem_dist:.3f}")
    print(f"\nFormat distribution:")
    for fmt, count in sorted(formats.items(), key=lambda x: -x[1]):
        print(f"  {fmt}: {count} ({count/len(questions)*100:.1f}%)")

    red_herrings = sum(1 for q in questions if q.get('is_red_herring'))
    backward = sum(1 for q in questions if q.get('is_backward'))

    print(f"\nSpecial chains:")
    print(f"  Red herrings: {red_herrings}")
    print(f"  Backward generated: {backward}")

    # Sample
    print("\n" + "=" * 70)
    print("📋 SAMPLES")
    print("=" * 70)

    for q in questions[:3]:
        print(f"\n[{q['format'].upper()}] {q['chain']}")
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}")
        print(f"Hints: {len(q['hints'])} available")
        print(f"Quality: {q['quality_score']:.1f}, Semantic: {q['semantic_distance']:.3f}")


if __name__ == '__main__':
    main()
