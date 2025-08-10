#!/usr/bin/env python3
"""
Results analysis tool for convoluted benchmark framework.
Provides detailed insights into model performance and question difficulty.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter
import statistics
from typing import Dict, List, Any

def load_results(results_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load all JSONL result files from a directory."""
    results = {}
    
    for jsonl_file in results_dir.glob("*.jsonl"):
        if jsonl_file.name == "summary.csv":
            continue
            
        model_name = jsonl_file.stem
        rows = []
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        
        results[model_name] = rows
    
    return results

def analyze_question_difficulty(results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Analyze which questions are most difficult across all models."""
    question_stats = defaultdict(lambda: {
        'total_attempts': 0,
        'correct': 0, 
        'exact_matches': 0,
        'fuzzy_scores': [],
        'question_text': '',
        'expected_answer': '',
        'wrong_answers': Counter()
    })
    
    # Collect stats per question
    for model_results in results.values():
        for result in model_results:
            q_id = result['id']
            stats = question_stats[q_id]
            
            stats['total_attempts'] += 1
            stats['question_text'] = result['question']
            stats['expected_answer'] = result['answer_ref']
            
            if result['is_correct']:
                stats['correct'] += 1
            else:
                # Track wrong answers
                if not result['answer'].startswith('<error:'):
                    stats['wrong_answers'][result['answer']] += 1
                    
            if result['is_exact']:
                stats['exact_matches'] += 1
                
            stats['fuzzy_scores'].append(result['fuzzy'])
    
    # Calculate difficulty metrics
    difficulty_analysis = []
    for q_id, stats in question_stats.items():
        accuracy = stats['correct'] / stats['total_attempts'] if stats['total_attempts'] > 0 else 0
        avg_fuzzy = statistics.mean(stats['fuzzy_scores']) if stats['fuzzy_scores'] else 0
        
        difficulty_analysis.append({
            'id': q_id,
            'question': stats['question_text'][:80] + "..." if len(stats['question_text']) > 80 else stats['question_text'],
            'expected': stats['expected_answer'],
            'accuracy': accuracy,
            'avg_fuzzy': avg_fuzzy,
            'attempts': stats['total_attempts'],
            'common_wrong_answers': dict(stats['wrong_answers'].most_common(3))
        })
    
    return sorted(difficulty_analysis, key=lambda x: x['accuracy'])

def analyze_model_performance(results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Analyze performance metrics per model."""
    model_analysis = []
    
    for model_name, model_results in results.items():
        if not model_results:
            continue
            
        total = len(model_results)
        correct = sum(1 for r in model_results if r['is_correct'])
        exact = sum(1 for r in model_results if r['is_exact'])
        errors = sum(1 for r in model_results if r['answer'].startswith('<error:'))
        
        fuzzy_scores = [r['fuzzy'] for r in model_results]
        latencies = [r['latency_ms'] for r in model_results]
        
        model_analysis.append({
            'model': model_name.replace('_', '/'),
            'accuracy': correct / total if total > 0 else 0,
            'exact_rate': exact / total if total > 0 else 0,
            'error_rate': errors / total if total > 0 else 0,
            'avg_fuzzy': statistics.mean(fuzzy_scores) if fuzzy_scores else 0,
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'total_questions': total
        })
    
    return sorted(model_analysis, key=lambda x: x['accuracy'], reverse=True)

def print_difficulty_analysis(difficulty_data: List[Dict[str, Any]], top_n: int = 10):
    """Print the most difficult questions."""
    print(f"\n=== TOP {top_n} MOST DIFFICULT QUESTIONS ===")
    print(f"{'ID':<4} {'Accuracy':<9} {'AvgFuzzy':<9} {'Question':<60} {'Expected':<20}")
    print("-" * 110)
    
    for item in difficulty_data[:top_n]:
        print(f"{item['id']:<4} {item['accuracy']:<9.3f} {item['avg_fuzzy']:<9.1f} {item['question']:<60} {item['expected']:<20}")
        
        if item['common_wrong_answers']:
            print(f"     Common wrong answers: {item['common_wrong_answers']}")
        print()

def print_model_analysis(model_data: List[Dict[str, Any]]):
    """Print model performance analysis."""
    print("\n=== MODEL PERFORMANCE ANALYSIS ===")
    print(f"{'Model':<40} {'Accuracy':<9} {'Exact%':<7} {'Error%':<7} {'AvgFuzzy':<9} {'AvgLatency(ms)':<15}")
    print("-" * 100)
    
    for item in model_data:
        print(f"{item['model']:<40} {item['accuracy']:<9.3f} {item['exact_rate']:<7.3f} {item['error_rate']:<7.3f} {item['avg_fuzzy']:<9.1f} {item['avg_latency_ms']:<15.1f}")

def main():
    parser = argparse.ArgumentParser(description="Analyze benchmark results")
    parser.add_argument("results_dir", help="Directory containing JSONL result files")
    parser.add_argument("--top-difficult", type=int, default=10, help="Show top N difficult questions")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Error: Results directory {results_dir} does not exist")
        return
    
    print(f"Loading results from {results_dir}")
    results = load_results(results_dir)
    
    if not results:
        print("No JSONL result files found")
        return
    
    print(f"Found results for {len(results)} models")
    
    # Analyze question difficulty
    difficulty_data = analyze_question_difficulty(results)
    print_difficulty_analysis(difficulty_data, args.top_difficult)
    
    # Analyze model performance  
    model_data = analyze_model_performance(results)
    print_model_analysis(model_data)

if __name__ == "__main__":
    main()