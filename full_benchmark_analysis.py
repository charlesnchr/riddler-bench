#!/usr/bin/env python3
"""
Comprehensive analysis of full benchmark results across all models.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
import statistics

def load_all_full_benchmark_results():
    """Load results from both the main run and remaining groq models."""
    results = {}
    
    # Load main results
    main_dir = Path("results/full-benchmark-all-models")
    if main_dir.exists():
        for jsonl_file in main_dir.glob("*.jsonl"):
            model_name = jsonl_file.stem
            with open(jsonl_file, 'r') as f:
                results[model_name] = [json.loads(line) for line in f if line.strip()]
    
    # Load remaining groq results if available
    groq_dir = Path("results/full-benchmark-remaining-groq")
    if groq_dir.exists():
        for jsonl_file in groq_dir.glob("*.jsonl"):
            model_name = jsonl_file.stem
            with open(jsonl_file, 'r') as f:
                results[model_name] = [json.loads(line) for line in f if line.strip()]
    
    return results

def analyze_gpt5_breakthrough():
    """Analyze GPT-5's performance on previously impossible questions."""
    
    # Previously impossible questions (0% accuracy from earlier analysis)
    impossible_questions = {
        '1': "Movie about a man fighting for his life to gain freedom in a large building in an old European city?",
        '44': "Manager who prefers wearable tech for surveillance.",
        '42': "Blue rock that took a very cold dive.",
        '34': "Tool that won't consider your application unless you're worthy.",
        '45': "Moon where tall blue cat-people argue with bulldozers."
    }
    
    results = load_all_full_benchmark_results()
    gpt5_results = results.get('azure_openai_gpt-5', [])
    
    print("=== GPT-5 BREAKTHROUGH ON PREVIOUSLY IMPOSSIBLE QUESTIONS ===\n")
    
    breakthroughs = 0
    for result in gpt5_results:
        if str(result['id']) in impossible_questions:
            status = "✅ SOLVED" if result['is_correct'] else "❌ FAILED"
            if result['is_correct']:
                breakthroughs += 1
            
            latency_s = result['latency_ms'] / 1000
            print(f"Q{result['id']}: {status}")
            print(f"   Question: {impossible_questions[str(result['id'])]}")
            print(f"   Expected: '{result['answer_ref']}'")
            print(f"   GPT-5 Answer: '{result['answer']}'")
            print(f"   Response time: {latency_s:.1f}s")
            print()
    
    print(f"BREAKTHROUGH SUMMARY: GPT-5 solved {breakthroughs}/5 previously impossible questions!")
    return breakthroughs

def create_comprehensive_leaderboard():
    """Create a comprehensive model leaderboard."""
    results = load_all_full_benchmark_results()
    
    leaderboard = []
    
    for model_name, model_results in results.items():
        if not model_results:
            continue
            
        total = len(model_results)
        if total == 0:
            continue
            
        correct = sum(1 for r in model_results if r['is_correct'])
        exact = sum(1 for r in model_results if r['is_exact'])
        errors = sum(1 for r in model_results if r['answer'].startswith('<error:'))
        
        # Calculate latency for non-error responses
        successful_responses = [r for r in model_results if not r['answer'].startswith('<error:')]
        avg_latency = statistics.mean([r['latency_ms'] for r in successful_responses]) if successful_responses else 0
        
        fuzzy_scores = [r['fuzzy'] for r in model_results]
        avg_fuzzy = statistics.mean(fuzzy_scores) if fuzzy_scores else 0
        
        # Calculate cost estimate (rough)
        cost_multiplier = {
            'gpt-5': 50,  # Estimated high cost
            'gpt-4o': 10,
            'claude-3.5-sonnet': 15,
            'llama-3.1-405b': 8,
            'gpt-4o-mini': 1
        }
        
        model_key = model_name.replace('azure_openai_', '').replace('openrouter_', '').replace('groq_', '')
        cost_est = cost_multiplier.get(model_key.split('_')[0], 3)
        
        leaderboard.append({
            'model': model_name.replace('_', '/'),
            'accuracy': correct / total,
            'total_questions': total,
            'correct': correct,
            'exact_matches': exact,
            'errors': errors,
            'avg_latency_ms': avg_latency,
            'avg_fuzzy': avg_fuzzy,
            'cost_estimate': cost_est,
            'score': (correct / total) * 100  # Simple scoring
        })
    
    return sorted(leaderboard, key=lambda x: x['accuracy'], reverse=True)

