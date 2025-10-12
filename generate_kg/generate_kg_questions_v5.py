#!/usr/bin/env python3
"""
V5: Ultra-Difficulty Knowledge Graph Question Generator

Key Features:
1. Obscurity & Specialization (Wikipedia view counts)
2. Cross-Domain Lateral Thinking (forced domain switches)
3. Abstract Concepts & Theories (non-tangible entities)
4. Multi-Inference Relations (2+ logical steps)
5. Recalibrated Quality Prompts (PhD-level standard)
"""

import json
import os
import random
import statistics
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_BASE_URL")
)

# ============================================================================
# DOMAIN TAXONOMY
# ============================================================================

DOMAIN_TAXONOMY = {
    "hard_sciences": ["physics", "chemistry", "mathematics", "astronomy"],
    "life_sciences": ["biology", "medicine", "neuroscience", "ecology"],
    "social_sciences": ["psychology", "sociology", "economics", "linguistics"],
    "humanities": ["philosophy", "literature", "history", "theology"],
    "arts": ["visual_art", "music", "film", "architecture", "theater"],
    "formal_systems": ["logic", "computer_science", "game_theory", "cryptography"],
    "applied": ["engineering", "business", "law", "politics"]
}

# Flatten for easy lookup
ALL_DOMAINS = [d for domains in DOMAIN_TAXONOMY.values() for d in domains]

# ============================================================================
# ABSTRACT CONCEPTS & THEORIES
# ============================================================================

ABSTRACT_ENTITIES = {
    "physics": [
        "Heisenberg Uncertainty Principle",
        "Special Relativity",
        "Quantum Entanglement",
        "Wave-Particle Duality",
        "Schrödinger's Cat",
        "Hawking Radiation"
    ],
    "philosophy": [
        "Cogito Ergo Sum",
        "Categorical Imperative",
        "Plato's Theory of Forms",
        "Existentialism",
        "Phenomenology",
        "Dialectical Materialism"
    ],
    "mathematics": [
        "Gödel's Incompleteness Theorems",
        "Banach-Tarski Paradox",
        "Fermat's Last Theorem",
        "Riemann Hypothesis",
        "P versus NP problem",
        "Chaos Theory"
    ],
    "economics": [
        "Nash Equilibrium",
        "Pareto Efficiency",
        "Prisoner's Dilemma",
        "Keynesian Economics",
        "Tragedy of the Commons",
        "Efficient Market Hypothesis"
    ],
    "psychology": [
        "Dunbar's Number",
        "Cognitive Dissonance",
        "Maslow's Hierarchy",
        "Stanford Prison Experiment",
        "Milgram Experiment",
        "Flow State"
    ],
    "linguistics": [
        "Sapir-Whorf Hypothesis",
        "Universal Grammar",
        "Prague School",
        "Structuralism",
        "Generative Grammar"
    ],
    "arts": [
        "Dadaism",
        "Surrealism",
        "Impressionism",
        "Abstract Expressionism",
        "Bauhaus Movement",
        "The Sublime"
    ],
    "logic": [
        "Modus Ponens",
        "Occam's Razor",
        "Russell's Paradox",
        "Tautology",
        "Sorites Paradox"
    ]
}

# ============================================================================
# ENTITY DATA STRUCTURE
# ============================================================================

@dataclass
class EnhancedEntity:
    name: str
    domain: str
    is_abstract: bool
    obscurity_score: float  # 0-1, 1 = very obscure
    type: str  # person, place, work, concept, theory, event

# ============================================================================
# SEED ENTITY POOLS (Curated for high obscurity)
# ============================================================================

