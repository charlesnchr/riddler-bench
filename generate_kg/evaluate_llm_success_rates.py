#!/usr/bin/env python3
"""
Evaluate LLM Success Rates on V1-V6 Questions

Tests how well different LLM tiers can solve riddles from each version:
- Frontier: GPT-4o, Claude 3.5 Sonnet
- Mid-tier: GPT-4o (extended thinking)
- Small: GPT-4o-mini, Llama 3.3 70B

Measures:
- Exact match rate
- Fuzzy match rate (semantic similarity)
- Success by version
- Success by model tier
"""

import json
import os
from typing import Dict, List
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
import re

load_dotenv()

# Initialize clients
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

# Model configurations stratified by capability
TEST_MODELS = [
    # Frontier models
    {
        "name": "GPT-4o",
        "client": azure_client,
        "model": "gpt-4o",
        "tier": "frontier",
        "temperature": 0.7
    },
    {
        "name": "Claude-3.5-Sonnet",
        "client": openrouter_client,
        "model": "anthropic/claude-3.5-sonnet",
        "tier": "frontier",
        "temperature": 0.7
    },
    # Gemini removed - model name issues
    # {
    #     "name": "Gemini-2.0-Flash",
    #     "client": openrouter_client,
    #     "model": "google/gemini-2.0-flash-exp:free",
    #     "tier": "frontier",
    #     "temperature": 0.7
    # },
    # Small models
    {
        "name": "GPT-4o-mini",
        "client": azure_client,
        "model": "gpt-4o-mini",
        "tier": "small",
        "temperature": 0.7
    },
    {
        "name": "Llama-3.3-70B",
        "client": groq_client,
        "model": "llama-3.3-70b-versatile",
        "tier": "small",
        "temperature": 0.7
    },
]

# Version samples
VERSION_SAMPLES = {
    "V1": {
        "question": "This groundbreaking physicist, often associated with a cosmic 'relative,' was once married to a brilliant mathematician and physicist who shared a name with a famous Serbian scientist. Who is this theoretical powerhouse known for revolutionizing our understanding of space and time?",
        "answer": "Albert Einstein",
        "chain": ["Einstein", "Mileva Marić", "Albert Einstein"]
    },
    "V2": {
        "question": "Which entrepreneurial shoemaker founded the brand famously endorsed by the world's fastest man?",
        "answer": "Rudolf Dassler",
        "chain": ["Usain Bolt", "Puma", "Rudolf Dassler"]
    },
    "V3": {
        "question": "Which renowned primatologist, who studied chimpanzees in a Tanzanian national park, authored a groundbreaking book about her observations?",
        "answer": "In the Shadow of Man",
        "chain": ["Jane Goodall", "Gombe Stream National Park", "In the Shadow of Man"]
    },
    "V4": {
        "question": "Which animated film about an ogre was produced by the studio co-founded by the director of E.T. and Jurassic Park?",
        "answer": "Shrek",
        "chain": ["Steven Spielberg", "Amblin Entertainment", "DreamWorks Pictures", "Shrek"]
    },
    "V5": {
        "question": "What theoretical framework, emerging from an era captivated by the cognitive limits of human connectivity and playfully quantified chains of collaboration across disciplines and industries, ultimately formalized our understanding of the surprising proximity within vast, intricate systems?",
        "answer": "Small-World Network",
        "chain": ["Dunbar's Number", "Erdős–Bacon number", "Six Degrees of Kevin Bacon", "Small-World Network"]
    },
}

# Load V6 samples
def load_v6_samples():
    """Load actual V6 questions from file."""
    try:
        with open('data/knowledge_graph_questions_v6.jsonl', 'r') as f:
            questions = [json.loads(line) for line in f if line.strip()]
            # Take first 3 questions
            return questions[:3]
    except:
        return []


