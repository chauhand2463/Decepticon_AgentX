

import json
import os
import requests
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

class ModelProvider(str, Enum):

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    GOOGLE = "google"

@dataclass
class ModelInfo:

    display_name: str
    model_name: str
    provider: ModelProvider
    api_key_available: bool = False

def load_cloud_models() -> List[ModelInfo]:

    config_path = Path(__file__).parent / "cloud_config.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            models_data = json.load(f)

        models = []
        for model_data in models_data:
            try:
                provider = ModelProvider(model_data["provider"])
                api_key_available = validate_api_key(provider)

                models.append(ModelInfo(
                    display_name=model_data["display_name"],
                    model_name=model_data["model_name"],
                    provider=provider,
                    api_key_available=api_key_available
                ))
            except (ValueError, KeyError):

                continue

        return models

    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_local_model_mappings() -> Dict[str, str]:

    config_path = Path(__file__).parent / "local_config.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            models_data = json.load(f)

        mappings = {}
        for model_data in models_data:
            try:
                if model_data.get("provider") == "ollama":
                    mappings[model_data["model_name"]] = model_data["display_name"]
            except KeyError:
                continue

        return mappings

    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_ollama_models_with_mappings() -> List[ModelInfo]:

    display_name_mappings = load_local_model_mappings()

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            models = []

            for model in models_data:
                model_name = model["name"]

                if model_name in display_name_mappings:
                    display_name = display_name_mappings[model_name]
                else:
                    display_name = f"{model_name} (Installed)"

                models.append(ModelInfo(
                    display_name=display_name,
                    model_name=model_name,
                    provider=ModelProvider.OLLAMA,
                    api_key_available=True
                ))

            return models
    except requests.RequestException:
        pass

    return []

_api_key_status_cache = {}

def validate_api_key(provider: ModelProvider) -> bool:
    if provider in _api_key_status_cache:
        return _api_key_status_cache[provider]

    key_map = {
        ModelProvider.OPENAI: "OPENAI_API_KEY",
        ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        ModelProvider.OPENROUTER: "OPENROUTER_API_KEY",
        ModelProvider.GROQ: "GROQ_API_KEY",
        ModelProvider.GOOGLE: "GOOGLE_API_KEY",
    }

    if provider == ModelProvider.OLLAMA:

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            status = (response.status_code == 200)
            _api_key_status_cache[provider] = status
            return status
        except requests.RequestException:
            _api_key_status_cache[provider] = False
            return False

    required_key = key_map.get(provider)
    key = os.getenv(required_key) if required_key else None
    
    if not key:
        _api_key_status_cache[provider] = False
        return False
        
    try:
        if provider == ModelProvider.OPENROUTER:
            res = requests.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {key}"}, timeout=3)
            status = (res.status_code == 200)
            _api_key_status_cache[provider] = status
            return status
            
        elif provider == ModelProvider.ANTHROPIC:
            res = requests.get("https://api.anthropic.com/v1/models", headers={"x-api-key": key, "anthropic-version": "2023-06-01"}, timeout=3)
            status = (res.status_code == 200)
            _api_key_status_cache[provider] = status
            return status
            
    except requests.RequestException:
        pass

    _api_key_status_cache[provider] = True
    return True

def check_ollama_connection() -> Dict[str, Any]:

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "connected": True,
                "url": "http://localhost:11434",
                "models": [model.get("name", "") for model in models],
                "count": len(models)
            }
        else:
            return {
                "connected": False,
                "url": "http://localhost:11434",
                "error": f"HTTP {response.status_code}",
                "models": [],
                "count": 0
            }
    except requests.RequestException as e:
        return {
            "connected": False,
            "url": "http://localhost:11434",
            "error": str(e),
            "models": [],
            "count": 0
        }

def list_available_models() -> List[Dict[str, Any]]:

    all_models = []

    all_models.extend(load_cloud_models())

    all_models.extend(get_ollama_models_with_mappings())

    return [
        {
            "display_name": model.display_name,
            "model_name": model.model_name,
            "provider": model.provider.value,
            "api_key_available": model.api_key_available
        }
        for model in all_models
    ]

def load_llm_model(model_name: str, provider: str, temperature: float = 0.0):

    try:
        provider_enum = ModelProvider(provider)
    except ValueError:
        raise ValueError(f"Unsupported provider: {provider}")

    if provider_enum == ModelProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name,
            temperature=0
        )

    elif provider_enum == ModelProvider.OPENAI:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            max_tokens=4000,
        )



    elif provider_enum == ModelProvider.OLLAMA:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model_name,
            temperature=0,
            num_ctx=8192,
        )



    elif provider_enum == ModelProvider.OPENROUTER:
        from .openrouter import create_openrouter_model
        return create_openrouter_model(
            model_name=model_name,
            temperature=temperature
        )

    elif provider_enum == ModelProvider.GROQ:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_name,
            temperature=temperature
        )

    elif provider_enum == ModelProvider.GOOGLE:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")

__all__ = [
    "load_llm_model",
    "list_available_models",
    "validate_api_key",
    "check_ollama_connection",
    "ModelProvider",
    "ModelInfo",

    "load_cloud_models",
    "load_local_model_mappings",
    "get_ollama_models_with_mappings"
]