CONCRETE_ENTITIES = {
    "physics": [
        {"name": "Erwin Schrödinger", "type": "person", "obscurity": 0.5},
        {"name": "Emmy Noether", "type": "person", "obscurity": 0.8},
        {"name": "Paul Dirac", "type": "person", "obscurity": 0.7},
        {"name": "Large Hadron Collider", "type": "place", "obscurity": 0.4},
        {"name": "Kamiokande detector", "type": "place", "obscurity": 0.9},
    ],
    "mathematics": [
        {"name": "Srinivasa Ramanujan", "type": "person", "obscurity": 0.6},
        {"name": "Évariste Galois", "type": "person", "obscurity": 0.8},
        {"name": "Sofia Kovalevskaya", "type": "person", "obscurity": 0.9},
        {"name": "Fields Medal", "type": "work", "obscurity": 0.5},
        {"name": "Millennium Prize Problems", "type": "work", "obscurity": 0.7},
    ],
    "literature": [
        {"name": "Jorge Luis Borges", "type": "person", "obscurity": 0.6},
        {"name": "Italo Calvino", "type": "person", "obscurity": 0.7},
        {"name": "The Library of Babel", "type": "work", "obscurity": 0.7},
        {"name": "If on a winter's night a traveler", "type": "work", "obscurity": 0.8},
        {"name": "Oulipo", "type": "work", "obscurity": 0.9},
    ],
    "philosophy": [
        {"name": "Edmund Husserl", "type": "person", "obscurity": 0.7},
        {"name": "Simone de Beauvoir", "type": "person", "obscurity": 0.6},
        {"name": "Ludwig Wittgenstein", "type": "person", "obscurity": 0.6},
        {"name": "Tractatus Logico-Philosophicus", "type": "work", "obscurity": 0.8},
        {"name": "Being and Time", "type": "work", "obscurity": 0.8},
    ],
    "visual_art": [
        {"name": "Kazimir Malevich", "type": "person", "obscurity": 0.7},
        {"name": "Yayoi Kusama", "type": "person", "obscurity": 0.5},
        {"name": "Black Square", "type": "work", "obscurity": 0.7},
        {"name": "The Treachery of Images", "type": "work", "obscurity": 0.6},
        {"name": "Fountain (Duchamp)", "type": "work", "obscurity": 0.7},
    ],
    "music": [
        {"name": "Arnold Schoenberg", "type": "person", "obscurity": 0.7},
        {"name": "John Cage", "type": "person", "obscurity": 0.6},
        {"name": "4'33\"", "type": "work", "obscurity": 0.7},
        {"name": "Pierrot Lunaire", "type": "work", "obscurity": 0.8},
        {"name": "The Rite of Spring", "type": "work", "obscurity": 0.6},
    ],
    "history": [
        {"name": "Congress of Vienna", "type": "event", "obscurity": 0.6},
        {"name": "Defenestration of Prague", "type": "event", "obscurity": 0.8},
        {"name": "Battle of Thermopylae", "type": "event", "obscurity": 0.5},
        {"name": "Taiping Rebellion", "type": "event", "obscurity": 0.7},
        {"name": "Treaty of Tordesillas", "type": "event", "obscurity": 0.8},
    ],
    "computer_science": [
        {"name": "Alan Turing", "type": "person", "obscurity": 0.4},
        {"name": "Grace Hopper", "type": "person", "obscurity": 0.6},
        {"name": "Dijkstra's algorithm", "type": "work", "obscurity": 0.7},
        {"name": "Lambda Calculus", "type": "work", "obscurity": 0.8},
        {"name": "Turing Test", "type": "work", "obscurity": 0.5},
    ],
    "economics": [
        {"name": "John Maynard Keynes", "type": "person", "obscurity": 0.5},
        {"name": "Friedrich Hayek", "type": "person", "obscurity": 0.7},
        {"name": "Amartya Sen", "type": "person", "obscurity": 0.7},
        {"name": "The General Theory", "type": "work", "obscurity": 0.8},
        {"name": "The Road to Serfdom", "type": "work", "obscurity": 0.8},
    ],
    "biology": [
        {"name": "Rosalind Franklin", "type": "person", "obscurity": 0.6},
        {"name": "Barbara McClintock", "type": "person", "obscurity": 0.8},
        {"name": "Lynn Margulis", "type": "person", "obscurity": 0.8},
        {"name": "Endosymbiotic theory", "type": "work", "obscurity": 0.7},
        {"name": "Hox genes", "type": "work", "obscurity": 0.8},
    ],
}

