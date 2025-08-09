#!/usr/bin/env python3
"""Test script for gpt-4o and gpt-5 token detection."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from riddler_bench.config import load_providers_config, resolve_model_specs
from riddler_bench.models import build_chat_model, ask_question

def test_model_with_tokens(model_name: str):
    """Test a model and verify token detection."""
    print(f"🧪 Testing {model_name}")
    print("=" * 50)

    try:
        # Load config and resolve the model
        cfg = load_providers_config("config/models.yaml")
        specs = resolve_model_specs(cfg, f"azure_openai:{model_name}")

        if not specs:
            print(f"❌ No model spec found for azure_openai:{model_name}")
            return False

        spec = specs[0]
        print(f"📋 Model: {spec.display_name}")

        # Build the chat model
        llm = build_chat_model(spec)
        print(f"✅ Successfully built {model_name} client")

        # Test with a riddle
        test_question = "A boy wizard with a lightning scar on his forehead"
        print(f"❓ Question: {test_question}")

        # Use the updated ask_question that returns tokens
        answer, token_usage = ask_question(llm, test_question)
        print(f"💬 Answer: {answer}")
        
        # Display token information
        if token_usage:
            input_tokens = token_usage.get('input_tokens', 0)
            output_tokens = token_usage.get('output_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)
            reasoning_tokens = token_usage.get('reasoning_tokens', 0)
            reasoning_parsed = token_usage.get('reasoning_parsed', False)
            reasoning_source = token_usage.get('reasoning_source', 'api')
            
            print(f"📊 Token Usage:")
            print(f"   • Input tokens: {input_tokens}")
            print(f"   • Output tokens: {output_tokens}")
            if reasoning_tokens > 0:
                if reasoning_parsed:
                    source_desc = f" ({reasoning_source} parsed)"
                else:
                    source_desc = " (API reported)"
                print(f"   • Reasoning tokens: {reasoning_tokens}{source_desc}")
            print(f"   • Total tokens: {total_tokens}")
            
            # Verify we got reasonable token counts
            if input_tokens > 0 and output_tokens > 0:
                print(f"✅ {model_name} token detection - SUCCESS")
                token_success = True
            else:
                print(f"❌ {model_name} token detection - FAILED (zero tokens)")
                token_success = False
        else:
            print(f"❌ {model_name} token detection - FAILED (no token data)")
            token_success = False

        # Check if we got a valid answer
        if answer and answer.strip():
            print(f"✅ {model_name} response - SUCCESS")
            response_success = True
        else:
            print(f"❌ {model_name} response - FAILED (empty response)")
            response_success = False

        return response_success and token_success

    except Exception as e:
        print(f"❌ {model_name} test - FAILED with exception: {e}")
        return False

def test_groq_model_with_tokens(model_name: str):
    """Test a Groq model and verify token detection."""
    print(f"🧪 Testing groq:{model_name}")
    print("=" * 50)

    try:
        # Load config and resolve the model
        cfg = load_providers_config("config/models.yaml")
        specs = resolve_model_specs(cfg, f"groq:{model_name}")

        if not specs:
            print(f"❌ No model spec found for groq:{model_name}")
            return False

        spec = specs[0]
        print(f"📋 Model: {spec.display_name}")

        # Build the chat model
        llm = build_chat_model(spec)
        print(f"✅ Successfully built {model_name} client")

        # Test with a riddle - use a more complex one to trigger reasoning
        test_question = "Manager who prefers wearable tech for surveillance"
        print(f"❓ Question: {test_question}")

        # Use the updated ask_question that returns tokens
        answer, token_usage = ask_question(llm, test_question)
        print(f"💬 Answer: {answer}")
        
        # Display token information
        if token_usage:
            input_tokens = token_usage.get('input_tokens', 0)
            output_tokens = token_usage.get('output_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)
            reasoning_tokens = token_usage.get('reasoning_tokens', 0)
            reasoning_parsed = token_usage.get('reasoning_parsed', False)
            reasoning_source = token_usage.get('reasoning_source', 'api')
            
            print(f"📊 Token Usage:")
            print(f"   • Input tokens: {input_tokens}")
            print(f"   • Output tokens: {output_tokens}")
            if reasoning_tokens > 0:
                if reasoning_parsed:
                    source_desc = f" ({reasoning_source} parsed)"
                else:
                    source_desc = " (API reported)"
                print(f"   • Reasoning tokens: {reasoning_tokens}{source_desc}")
            print(f"   • Total tokens: {total_tokens}")
            
            # For DeepSeek, we expect reasoning tokens if the response had <think> tags
            success_criteria = input_tokens > 0 and output_tokens > 0
            if success_criteria:
                print(f"✅ {model_name} token detection - SUCCESS")
                token_success = True
            else:
                print(f"❌ {model_name} token detection - FAILED (insufficient token data)")
                token_success = False
        else:
            print(f"❌ {model_name} token detection - FAILED (no token data)")
            token_success = False

        # Check if we got a valid answer
        if answer and answer.strip():
            print(f"✅ {model_name} response - SUCCESS")
            response_success = True
        else:
            print(f"❌ {model_name} response - FAILED (empty response)")
            response_success = False

        return response_success and token_success

    except Exception as e:
        print(f"❌ {model_name} test - FAILED with exception: {e}")
        return False

def main():
    """Test both models."""
    print("🚀 Testing Token Detection for GPT Models")
    print("=" * 60)
    
    results = {}
    
    # Test gpt-4o (standard model)
    results['gpt-4o'] = test_model_with_tokens('gpt-4o')
    print()
    
    # Test gpt-5 (responses API model)
    results['gpt-5'] = test_model_with_tokens('gpt-5')
    print()
    
    # Test deepseek reasoning model
    try:
        results['deepseek-r1'] = test_groq_model_with_tokens('deepseek-r1-distill-llama-70b')
        print()
    except Exception as e:
        print(f"⚠️  Skipping DeepSeek test: {e}")
        print()
    
    # Test qwen3 reasoning model
    try:
        results['qwen3-32b'] = test_groq_model_with_tokens('qwen/qwen3-32b')
        print()
    except Exception as e:
        print(f"⚠️  Skipping Qwen3 test: {e}")
        print()
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for model, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{model:<15} {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All {len(results)} models passed token detection tests!")
    else:
        failed = sum(1 for success in results.values() if not success)
        print(f"\n⚠️  {failed}/{len(results)} models failed tests")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
