from __future__ import annotations

import os
import re
from typing import Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from .config import ModelSpec, ProviderConfig


DEFAULT_SYSTEM_PROMPT = (
    "You answer riddles that obliquely describe a single real-world entity (movie, character, historical figure, item, place). "
    "Return ONLY the most likely name as a short proper noun or noun phrase. Do not explain or add punctuation."
)


def _estimate_tokens(text: str) -> int:
    """
    Rough token count estimation for DeepSeek reasoning tokens.
    Uses approximation: ~0.75 tokens per word or ~0.25 tokens per character.
    """
    if not text:
        return 0
    
    # Clean up the text and count words
    words = len(text.split())
    chars = len(text)
    
    # Use word-based estimation as primary, with character-based as fallback
    word_based = int(words * 0.75)
    char_based = int(chars * 0.25)
    
    # Return the higher estimate to be conservative
    return max(word_based, char_based, 1)


def _parse_deepseek_reasoning_content(response_text: str) -> tuple[str, dict]:
    """
    Parse DeepSeek/Qwen3 reasoning format: <think>...</think> content
    Returns (clean_response, additional_token_info)
    
    Reasoning tokens should be a subset of output tokens, not additional.
    """
    # Parse <think>...</think> tags (DeepSeek format)
    think_pattern = r'<think>(.*?)</think>'
    think_matches = re.findall(think_pattern, response_text, re.DOTALL)
    
    if think_matches:
        # Extract reasoning content
        reasoning_text = '\n'.join(think_matches)
        
        # Remove think tags to get clean response
        clean_response = re.sub(think_pattern, '', response_text, flags=re.DOTALL).strip()
        
        # Estimate reasoning tokens and final answer tokens
        reasoning_tokens = _estimate_tokens(reasoning_text)
        final_answer_tokens = _estimate_tokens(clean_response)
        
        # Reasoning tokens should be a portion of the total output
        # Don't let reasoning exceed what would be reasonable
        total_estimated = reasoning_tokens + final_answer_tokens
        
        return clean_response, {
            'reasoning_tokens': reasoning_tokens,
            'estimated_final_tokens': final_answer_tokens,
            'estimated_total_tokens': total_estimated,
            'reasoning_text_length': len(reasoning_text),
            'final_text_length': len(clean_response)
        }
    
    return response_text, {}


def _parse_deepseek_reasoning(response_text: str, model_spec: ModelSpec) -> tuple[str, dict]:
    """
    Parse DeepSeek reasoning format: <think>...</think> content
    Returns (clean_response, additional_token_info)
    """
    # Check if this is a DeepSeek model
    if 'deepseek' not in model_spec.model_id.lower():
        return response_text, {}
    
    return _parse_deepseek_reasoning_content(response_text)


def _build_headers(provider: ProviderConfig) -> Optional[Dict[str, str]]:
    headers = provider.get_resolved_headers()

    # OpenRouter best practice headers (optional but helpful)
    base_url = provider.get_base_url()
    if base_url and "openrouter.ai" in base_url:
        headers.setdefault("HTTP-Referer", "https://localhost")
        headers.setdefault("X-Title", "Convoluted Benchmark")

    return headers or None


