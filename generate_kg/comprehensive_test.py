#!/usr/bin/env python3
"""
Comprehensive test across multiple models and question versions
"""

import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

load_dotenv()

# Initialize clients
azure_client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_BASE_URL")
)

openrouter_client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# All models to test
MODELS = [
    # Frontier models
    {
        "name": "GPT-4o",
        "client": azure_client,
        "model": "gpt-4o",
        "tier": "frontier",
        "temperature": 0.3,
        "use_reasoning": False
    },
    {
        "name": "Claude-3.5-Sonnet",
        "client": openrouter_client,
        "model": "anthropic/claude-3.5-sonnet",
        "tier": "frontier",
        "temperature": 0.3,
        "use_reasoning": False
    },
    # GPT-5 reasoning models
    {
        "name": "gpt-5",
        "client": azure_client,
        "model": "gpt-5",
        "tier": "reasoning",
        "temperature": 1.0,
        "use_reasoning": True
    },
    {
        "name": "gpt-5-mini",
        "client": azure_client,
        "model": "gpt-5-mini",
        "tier": "reasoning",
        "temperature": 1.0,
        "use_reasoning": True
    },
    {
        "name": "gpt-5-nano",
        "client": azure_client,
        "model": "gpt-5-nano",
        "tier": "reasoning",
        "temperature": 1.0,
        "use_reasoning": True
    },
    # o1 models
    {
        "name": "o1",
        "client": azure_client,
        "model": "o1",
        "tier": "reasoning",
        "temperature": 1.0,
        "use_reasoning": True
    },
    {
        "name": "o1-mini",
        "client": azure_client,
        "model": "o1-mini",
        "tier": "reasoning",
        "temperature": 1.0,
        "use_reasoning": True
    },
]

# Question versions to test
QUESTION_VERSIONS = [
    ("v2", "data/knowledge_graph_questions_v2.jsonl"),
    ("v4", "data/knowledge_graph_questions_v4.jsonl"),
    ("v5", "data/knowledge_graph_questions_v5.jsonl"),
    ("v6", "data/knowledge_graph_questions_v6.jsonl"),
    ("v7", "data/knowledge_graph_questions_v7.jsonl"),
]


def ask_llm(model_config: dict, question: str) -> str:
    """Ask model to answer a riddle."""
    try:
        # Prepare messages
        if model_config['use_reasoning']:
            messages = [
                {
                    "role": "user",
                    "content": f"Solve this riddle. Respond with ONLY the answer, nothing else.\n\n{question}"
                }
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": "You are solving challenging trivia riddles. Respond with ONLY the answer, nothing else."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]

        # Build API call parameters
        params = {
            "model": model_config['model'],
            "messages": messages,
            "temperature": model_config['temperature']
        }

        # Standard models use max_tokens
        if not model_config['use_reasoning']:
            params['max_tokens'] = 150

        response = model_config['client'].chat.completions.create(**params)
        content = response.choices[0].message.content

        if content is None:
            return "(no content)"
        return content.strip()

    except Exception as e:
        return f"Error: {str(e)}"


def check_correctness(llm_answer: str, correct_answer: str) -> bool:
    """Check if LLM answer is correct."""
    llm_lower = llm_answer.lower().strip()
    answer_lower = correct_answer.lower().strip()

    # Exact match
    if llm_lower == answer_lower:
        return True

    # Partial match (answer contained in LLM response)
    if answer_lower in llm_lower or llm_lower in answer_lower:
        return True

    # Fuzzy match (significant word overlap)
    llm_words = set(llm_lower.split())
    answer_words = set(answer_lower.split())

    if len(llm_words) > 0 and len(answer_words) > 0:
        overlap = len(llm_words & answer_words) / min(len(llm_words), len(answer_words))
        if overlap > 0.5:
            return True

    return False


def load_questions(version: str, filepath: str, sample_size: int = 1):
    """Load questions from a version file."""
    if not os.path.exists(filepath):
        print(f"  ⚠️  {version} file not found: {filepath}")
        return []

    with open(filepath, 'r') as f:
        questions = [json.loads(line) for line in f if line.strip()]

    # Sample
    questions = questions[:sample_size]
    print(f"  ✓ Loaded {len(questions)} {version} questions")
    return [(version, q) for q in questions]


def main():
    print("="*80)
    print("COMPREHENSIVE MODEL EVALUATION")
    print("="*80)

    # Load only V7 questions
    print("\nLoading questions...")
    all_questions = []
    # Only test V7
    questions = load_questions("v7", "data/knowledge_graph_questions_v7.jsonl", sample_size=10)
    all_questions.extend(questions)

    print(f"\nTotal questions to test: {len(all_questions)}")
    print(f"Total models to test: {len(MODELS)}")
    print(f"Total evaluations: {len(all_questions) * len(MODELS)}")

    # Run evaluation
    results = []
    question_num = 0

    for version, question_data in all_questions:
        question_num += 1
        question = question_data.get('question', '')
        answer = question_data.get('answer', '')

        print(f"\n{'='*80}")
        print(f"Q{question_num} ({version}): {question}")
        print(f"Answer: {answer}")
        print(f"{'='*80}")

        for model in MODELS:
            print(f"\n{model['name']:20}", end=" ", flush=True)

            llm_answer = ask_llm(model, question)
            correct = check_correctness(llm_answer, answer)

            result = {
                'question_num': question_num,
                'version': version,
                'question': question,
                'correct_answer': answer,
                'model': model['name'],
                'tier': model['tier'],
                'llm_answer': llm_answer,
                'correct': correct
            }

            results.append(result)

            status = "✓" if correct else "✗"
            print(f"{status} {llm_answer[:60]}")

    # Calculate statistics
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    # Per model
    print("\nPER MODEL:")
    for model in MODELS:
        model_results = [r for r in results if r['model'] == model['name']]
        correct = sum(1 for r in model_results if r['correct'])
        total = len(model_results)
        rate = (correct / total * 100) if total else 0

        print(f"  {model['name']:25} {correct:2}/{total:2} = {rate:5.1f}%")

    # Per version
    print("\nPER VERSION:")
    for version, _ in QUESTION_VERSIONS:
        version_results = [r for r in results if r['version'] == version]
        if not version_results:
            continue
        correct = sum(1 for r in version_results if r['correct'])
        total = len(version_results)
        rate = (correct / total * 100) if total else 0

        print(f"  {version:10} {correct:2}/{total:2} = {rate:5.1f}%")

    # Per tier
    print("\nPER TIER:")
    for tier in ['frontier', 'reasoning']:
        tier_results = [r for r in results if r['tier'] == tier]
        if not tier_results:
            continue
        correct = sum(1 for r in tier_results if r['correct'])
        total = len(tier_results)
        rate = (correct / total * 100) if total else 0

        print(f"  {tier:15} {correct:2}/{total:2} = {rate:5.1f}%")

    # Save results
    output_file = 'results/comprehensive_test_results.json'
    os.makedirs('results', exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'total_questions': len(all_questions),
            'total_models': len(MODELS),
            'models': [{'name': m['name'], 'tier': m['tier']} for m in MODELS],
            'versions': [v for v, _ in QUESTION_VERSIONS],
            'results': results
        }, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")


if __name__ == '__main__':
    main()
