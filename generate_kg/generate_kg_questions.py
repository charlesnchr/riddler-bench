#!/usr/bin/env python3
"""
Generate knowledge-graph-based trivia questions using LLM calls.

Algorithm:
1. Start with a seed entity (famous person, place, thing)
2. LLM generates a related entity via a specific relation
3. LLM generates another entity related to the second entity
4. LLM constructs a question based on the chain without being too explicit
"""

import json
import os
import random
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

SEED_ENTITIES = [
    "Steve Jobs", "Oprah Winfrey", "Leonardo da Vinci", "Marie Curie",
    "Nelson Mandela", "Queen Elizabeth II", "Muhammad Ali", "Pablo Picasso",
    "The Beatles", "Michael Jordan", "Ernest Hemingway", "Cleopatra",
    "Einstein", "Mozart", "Shakespeare", "Galileo", "Darwin", "Beethoven",
    "Nike", "Apple Inc", "Microsoft", "Amazon", "Google", "Tesla",
    "Statue of Liberty", "Eiffel Tower", "Great Wall of China", "Taj Mahal",
    "Beatles", "Rolling Stones", "Led Zeppelin", "Pink Floyd",
]

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Make a call to the LLM and return the response."""
    response = client.chat.completions.create(
        model="gpt-4o",  # or your deployment name
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.9,  # Higher temperature for more variety
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def generate_entity_chain():
    """Generate a 3-entity chain using LLM calls."""

    # Step 1: Pick random seed entity
    entity1 = random.choice(SEED_ENTITIES)

    # Step 2: Generate related entity via LLM
    system_prompt = "You are a knowledge graph expert. Generate a single related entity based on a specific relation."
    user_prompt = f"""Given the entity: {entity1}

Generate ONE related entity through a meaningful but not overly obvious connection.
The relation could be: worked with, founded, attended, created, married to, located in, inspired by, competitor of, etc.

Respond with ONLY the entity name and a brief relation description in this format:
ENTITY: [name]
RELATION: [brief relation from {entity1}]

Example:
ENTITY: MacKenzie Scott
RELATION: ex-wife of"""

    response1 = call_llm(system_prompt, user_prompt)

    # Parse entity2
    entity2 = None
    relation1 = None
    for line in response1.split('\n'):
        if line.startswith('ENTITY:'):
            entity2 = line.replace('ENTITY:', '').strip()
        elif line.startswith('RELATION:'):
            relation1 = line.replace('RELATION:', '').strip()

    if not entity2:
        raise ValueError(f"Failed to extract entity2 from: {response1}")

    # Step 3: Generate third entity related to entity2
    user_prompt2 = f"""Given the entity: {entity2}

Generate ONE related entity through a meaningful connection.
The relation could be: worked with, founded, attended, created, married to, located in, inspired by, etc.

Respond with ONLY the entity name and a brief relation description in this format:
ENTITY: [name]
RELATION: [brief relation from {entity2}]"""

    response2 = call_llm(system_prompt, user_prompt2)

    # Parse entity3 (the answer)
    entity3 = None
    relation2 = None
    for line in response2.split('\n'):
        if line.startswith('ENTITY:'):
            entity3 = line.replace('ENTITY:', '').strip()
        elif line.startswith('RELATION:'):
            relation2 = line.replace('RELATION:', '').strip()

    if not entity3:
        raise ValueError(f"Failed to extract entity3 from: {response2}")

    return {
        'entity1': entity1,
        'entity2': entity2,
        'entity3': entity3,
        'relation1': relation1,
        'relation2': relation2
    }

def generate_question(chain: dict) -> dict:
    """Generate a trivia question based on the entity chain."""

    system_prompt = """You are an expert trivia question writer. Create clever, engaging questions that describe entities indirectly without naming them explicitly."""

    user_prompt = f"""Create a trivia question based on this knowledge chain:

Entity 1: {chain['entity1']}
→ (via {chain['relation1']}) →
Entity 2: {chain['entity2']}
→ (via {chain['relation2']}) →
Entity 3: {chain['entity3']} [ANSWER]

The question should:
1. Describe Entity 1 without using its exact name (use indirect descriptions)
2. Mention the relation to Entity 2 (also described indirectly)
3. Mention the relation to Entity 3
4. Ask for Entity 3 as the answer

Make it clever and engaging, like a riddle. Avoid being too obvious with names.

Format:
QUESTION: [your question]
ANSWER: {chain['entity3']}"""

    response = call_llm(system_prompt, user_prompt)

    # Parse question
    question = None
    answer = None
    for line in response.split('\n'):
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

    return {
        'chain': f"{chain['entity1']} → {chain['entity2']} → {chain['entity3']}",
        'question': question or response,  # Fallback to full response if parsing fails
        'answer': answer or chain['entity3'],
        'entity1': chain['entity1'],
        'entity2': chain['entity2'],
        'entity3': chain['entity3'],
        'relation1': chain['relation1'],
        'relation2': chain['relation2']
    }

def main():
    """Generate 30 questions using the LLM-driven algorithm."""

    questions = []

    print("Generating knowledge graph questions using LLM algorithm...\n")

    for i in range(30):
        try:
            print(f"Generating question {i+1}/30...")

            # Generate entity chain
            chain = generate_entity_chain()
            print(f"  Chain: {chain['entity1']} → {chain['entity2']} → {chain['entity3']}")

            # Generate question
            q = generate_question(chain)
            q['id'] = i + 1

            questions.append(q)
            print(f"  Question: {q['question'][:80]}...")
            print()

        except Exception as e:
            print(f"  Error generating question {i+1}: {e}")
            print()
            continue

    # Save to file
    output_file = 'data/knowledge_graph_questions_llm.jsonl'
    with open(output_file, 'w') as f:
        for q in questions:
            f.write(json.dumps(q) + '\n')

    print(f"\nGenerated {len(questions)} questions saved to {output_file}")

    # Print summary
    print("\n=== SAMPLE QUESTIONS ===")
    for q in questions[:5]:
        print(f"\nChain: {q['chain']}")
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}")

if __name__ == '__main__':
    main()