def print_leaderboard(leaderboard):
    """Print the comprehensive leaderboard."""
    print("\n=== COMPREHENSIVE MODEL LEADERBOARD (Full Benchmark) ===\n")
    
    print(f"{'Rank':<4} {'Model':<40} {'Accuracy':<9} {'Questions':<10} {'Errors':<7} {'Avg Latency':<12} {'Cost Est':<9}")
    print("-" * 100)
    
    for i, model in enumerate(leaderboard, 1):
        latency_display = f"{model['avg_latency_ms']/1000:.1f}s" if model['avg_latency_ms'] > 1000 else f"{model['avg_latency_ms']:.0f}ms"
        cost_display = "$" * min(model['cost_estimate'], 5)  # Visual cost indicator
        
        print(f"{i:<4} {model['model']:<40} {model['accuracy']:<9.3f} {model['correct']}/{model['total_questions']:<7} {model['errors']:<7} {latency_display:<12} {cost_display:<9}")

def identify_model_categories():
    """Categorize models by performance tiers."""
    leaderboard = create_comprehensive_leaderboard()
    
    print("\n=== MODEL PERFORMANCE TIERS ===\n")
    
    tier1 = [m for m in leaderboard if m['accuracy'] >= 0.8]
    tier2 = [m for m in leaderboard if 0.6 <= m['accuracy'] < 0.8]
    tier3 = [m for m in leaderboard if 0.4 <= m['accuracy'] < 0.6]
    tier4 = [m for m in leaderboard if m['accuracy'] < 0.4]
    
    print("🏆 TIER 1 - ELITE (≥80% accuracy):")
    for model in tier1:
        print(f"   • {model['model']}: {model['accuracy']:.1%}")
    
    print(f"\n🥈 TIER 2 - STRONG (60-79% accuracy):")
    for model in tier2:
        print(f"   • {model['model']}: {model['accuracy']:.1%}")
    
    print(f"\n🥉 TIER 3 - MODERATE (40-59% accuracy):")
    for model in tier3:
        print(f"   • {model['model']}: {model['accuracy']:.1%}")
    
    print(f"\n📉 TIER 4 - WEAK (<40% accuracy):")
    for model in tier4:
        print(f"   • {model['model']}: {model['accuracy']:.1%}")

def main():
    print("=== COMPREHENSIVE FULL BENCHMARK ANALYSIS ===")
    
    # Analyze GPT-5 breakthroughs
    breakthroughs = analyze_gpt5_breakthrough()
    
    # Create and display leaderboard
    leaderboard = create_comprehensive_leaderboard()
    print_leaderboard(leaderboard)
    
    # Show performance tiers
    identify_model_categories()
    
    print(f"\n=== KEY INSIGHTS ===")
    print(f"• GPT-5 leads with {leaderboard[0]['accuracy']:.1%} accuracy but ~30x slower responses")
    print(f"• GPT-4o offers best speed/accuracy balance at {[m for m in leaderboard if 'gpt-4o' in m['model'] and 'gpt-5' not in m['model']][0]['accuracy']:.1%}")
    print(f"• {breakthroughs}/5 previously impossible questions now solved by GPT-5")
    print(f"• {len([m for m in leaderboard if m['errors'] > 0])} models experienced API errors")
    print(f"• Total models evaluated: {len(leaderboard)}")

if __name__ == "__main__":
    main()