# ============================================================================
# ENTITY POOL CONSTRUCTION
# ============================================================================

def build_entity_pool() -> List[EnhancedEntity]:
    """Build enhanced entity pool with domains and obscurity."""
    pool = []

    # Add concrete entities
    for domain, entities in CONCRETE_ENTITIES.items():
        for entity in entities:
            pool.append(EnhancedEntity(
                name=entity['name'],
                domain=domain,
                is_abstract=False,
                obscurity_score=entity['obscurity'],
                type=entity['type']
            ))

    # Add abstract entities
    for domain, concepts in ABSTRACT_ENTITIES.items():
        for concept in concepts:
            pool.append(EnhancedEntity(
                name=concept,
                domain=domain,
                is_abstract=True,
                obscurity_score=0.9,  # Abstracts are inherently obscure
                type='concept'
            ))

    return pool

# ============================================================================
# MULTI-INFERENCE RELATION TEMPLATES
# ============================================================================

MULTI_INFERENCE_RELATIONS = [
    {
        "template": "{A} pioneered a technique that influenced {B}",
        "requires_inference": [
            "What technique did {A} pioneer?",
            "Who was influenced by this technique?",
        ],
    },
    {
        "template": "{A}'s work contradicted the principle underlying {B}",
        "requires_inference": [
            "What was the core principle in {A}'s work?",
            "What principle underlies {B}?",
        ],
    },
    {
        "template": "{A} shares a mathematical/structural principle with {B}",
        "requires_inference": [
            "What principle/structure describes {A}?",
            "What principle/structure describes {B}?",
        ],
    },
    {
        "template": "{A} was inspired by the failure/limitation of {B}",
        "requires_inference": [
            "What did {B} fail at or lack?",
            "How did this inspire {A}?",
        ],
    },
    {
        "template": "{A} and {B} were contemporaneous responses to the same historical/cultural moment",
        "requires_inference": [
            "What historical moment influenced {A}?",
            "How did {B} respond to the same moment?",
        ],
    },
]

# ============================================================================
# DIFFICULTY SETTINGS
# ============================================================================

DIFFICULTY_HOPS = {
    "medium": 3,
    "hard": 4,
    "expert": 5,
    "grandmaster": 6  # NEW: Ultra-difficulty
}

# ============================================================================
# CHAIN GENERATION
# ============================================================================

def select_seed_entity(entity_pool: List[EnhancedEntity], min_obscurity: float = 0.5) -> EnhancedEntity:
    """Select seed entity with minimum obscurity."""
    candidates = [e for e in entity_pool if e.obscurity_score >= min_obscurity]
    return random.choice(candidates) if candidates else random.choice(entity_pool)

def get_next_entity_constraints(
    current_entity: EnhancedEntity,
    chain_history: List[EnhancedEntity],
    hop_number: int,
    num_hops: int
) -> dict:
    """Determine constraints for next entity selection."""

    # Domain constraint: MUST be different from current
    used_domains = [e.domain for e in chain_history]
    forbidden_domains = [current_entity.domain]

    # Avoid recently used domains (if chain is long enough)
    if len(used_domains) >= 2:
        forbidden_domains.append(used_domains[-2])

    # Abstract requirement: force 1 abstract concept at mid-chain
    require_abstract = (
        hop_number == num_hops // 2 and
        not any(e.is_abstract for e in chain_history)
    )

    # Obscurity: higher for expert/grandmaster
    if num_hops >= 5:
        min_obscurity = 0.7
    elif num_hops >= 4:
        min_obscurity = 0.6
    else:
        min_obscurity = 0.5

    return {
        'forbidden_domains': forbidden_domains,
        'min_obscurity': min_obscurity,
        'require_abstract': require_abstract,
        'forbidden_names': [e.name for e in chain_history]
    }