def ask_llm(model_config: dict, question: str) -> str:
    """Ask LLM to answer a riddle question."""

    system_prompt = """You are solving challenging trivia riddles.

Instructions:
- Read the riddle carefully
- Think through the clues
- Provide your best answer
- Be concise - just give the answer, no explanation
- If unsure, make your best educated guess

Respond with ONLY the answer, nothing else."""

    try:
        response = model_config['client'].chat.completions.create(
            model=model_config['model'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Riddle: {question}\n\nAnswer:"}
            ],
            temperature=model_config['temperature'],
            max_tokens=100
        )

        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        print(f"  Error with {model_config['name']}: {e}")
        return ""


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison."""
    # Remove common prefixes
    answer = re.sub(r'^(the |a |an )', '', answer.lower())
    # Remove punctuation
    answer = re.sub(r'[^\w\s]', '', answer)
    # Normalize whitespace
    answer = ' '.join(answer.split())
    return answer


def check_correctness(llm_answer: str, correct_answer: str) -> dict:
    """Check if LLM answer is correct."""

    llm_norm = normalize_answer(llm_answer)
    correct_norm = normalize_answer(correct_answer)

    # Exact match
    if llm_norm == correct_norm:
        return {'correct': True, 'match_type': 'exact'}

    # Contains match (LLM answer contains correct answer)
    if correct_norm in llm_norm or llm_norm in correct_norm:
        return {'correct': True, 'match_type': 'partial'}

    # Check if key words match (for multi-word answers)
    llm_words = set(llm_norm.split())
    correct_words = set(correct_norm.split())

    # If >50% of words overlap
    if len(llm_words & correct_words) / max(len(correct_words), 1) > 0.5:
        return {'correct': True, 'match_type': 'fuzzy'}

    return {'correct': False, 'match_type': 'none'}


def evaluate_version(version: str, question_data: dict, models: List[dict]) -> dict:
    """Evaluate all models on a single version."""

    question = question_data['question']
    correct_answer = question_data['answer']

    print(f"\n{'='*80}")
    print(f"{version}: {question[:80]}...")
    print(f"{'='*80}")
    print(f"Correct Answer: {correct_answer}")
    print(f"Chain: {' → '.join(question_data.get('chain', []))}")
    print()

    results = []

    for model in models:
        print(f"  {model['name']:20} ", end="", flush=True)

        llm_answer = ask_llm(model, question)
        correctness = check_correctness(llm_answer, correct_answer)

        result = {
            'model': model['name'],
            'tier': model['tier'],
            'llm_answer': llm_answer,
            'correct_answer': correct_answer,
            'correct': correctness['correct'],
            'match_type': correctness['match_type']
        }

        results.append(result)

        if correctness['correct']:
            print(f"✓ {llm_answer[:40]}")
        else:
            print(f"✗ {llm_answer[:40]}")

    return results


def main():
    print("="*80)
    print("LLM SUCCESS RATE EVALUATION: V1-V6")
    print("="*80)
    print(f"\nTesting {len(TEST_MODELS)} models across versions")
    print(f"Models by tier:")
    for tier in ['frontier', 'small']:
        tier_models = [m['name'] for m in TEST_MODELS if m['tier'] == tier]
        print(f"  {tier.capitalize()}: {', '.join(tier_models)}")

    # Run evaluations
    all_results = {}

    # V1-V5 from samples
    for version, data in VERSION_SAMPLES.items():
        results = evaluate_version(version, data, TEST_MODELS)
        all_results[version] = results

    # V6 from actual generated questions
    v6_samples = load_v6_samples()
    if v6_samples:
        for i, q in enumerate(v6_samples, 1):
            version = f"V6-{i}"
            results = evaluate_version(version, q, TEST_MODELS)
            all_results[version] = results

    # Calculate statistics
    print("\n" + "="*80)
    print("SUCCESS RATE SUMMARY")
    print("="*80)

    # By version
    print("\n📊 Success Rate by Version:")
    print("-"*80)
    print(f"{'Version':<12} {'Frontier':<12} {'Small':<12} {'Overall':<12}")
    print("-"*80)

    for version in ['V1', 'V2', 'V3', 'V4', 'V5'] + [f'V6-{i}' for i in range(1, len(v6_samples)+1)]:
        if version not in all_results:
            continue

        results = all_results[version]

        frontier_correct = sum(1 for r in results if r['tier'] == 'frontier' and r['correct'])
        frontier_total = sum(1 for r in results if r['tier'] == 'frontier')

        small_correct = sum(1 for r in results if r['tier'] == 'small' and r['correct'])
        small_total = sum(1 for r in results if r['tier'] == 'small')

        total_correct = sum(1 for r in results if r['correct'])
        total = len(results)

        frontier_pct = (frontier_correct / frontier_total * 100) if frontier_total else 0
        small_pct = (small_correct / small_total * 100) if small_total else 0
        overall_pct = (total_correct / total * 100) if total else 0

        print(f"{version:<12} {frontier_pct:>6.1f}%      {small_pct:>6.1f}%      {overall_pct:>6.1f}%")

    # By model
    print("\n📊 Success Rate by Model:")
    print("-"*80)
    print(f"{'Model':<25} {'Tier':<10} {'Correct':<10} {'Total':<10} {'Rate':<10}")
    print("-"*80)

    for model in TEST_MODELS:
        model_results = []
        for results in all_results.values():
            model_results.extend([r for r in results if r['model'] == model['name']])

        correct = sum(1 for r in model_results if r['correct'])
        total = len(model_results)
        rate = (correct / total * 100) if total else 0

        print(f"{model['name']:<25} {model['tier']:<10} {correct:<10} {total:<10} {rate:>6.1f}%")

    # Difficulty analysis
    print("\n📊 Difficulty Analysis:")
    print("-"*80)

    # Average success rates
    version_rates = {}
    for version in ['V1', 'V2', 'V3', 'V4', 'V5'] + [f'V6-{i}' for i in range(1, len(v6_samples)+1)]:
        if version not in all_results:
            continue

        results = all_results[version]
        rate = sum(1 for r in results if r['correct']) / len(results) * 100
        version_rates[version] = rate

    # Sort by difficulty (lowest success rate = hardest)
    sorted_versions = sorted(version_rates.items(), key=lambda x: x[1])

    print("\nVersions by Difficulty (hardest first):")
    for version, rate in sorted_versions:
        difficulty = "🔴 Very Hard" if rate < 30 else "🟠 Hard" if rate < 50 else "🟡 Medium" if rate < 70 else "🟢 Easy"
        print(f"  {version:<12} {rate:>5.1f}% success  {difficulty}")

    # Save detailed results
    output_file = 'results/llm_success_rates.json'
    os.makedirs('results', exist_ok=True)

    # Save model info without client objects (not JSON serializable)
    model_info = [
        {'name': m['name'], 'model': m['model'], 'tier': m['tier'], 'temperature': m['temperature']}
        for m in TEST_MODELS
    ]

    with open(output_file, 'w') as f:
        json.dump({
            'models': model_info,
            'results': all_results,
            'summary': {
                'by_version': version_rates,
                'by_model': {
                    model['name']: {
                        'correct': sum(1 for results in all_results.values()
                                     for r in results if r['model'] == model['name'] and r['correct']),
                        'total': sum(1 for results in all_results.values()
                                   for r in results if r['model'] == model['name'])
                    }
                    for model in TEST_MODELS
                }
            }
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == '__main__':
    main()
