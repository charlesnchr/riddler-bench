from __future__ import annotations

import os
from typing import Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from .config import ModelSpec, ProviderConfig


DEFAULT_SYSTEM_PROMPT = (
    "You answer riddles that obliquely describe a single real-world entity (movie, character, historical figure, item, place). "
    "Return ONLY the most likely name as a short proper noun or noun phrase. Do not explain or add punctuation."
)


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
        
        return AzureChatOpenAI(
            azure_endpoint=spec.provider.get_base_url(),
            openai_api_key=api_key,
            api_version=api_version,
            model=spec.deployment or spec.model_id,
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


def ask_question(llm, question: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]
    out = llm.invoke(messages)
    text = out.content if hasattr(out, "content") else str(out)
    return (text or "").strip() 