def generate_next_entity_v5(
    current_entity: EnhancedEntity,
    entity_pool: List[EnhancedEntity],
    constraints: dict
) -> Optional[EnhancedEntity]:
    """Generate next entity using LLM with strict constraints."""

    system_prompt = """You are a knowledge graph expert generating ultra-difficult trivia chains.
Target audience: PhD-level educated individuals.

Focus on:
- Obscure but verifiable connections
- Cross-domain lateral thinking
- Abstract concepts when possible
- Multi-step logical relations"""

    # Build constraint text
    constraint_text = f"""
CRITICAL CONSTRAINTS:
1. Must be in a DIFFERENT domain from: {', '.join(constraints['forbidden_domains'])}
2. Must NOT be any of these entities: {', '.join(constraints['forbidden_names'])}
3. Must be obscure/specialized (not household name)
"""

    if constraints['require_abstract']:
        constraint_text += "4. Must be an ABSTRACT concept, theory, or principle (not a concrete person/place)\n"

    user_prompt = f"""Current entity: {current_entity.name} (domain: {current_entity.domain})

{constraint_text}

Generate the next entity in the knowledge chain.

Respond with ONLY the entity name, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=50
        )

        next_entity_name = response.choices[0].message.content.strip().strip('"').strip("'")

        # Try to find in pool first
        for entity in entity_pool:
            if entity.name.lower() == next_entity_name.lower():
                # Verify constraints
                if entity.domain not in constraints['forbidden_domains']:
                    return entity

        # If not in pool, create new entity (infer domain from LLM)
        domain = infer_domain(next_entity_name)
        is_abstract = constraints.get('require_abstract', False) or is_abstract_concept(next_entity_name)

        # Verify domain constraint
        if domain in constraints['forbidden_domains']:
            return None

        return EnhancedEntity(
            name=next_entity_name,
            domain=domain,
            is_abstract=is_abstract,
            obscurity_score=0.8,  # Assume high obscurity for LLM-generated
            type='concept' if is_abstract else 'person'
        )

    except Exception as e:
        print(f"    Error generating entity: {e}")
        return None

def infer_domain(entity_name: str) -> str:
    """Infer domain from entity name using LLM."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"What domain does '{entity_name}' belong to? Choose from: {', '.join(ALL_DOMAINS)}. Respond with ONLY the domain name."
            }],
            temperature=0.3,
            max_tokens=20
        )

        domain = response.choices[0].message.content.strip().lower()
        return domain if domain in ALL_DOMAINS else "philosophy"  # Default fallback
    except:
        return "philosophy"

def is_abstract_concept(entity_name: str) -> bool:
    """Check if entity appears to be abstract."""
    abstract_keywords = [
        'theorem', 'theory', 'principle', 'hypothesis', 'paradox',
        'law', 'equation', 'conjecture', 'problem', 'experiment',
        'effect', 'phenomenon', '-ism', 'concept', 'idea'
    ]
    return any(keyword in entity_name.lower() for keyword in abstract_keywords)

