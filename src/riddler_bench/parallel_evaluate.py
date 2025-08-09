"""
Parallel evaluation system for faster benchmark execution.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from tqdm import tqdm

from .config import ModelSpec
from .dataset import QAItem
from .evaluate import append_jsonl, ensure_dir, grade_answer, summarize_results
from .models import ask_question, build_chat_model


class ParallelEvaluator:
    """Parallel evaluation with configurable concurrency per provider."""
    
    def __init__(self, provider_concurrency: Dict[str, int] = None):
        """
        Initialize with provider-specific concurrency limits.
        
        Args:
            provider_concurrency: Dict mapping provider names to max concurrent workers
                                 Example: {"azure_openai": 20, "groq": 2, "openrouter": 5}
        """
        self.provider_concurrency = provider_concurrency or {
            "azure_openai": 20,  # High concurrency for Azure
            "groq": 2,           # Conservative for Groq rate limits
            "openrouter": 5,     # Moderate for OpenRouter
        }
    
    def _get_provider_name(self, model_spec: ModelSpec) -> str:
        """Extract provider name from model spec."""
        return model_spec.display_name.split(':')[0]
    
    def evaluate_model_parallel(
        self, 
        model_spec: ModelSpec, 
        items: List[QAItem], 
        out_dir: str,
        fuzzy_threshold: int = 85,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Evaluate a single model with parallel question processing."""
        
        provider = self._get_provider_name(model_spec)
        max_workers = self.provider_concurrency.get(provider, 5)
        
        model_key = model_spec.display_name
        out_path = Path(out_dir) / f"{model_key.replace('/', '_').replace(':', '_')}.jsonl"
        
        # Ensure output file is empty
        if out_path.exists():
            out_path.unlink()
        
        print(f"[{model_key}] Starting evaluation with {max_workers} parallel workers")
        
        start_time = time.time()
        rows: List[dict] = []
        
        # Build model once
        llm = build_chat_model(model_spec, temperature=temperature)
        
        def process_question(item: QAItem) -> dict:
            """Process a single question."""
            t0 = time.time()
            try:
                answer = ask_question(llm, item.question)
            except Exception as e:
                answer = f"<error: {e}>"
            latency_ms = int((time.time() - t0) * 1000)
            
            g = grade_answer(item, answer, fuzzy_threshold=fuzzy_threshold)
            row = {
                "id": item.id,
                "question": item.question,
                "answer_ref": item.answer,
                "aliases": item.aliases or [],
                "model": model_key,
                "answer": answer,
                "latency_ms": latency_ms,
                "is_exact": g.is_exact,
                "is_alias": g.is_alias,
                "fuzzy": g.fuzzy,
                "is_correct": g.is_correct,
            }
            
            # Write immediately to file (thread-safe append)
            append_jsonl(out_path, row)
            
            return row
        
        # Execute in parallel with provider-specific concurrency and progress bar
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {executor.submit(process_question, item): item for item in items}
            
            # Collect results as they complete with progress bar
            with tqdm(total=len(items), desc=f"{model_key}", unit="q", 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
                     ncols=100) as pbar:
                
                for future in as_completed(future_to_item):
                    try:
                        row = future.result()
                        rows.append(row)
                        
                        # Update progress bar with status
                        status = "✓" if row['is_correct'] else "✗"
                        latency = f"{row['latency_ms']:.0f}ms"
                        pbar.set_postfix_str(f"{status} Q{row['id']} ({latency})")
                        pbar.update(1)
                        
                    except Exception as e:
                        item = future_to_item[future]
                        pbar.set_postfix_str(f"✗ Q{item.id} (ERROR)")
                        pbar.update(1)
                        print(f"\n[{model_key}] Error processing question {item.id}: {e}")
        
        elapsed = int(time.time() - start_time)
        stats = summarize_results(rows)
        stats.update({"model": model_key, "elapsed_s": elapsed})
        
        print(f"[{model_key}] Completed: {stats['correct']}/{stats['total']} correct ({stats['accuracy']:.3f}) in {elapsed}s")
        
        return stats
    
    def evaluate_all_models(
        self,
        model_specs: List[ModelSpec],
        items: List[QAItem],
        out_dir: str,
        fuzzy_threshold: int = 85,
        temperature: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Evaluate all models with model-level parallelization."""
        
        ensure_dir(out_dir)
        
        print(f"Starting parallel evaluation of {len(model_specs)} models on {len(items)} questions")
        print(f"Provider concurrency limits: {self.provider_concurrency}")
        
        # Group models by provider for better resource management
        provider_groups = {}
        for spec in model_specs:
            provider = self._get_provider_name(spec)
            if provider not in provider_groups:
                provider_groups[provider] = []
            provider_groups[provider].append(spec)
        
        print(f"Models grouped by provider: {[(k, len(v)) for k, v in provider_groups.items()]}")
        
        summary_rows: List[Dict[str, Any]] = []
        
        # Create overall progress tracker
        total_models = sum(len(specs) for specs in provider_groups.values())
        
        with tqdm(total=total_models, desc="Overall Progress", unit="model",
                 position=0, leave=True, colour='green',
                 bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} models [{elapsed}<{remaining}]') as overall_pbar:
            
            # Process each provider group
            for provider, specs in provider_groups.items():
                overall_pbar.write(f"\n🚀 Processing {provider} models ({len(specs)} models)")
                
                # Run models in this provider sequentially to avoid overwhelming the API
                # but each model's questions are processed in parallel
                for spec in specs:
                    try:
                        stats = self.evaluate_model_parallel(
                            spec, items, out_dir, fuzzy_threshold, temperature
                        )
                        summary_rows.append(stats)
                        
                        # Update overall progress
                        accuracy = stats['accuracy']
                        overall_pbar.set_postfix_str(f"Latest: {spec.display_name} ({accuracy:.1%})")
                        overall_pbar.update(1)
                        
                    except Exception as e:
                        overall_pbar.write(f"\n❌ [{spec.display_name}] Failed: {e}")
                        # Create error stats
                        error_stats = {
                            "model": spec.display_name,
                            "total": len(items),
                            "correct": 0,
                            "accuracy": 0.0,
                            "exact": 0,
                            "alias": 0,
                            "avg_fuzzy": 0.0,
                            "elapsed_s": 0,
                            "error": str(e)
                        }
                        summary_rows.append(error_stats)
                        overall_pbar.update(1)
        
        return summary_rows


def create_parallel_evaluator(config_path: Optional[str] = None) -> ParallelEvaluator:
    """Create a parallel evaluator with configuration from file or defaults."""
    
    # Load concurrency config from file if provided
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        provider_concurrency = config.get('provider_concurrency', {})
    else:
        provider_concurrency = {}
    
    return ParallelEvaluator(provider_concurrency=provider_concurrency)