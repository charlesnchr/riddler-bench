#!/usr/bin/env python3
"""Test script to verify each LLM client works individually."""

import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from riddler_bench.config import load_providers_config, resolve_model_specs
from riddler_bench.models import build_chat_model, ask_question

# Thread-safe print lock
print_lock = Lock()

def test_llm_provider(provider_key: str, model_id: str):
    """Test a specific LLM provider with a simple question."""
    model_key = f"{provider_key}:{model_id}"
    
    try:
        # Load config and resolve the specific model
        cfg = load_providers_config("config/models.yaml")
        specs = resolve_model_specs(cfg, model_key)

        if not specs:
            with print_lock:
                print(f"❌ {model_key} - No model spec found")
            return model_key, False, "No model spec found"

        spec = specs[0]

        # Build the chat model
        llm = build_chat_model(spec, temperature=0.0)

        # Test with a simple question
        test_question = "Movie feauturing a wizard boy with a scar on his forehead"
        answer, token_usage = ask_question(llm, test_question)
        
        # Prepare token info
        token_info = ""
        if token_usage:
            tokens_str = f"📊 {token_usage.get('input_tokens', 0)} in, {token_usage.get('output_tokens', 0)} out"
            if 'reasoning_tokens' in token_usage and token_usage['reasoning_tokens'] > 0:
                tokens_str += f" ({token_usage['reasoning_tokens']} reasoning)"
            token_info = tokens_str

        if answer and not answer.startswith("<error:"):
            with print_lock:
                print(f"✅ {model_key} - SUCCESS")
                if token_info:
                    print(f"   {token_info}")
            return model_key, True, answer[:50] + "..." if len(answer) > 50 else answer
        else:
            with print_lock:
                print(f"❌ {model_key} - FAILED (error in response)")
            return model_key, False, "Error in response"

    except Exception as e:
        with print_lock:
            print(f"❌ {model_key} - FAILED with exception: {str(e)[:100]}...")
        return model_key, False, str(e)

def main():
    """Test all configured providers in parallel."""
    print("🚀 Testing LLM Clients in Parallel")
    print("=" * 60)

    # Test cases: (provider_key, model_id) - All models from config
    test_cases = [
        # Azure OpenAI models
        ("azure_openai", "gpt-4o"),
        ("azure_openai", "gpt-5"),
        ("azure_openai", "gpt-5-mini"),
        ("azure_openai", "gpt-5-nano"),
        ("azure_openai", "gpt-5-chat"),
        ("azure_openai", "o3-pro"),
        
        # OpenRouter models  
        ("openrouter", "openai/gpt-4o-mini"),
        ("openrouter", "meta-llama/llama-3.1-405b-instruct"),
        ("openrouter", "qwen/qwen-2.5-72b-instruct"),
        ("openrouter", "meta-llama/llama-3.1-8b-instruct"),
        ("openrouter", "qwen/qwen-2.5-7b-instruct"),
        ("openrouter", "mistralai/mistral-7b-instruct"),
        
        # Groq models
        ("groq", "llama-3.3-70b-versatile"),
        ("groq", "deepseek-r1-distill-llama-70b"),
        ("groq", "qwen/qwen3-32b"),
        ("groq", "gemma2-9b-it"),
        ("groq", "llama-3.1-8b-instant"),
        ("groq", "openai/gpt-oss-120b"),
        ("groq", "moonshotai/kimi-k2-instruct"),
    ]

    print(f"Testing {len(test_cases)} models in parallel...")
    print()

    # Run tests in parallel with appropriate thread limits
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_model = {
            executor.submit(test_llm_provider, provider_key, model_id): f"{provider_key}:{model_id}"
            for provider_key, model_id in test_cases
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_model):
            model_key, success, details = future.result()
            results[model_key] = success

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    # Sort results for consistent display
    sorted_results = sorted(results.items())
    for model_key, success in sorted_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{model_key:<40} {status}")

    all_passed = all(results.values())
    if all_passed:
        print(f"\n🎉 All {len(results)} LLM clients are working!")
    else:
        failed_count = sum(1 for success in results.values() if not success)
        print(f"\n⚠️  {failed_count}/{len(results)} LLM clients failed")

    return all_passed

if __name__ == "__main__":
    main()