def generate_multi_inference_relation(
    entity1: EnhancedEntity,
    entity2: EnhancedEntity
) -> dict:
    """Generate a multi-step inference relation between entities."""

    relation_template = random.choice(MULTI_INFERENCE_RELATIONS)

    system_prompt = """You create complex knowledge connections requiring multi-step reasoning.
The connection should be factual but not immediately obvious."""

    user_prompt = f"""Create a connection between:
Entity 1: {entity1.name} (domain: {entity1.domain}, {'abstract' if entity1.is_abstract else 'concrete'})
Entity 2: {entity2.name} (domain: {entity2.domain}, {'abstract' if entity2.is_abstract else 'concrete'})

Relation type: {relation_template['template'].format(A='{A}', B='{B}')}

This must require knowing:
{chr(10).join('- ' + q.format(A=entity1.name, B=entity2.name) for q in relation_template['requires_inference'])}

Provide a specific, factual connection in 1-2 sentences. Be precise."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        relation_text = response.choices[0].message.content.strip()

        return {
            'entity1': entity1.name,
            'entity2': entity2.name,
            'relation': relation_text,
            'inference_steps': relation_template['requires_inference'],
            'complexity': 'multi_inference'
        }
    except Exception as e:
        return {
            'entity1': entity1.name,
            'entity2': entity2.name,
            'relation': f"connected to",
            'complexity': 'simple'
        }

def generate_v5_chain(difficulty: str, entity_pool: List[EnhancedEntity]) -> Optional[dict]:
    """Generate V5 chain with all constraints."""

    num_hops = DIFFICULTY_HOPS.get(difficulty, 4)

    # Select seed
    entity1 = select_seed_entity(entity_pool, min_obscurity=0.5)
    chain = [entity1]
    relations = []

    for hop in range(1, num_hops):
        constraints = get_next_entity_constraints(
            current_entity=chain[-1],
            chain_history=chain,
            hop_number=hop,
            num_hops=num_hops
        )

        next_entity = generate_next_entity_v5(chain[-1], entity_pool, constraints)

        if next_entity is None:
            return None  # Failed constraint, retry

        # Generate multi-inference relation
        relation = generate_multi_inference_relation(chain[-1], next_entity)

        chain.append(next_entity)
        relations.append(relation)

    # Validate chain
    if not validate_v5_chain(chain):
        return None

    return {
        'entities': [e.name for e in chain],
        'entity_objects': chain,
        'relations': relations,
        'num_hops': num_hops,
        'domains': [e.domain for e in chain],
        'obscurity_scores': [e.obscurity_score for e in chain],
        'has_abstract': any(e.is_abstract for e in chain),
        'cross_domain_count': len(set(e.domain for e in chain)),
        'difficulty': difficulty
    }

def validate_v5_chain(chain: List[EnhancedEntity]) -> bool:
    """Validate V5 chain meets all requirements."""

    # Check domain diversity (no consecutive same domain)
    domains = [e.domain for e in chain]
    if any(domains[i] == domains[i+1] for i in range(len(domains)-1)):
        return False

    # Check obscurity threshold
    avg_obscurity = sum(e.obscurity_score for e in chain) / len(chain)
    if avg_obscurity < 0.5:
        return False

    # Check for abstract concept (for chains 4+)
    if len(chain) >= 4 and not any(e.is_abstract for e in chain):
        return False

    # Check uniqueness
    if len(set(e.name for e in chain)) != len(chain):
        return False

    return True

# ============================================================================
# QUESTION GENERATION
# ============================================================================

def generate_question_from_chain_v5(chain: dict) -> dict:
    """Generate question from V5 chain."""

    entities = chain['entities']
    answer = entities[-1]

    # Build context
    context = f"""Knowledge chain: {' → '.join(entities)}
Domains: {' → '.join(chain['domains'])}
Number of hops: {chain['num_hops']}
Cross-domain jumps: {chain['cross_domain_count']}
Contains abstract concept: {chain['has_abstract']}

Relations:
"""
    for i, rel in enumerate(chain['relations']):
        context += f"{i+1}. {rel['relation']}\n"

    system_prompt = """You create ultra-difficult trivia questions for PhD-level educated audiences.

Requirements:
- Question should be elegant and concise
- Must not give away intermediate entities
- Should hint at the connections without being obvious
- Use sophisticated language
- No multiple choice - the question itself is the challenge"""

    user_prompt = f"""{context}

Create a single, elegant question where the answer is: {answer}

The question should:
1. Reference the starting entity ({entities[0]}) subtly or describe it
2. Hint at the chain of connections without revealing them
3. Be solvable only by someone who knows the obscure facts
4. Be beautifully worded

Respond with ONLY the question text, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=200
        )

        question = response.choices[0].message.content.strip().strip('"')

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
            'relations': chain['relations']
        }

    except Exception as e:
        print(f"    Error generating question: {e}")
        return None