def build_chat_model(
    spec: ModelSpec,
    temperature: float = 0.0,
    timeout: int = 60,
    max_retries: int = 2,
):
    api_key_env = spec.provider.api_key_env
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise EnvironmentError(
            f"Environment variable '{api_key_env}' is required for provider '{spec.provider_key}'."
        )

    # Provider-specific setup
    if spec.provider_key == "azure_openai":
        # AzureChatOpenAI for Azure OpenAI endpoints
        query_params = spec.provider.get_resolved_query_params()
        api_version = query_params.get("api-version")
        model_name = spec.deployment or spec.model_id
        
        # Handle reasoning models that require Responses API
        if model_name in ["o3-pro", "o3-mini", "o3", "gpt-5", "gpt-5-mini", "gpt-5-nano"]:
            return AzureChatOpenAI(
                azure_endpoint=spec.provider.get_base_url(),
                openai_api_key=api_key,
                api_version=api_version,
                model=model_name,
                # Note: reasoning models don't support temperature parameter
                timeout=timeout,
                max_retries=max_retries,
                # Enable Responses API for reasoning models
                use_responses_api=True,
                reasoning={
                    "effort": "medium",  # low, medium, or high
                    "summary": "auto"    # auto, concise, or detailed
                }
            )
        else:
            return AzureChatOpenAI(
                azure_endpoint=spec.provider.get_base_url(),
                openai_api_key=api_key,
                api_version=api_version,
                model=model_name,
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )

    # Default path: OpenAI-compatible (OpenRouter, Groq, other OpenAI-compatible APIs)
    headers = _build_headers(spec.provider)
    default_query = spec.provider.get_resolved_query_params() or None

    # Use deployment name if provided, otherwise use model ID
    model_name = spec.deployment or spec.model_id

    return ChatOpenAI(
        model=model_name,
        base_url=spec.provider.get_base_url(),
        api_key=api_key,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
        default_headers=headers,
        default_query=default_query,
    )


def ask_question(llm, question: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> tuple[str, dict]:
    """
    Ask a question to the LLM and return both answer and token usage.
    
    Returns:
        tuple: (answer_text, token_usage_dict)
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]
    out = llm.invoke(messages)
    
    # Extract token usage information
    token_usage = {}
    
    # Check usage_metadata first (newer langchain format)
    if hasattr(out, 'usage_metadata') and out.usage_metadata:
        usage = out.usage_metadata
        token_usage['input_tokens'] = usage.get('input_tokens', 0)
        token_usage['output_tokens'] = usage.get('output_tokens', 0)
        token_usage['total_tokens'] = usage.get('total_tokens', 0)
        
        # Check for reasoning tokens (o1/o3 models)
        if 'output_token_details' in usage and usage['output_token_details']:
            details = usage['output_token_details']
            if 'reasoning' in details:
                token_usage['reasoning_tokens'] = details['reasoning']
    
    # Fallback: check response_metadata for token info
    elif hasattr(out, 'response_metadata') and 'token_usage' in out.response_metadata:
        metadata = out.response_metadata['token_usage']
        token_usage['input_tokens'] = metadata.get('prompt_tokens', 0)
        token_usage['output_tokens'] = metadata.get('completion_tokens', 0)
        token_usage['total_tokens'] = metadata.get('total_tokens', 0)
        
        # Check for reasoning tokens in completion_tokens_details
        if 'completion_tokens_details' in metadata:
            details = metadata['completion_tokens_details']
            if 'reasoning_tokens' in details:
                token_usage['reasoning_tokens'] = details['reasoning_tokens']
    
    # Handle different response formats for content
    if hasattr(out, "content"):
        content = out.content
        
        # Handle Responses API format (list of content blocks)
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            text = ' '.join(text_parts)
        else:
            text = str(content)
    else:
        text = str(out)
    
    raw_text = (text or "").strip()
    
    # Handle DeepSeek/Qwen3 reasoning format: <think>...</think>
    clean_text, parsed_tokens = _parse_deepseek_reasoning_content(raw_text)
    
    # Merge parsed reasoning tokens with existing token usage
    if parsed_tokens and 'reasoning_tokens' in parsed_tokens:
        # If we don't have reasoning tokens from the API but parsing found them
        if 'reasoning_tokens' not in token_usage or token_usage.get('reasoning_tokens', 0) == 0:
            reasoning_tokens = parsed_tokens['reasoning_tokens']
            
            # Ensure reasoning tokens don't exceed output tokens from API
            api_output_tokens = token_usage.get('output_tokens', 0)
            if api_output_tokens > 0:
                # Cap reasoning tokens to be at most 90% of total output tokens
                max_reasoning = int(api_output_tokens * 0.9)
                reasoning_tokens = min(reasoning_tokens, max_reasoning)
            
            token_usage['reasoning_tokens'] = reasoning_tokens
            # Also add metadata about the parsing
            token_usage['reasoning_parsed'] = True
            token_usage['reasoning_source'] = 'think_tags'
    
    return clean_text, token_usage 