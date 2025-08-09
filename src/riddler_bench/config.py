from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel

# Load .env file if it exists
def load_dotenv():
    """Simple .env file loader."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Remove quotes
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value

# Load .env on import
load_dotenv()


class ModelEntry(BaseModel):
    id: str
    deployment: Optional[str] = None


class ProviderConfig(BaseModel):
    name: str
    base_url: Optional[str] = None
    base_url_env: Optional[str] = None
    api_key_env: str
    query_params: Optional[Dict[str, Union[str, Dict[str, str]]]] = None
    default_headers: Optional[Dict[str, Union[str, Dict[str, str]]]] = None
    models: List[ModelEntry]
    
    def get_base_url(self) -> str:
        """Get base URL from direct value or environment variable."""
        if self.base_url:
            return self.base_url
        if self.base_url_env:
            url = os.getenv(self.base_url_env)
            if not url:
                raise ValueError(f"Environment variable {self.base_url_env} not set")
            return url
        raise ValueError("Neither base_url nor base_url_env specified")
    
    def get_resolved_query_params(self) -> Dict[str, str]:
        """Resolve query params with environment variable substitution."""
        if not self.query_params:
            return {}
        
        resolved = {}
        for key, value in self.query_params.items():
            if isinstance(value, str):
                resolved[key] = value
            elif isinstance(value, dict) and len(value) == 1:
                # Handle format like "api-version_env: AZURE_OPENAI_API_VERSION"
                env_key = list(value.keys())[0]
                if env_key.endswith('_env'):
                    param_name = env_key[:-4]  # Remove '_env' suffix
                    env_var = value[env_key]
                    env_value = os.getenv(env_var)
                    if not env_value:
                        raise ValueError(f"Environment variable {env_var} not set")
                    resolved[param_name] = env_value
                else:
                    resolved[key] = str(value)
            else:
                # Handle direct key_env format
                if key.endswith('_env'):
                    param_name = key[:-4]  # Remove '_env' suffix
                    env_value = os.getenv(str(value))
                    if not env_value:
                        raise ValueError(f"Environment variable {value} not set")
                    resolved[param_name] = env_value
                else:
                    resolved[key] = str(value)
        
        return resolved
    
    def get_resolved_headers(self) -> Dict[str, str]:
        """Resolve headers with environment variable substitution."""
        if not self.default_headers:
            return {}
        
        resolved = {}
        for key, value in self.default_headers.items():
            if isinstance(value, str):
                resolved[key] = value
            else:
                # Handle key_env format
                if key.endswith('_env'):
                    header_name = key[:-4]  # Remove '_env' suffix
                    env_value = os.getenv(str(value))
                    if env_value:  # Optional headers can be missing
                        resolved[header_name] = env_value
                else:
                    resolved[key] = str(value)
        
        return resolved


class ProvidersConfig(BaseModel):
    providers: Dict[str, ProviderConfig]


@dataclass(frozen=True)
class ModelSpec:
    provider_key: str
    provider: ProviderConfig
    model_id: str
    deployment: Optional[str]

    @property
    def display_name(self) -> str:
        if self.deployment and self.deployment != self.model_id:
            return f"{self.provider_key}:{self.model_id}({self.deployment})"
        return f"{self.provider_key}:{self.model_id}"


def load_providers_config(path: str) -> ProvidersConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ProvidersConfig(**raw)


def list_model_specs(cfg: ProvidersConfig) -> List[ModelSpec]:
    specs: List[ModelSpec] = []
    for provider_key, provider in cfg.providers.items():
        for entry in provider.models:
            specs.append(
                ModelSpec(
                    provider_key=provider_key,
                    provider=provider,
                    model_id=entry.id,
                    deployment=entry.deployment,
                )
            )
    return specs


def resolve_model_specs(cfg: ProvidersConfig, selector: Optional[str]) -> List[ModelSpec]:
    """Resolve CSV selector like 'azure_openai:gpt-4o-mini,openrouter:anthropic/claude-3.5-sonnet'.

    If selector is None or empty, return all models in config.
    """
    if not selector:
        return list_model_specs(cfg)

    wanted: List[tuple[str, str]] = []
    for part in selector.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(
                f"Expected 'provider:model_id' format in selector, got '{part}'"
            )
        prov, mod = part.split(":", 1)
        wanted.append((prov.strip(), mod.strip()))

    matched: List[ModelSpec] = []
    for prov_key, mod_id in wanted:
        prov = cfg.providers.get(prov_key)
        if not prov:
            raise KeyError(f"Unknown provider key '{prov_key}' in config")
        found = None
        for entry in prov.models:
            if entry.id == mod_id:
                found = ModelSpec(
                    provider_key=prov_key,
                    provider=prov,
                    model_id=entry.id,
                    deployment=entry.deployment,
                )
                break
        if not found:
            raise KeyError(
                f"Model id '{mod_id}' not found under provider '{prov_key}'"
            )
        matched.append(found)

    return matched 