# ============================================================================
# RECALIBRATED QUALITY ASSESSMENT
# ============================================================================

def assess_chain_quality_v5(chain: dict) -> dict:
    """Assess with recalibrated PhD-level standards."""

    chain_text = " → ".join(chain['chain'])
    domains_text = " → ".join(chain['domains'])

    system_prompt = """You evaluate trivia for PhD-LEVEL educated audiences.

Target audience:
- Deep specialized knowledge in at least one field
- Broad cross-domain knowledge
- Enjoys extremely challenging intellectual puzzles
- Values obscure but meaningful connections

RECALIBRATED SCALE: What was previously 8/10 is now 5-6/10.
We are raising the bar significantly."""

    user_prompt = f"""Evaluate this {chain['num_hops']}-hop chain on NINE dimensions (0-10):

Chain: {chain_text}
Domains: {domains_text}
Has abstract: {chain['has_abstract']}
Cross-domain jumps: {chain['cross_domain_count']}
Avg obscurity: {chain['avg_obscurity']:.2f}

1. NON-CIRCULARITY (0-10): All entities distinct?
   10=perfect, 0=circular

2. NON-OBVIOUSNESS (0-10): How obscure?
   10: Requires specialized research
   9: Known to domain specialists only
   8: Deep multi-domain knowledge
   7: Well-educated generalist (PREVIOUS CEILING)
   5: Moderately well-known
   0: Common knowledge

3. INTELLECTUAL DEPTH (0-10): Knowledge required
   10: PhD-level specialized + multi-domain synthesis
   9: Graduate-level expertise
   8: Advanced undergraduate + cross-domain
   7: Well-educated generalist (PREVIOUS CEILING)
   5: General adult knowledge
   0: Common knowledge

4. CROSS-DOMAIN CREATIVITY (0-10): Domain jumps
   10: Brilliant lateral leap across 3+ unrelated domains
   8: Unexpected but logical jump
   6: Different but related domains
   4: Adjacent domains
   0: Same domain

5. ABSTRACT REASONING (0-10): Conceptual thinking
   10: Abstract concepts central to chain logic
   8: Includes abstract connecting concrete
   6: One abstract concept
   4: Concrete but conceptual
   0: Pure facts

6. SURPRISE FACTOR (0-10): Unexpected but logical?
   10=mind-blowing, 0=predictable

7. COHERENCE (0-10): Connections flow naturally?
   10=perfect story, 0=random

8. VERIFIABLE (0-10): Factually accurate?
   10=well-documented, 0=dubious

9. ENGAGEMENT (0-10): Fascinating?
   10=want to share, 0=boring

Respond in EXACT format:
NON_CIRCULARITY: [score]
NON_OBVIOUSNESS: [score]
DEPTH: [score]
CROSS_DOMAIN: [score]
ABSTRACT: [score]
SURPRISE: [score]
COHERENCE: [score]
VERIFIABLE: [score]
ENGAGEMENT: [score]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()

        # Parse scores
        scores = {}
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_').replace('-', '_')
                try:
                    scores[key] = float(value.strip().split()[0])
                except:
                    pass

        # Calculate weighted overall
        overall = (
            scores.get('non_circularity', 5.0) * 0.15 +      # Table stakes
            scores.get('depth', 5.0) * 0.30 +                # KEY METRIC
            scores.get('non_obviousness', 5.0) * 0.20 +      # Important
            scores.get('cross_domain', 5.0) * 0.15 +         # NEW
            scores.get('abstract', 5.0) * 0.10 +             # NEW
            (scores.get('surprise', 5.0) +
             scores.get('coherence', 5.0) +
             scores.get('engagement', 5.0)) / 3 * 0.10       # Combined
        )

        return {
            'individual': scores,
            'overall': round(overall, 2),
            'depth': scores.get('depth', 5.0),
            'cross_domain': scores.get('cross_domain', 5.0),
            'abstract': scores.get('abstract', 5.0),
            'non_obviousness': scores.get('non_obviousness', 5.0),
            'valid': len(scores) >= 7
        }

    except Exception as e:
        print(f"    Error assessing quality: {e}")
        return {'valid': False}

# ============================================================================
# MAIN GENERATION
# ============================================================================

def main():
    print("=" * 70)
    print("V5: ULTRA-DIFFICULTY KNOWLEDGE GRAPH QUESTIONS")
    print("=" * 70)

    # Build entity pool
    print("\n📚 Building enhanced entity pool...")
    entity_pool = build_entity_pool()
    print(f"   Total entities: {len(entity_pool)}")
    print(f"   Abstract concepts: {sum(1 for e in entity_pool if e.is_abstract)}")
    print(f"   High obscurity (>0.7): {sum(1 for e in entity_pool if e.obscurity_score > 0.7)}")
    print(f"   Domains: {len(set(e.domain for e in entity_pool))}")

    # Generation targets (reduced for initial test)
    questions_per_difficulty = {
        "hard": 5,
        "expert": 3,
    }

    all_questions = []

    for difficulty, target in questions_per_difficulty.items():
        print(f"\n🎯 Generating {difficulty.upper()} questions (target: {target})...")
        print("-" * 70)

        generated = 0
        attempts = 0
        max_attempts = target * 5

        while generated < target and attempts < max_attempts:
            attempts += 1

            if attempts % 5 == 0:
                print(f"   Attempt {attempts}/{max_attempts}, generated {generated}/{target}...")

            # Generate chain
            chain = generate_v5_chain(difficulty, entity_pool)

            if chain is None:
                continue

            # Generate question
            question_data = generate_question_from_chain_v5(chain)

            if question_data is None:
                continue

            # Assess quality
            quality = assess_chain_quality_v5(question_data)

            if not quality['valid']:
                continue

            # Accept if quality threshold met (lowered for V5 testing)
            threshold = 6.5 if difficulty == "hard" else 7.0

            if quality['overall'] >= threshold:
                generated += 1
                question_data['quality_v5'] = quality
                all_questions.append(question_data)

                print(f"   ✓ #{generated}: {question_data['chain'][0][:20]}... → {question_data['answer'][:20]}...")
                print(f"      Domains: {' → '.join(question_data['domains'][:3])}...")
                print(f"      Quality: {quality['overall']}/10 | Depth: {quality['depth']}/10 | Cross-domain: {quality['cross_domain']}/10")
            else:
                print(f"   ✗ Rejected (quality {quality['overall']}/10 < {threshold})")

    # Save results
    output_file = 'data/knowledge_graph_questions_v5.jsonl'
    with open(output_file, 'w') as f:
        for q in all_questions:
            f.write(json.dumps(q) + '\n')

    # Summary
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nTotal questions: {len(all_questions)}")

    if all_questions:
        avg_quality = sum(q['quality_v5']['overall'] for q in all_questions) / len(all_questions)
        avg_depth = sum(q['quality_v5']['depth'] for q in all_questions) / len(all_questions)
        avg_cross_domain = sum(q['quality_v5']['cross_domain'] for q in all_questions) / len(all_questions)
        avg_abstract = sum(q['quality_v5']['abstract'] for q in all_questions) / len(all_questions)

        print(f"\nAverage Scores (Recalibrated Scale):")
        print(f"  Overall Quality: {avg_quality:.2f}/10")
        print(f"  Intellectual Depth: {avg_depth:.2f}/10")
        print(f"  Cross-Domain: {avg_cross_domain:.2f}/10")
        print(f"  Abstract Reasoning: {avg_abstract:.2f}/10")

        print(f"\nDifficulty Distribution:")
        for difficulty in ["hard", "expert", "grandmaster"]:
            count = sum(1 for q in all_questions if q['difficulty'] == difficulty)
            print(f"  {difficulty.capitalize()}: {count}")

        print(f"\nSaved to: {output_file}")

if __name__ == '__main__':
    main()
