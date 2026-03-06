

import time
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple
from frontend.web.utils.validation import validate_model_info
from frontend.web.utils.constants import PROVIDERS

class ModelManager:

    def __init__(self):

        self.models_cache = {}
        self.cache_timestamp = 0
        self.cache_duration = 300

    def load_models_data(self) -> Dict[str, Any]:

        try:
            from src.utils.llm.models import list_available_models, check_ollama_connection

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

                model_future = executor.submit(list_available_models)
                ollama_future = executor.submit(check_ollama_connection)

                try:

                    models = model_future.result(timeout=5.0)
                    ollama_info = ollama_future.result(timeout=2.0)
                except concurrent.futures.TimeoutError:

                    models = model_future.result() if model_future.done() else []
                    ollama_info = ollama_future.result() if ollama_future.done() else {"connected": False, "count": 0}

            available_models = [m for m in models if m.get("api_key_available", False)]

            if not available_models:
                return {
                    "success": False,
                    "error": "No models available. Please set up your API keys.",
                    "type": "error"
                }

            self.models_cache = {}
            for model in available_models:
                provider = model.get('provider', 'Unknown')
                if provider not in self.models_cache:
                    self.models_cache[provider] = []
                self.models_cache[provider].append(model)

            self.cache_timestamp = time.time()

            result = {"success": True, "type": "success", "models_by_provider": self.models_cache}
            if ollama_info.get("connected", False):
                result["ollama_message"] = f"Ollama Connected - {ollama_info.get('count', 0)} local models available"

            return result

        except ImportError as e:
            return {
                "success": False,
                "error": "Model selection feature unavailable",
                "info": "Setup Required: Please install CLI dependencies",
                "type": "import_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading models: {str(e)}",
                "type": "error"
            }

    def get_cached_models_data(self, force_refresh: bool = False) -> Dict[str, Any]:

        current_time = time.time()
        needs_refresh = (
            force_refresh or
            not self.models_cache or
            current_time - self.cache_timestamp > self.cache_duration
        )

        if needs_refresh:
            return self.load_models_data()

        return {
            "success": True,
            "type": "cached",
            "models_by_provider": self.models_cache
        }

    def get_default_selection(self) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:

        default_provider = None
        default_model = None

        anthropic_provider_key = None
        for provider_key in self.models_cache.keys():
            if provider_key.lower() == "anthropic":
                anthropic_provider_key = provider_key
                break

        if anthropic_provider_key:
            anthropic_models = self.models_cache[anthropic_provider_key]
            for model in anthropic_models:
                if "claude-3-5-sonnet" in model.get("model_name", "").lower():
                    default_provider = anthropic_provider_key
                    default_model = model
                    break

        if not default_model and anthropic_provider_key:
            default_provider = anthropic_provider_key
            default_model = self.models_cache[anthropic_provider_key][0]

        if not default_model:
            providers = list(self.models_cache.keys())
            if providers:
                default_provider = providers[0]
                default_model = self.models_cache[default_provider][0]

        return default_provider, default_model

    def validate_model_selection(self, model_info: Dict[str, Any]) -> Dict[str, Any]:

        return validate_model_info(model_info)

    def prepare_model_initialization(self, model_info: Dict[str, Any]) -> Dict[str, Any]:

        validation_result = self.validate_model_selection(model_info)
        if not validation_result["valid"]:
            return {
                "ready": False,
                "errors": validation_result["errors"]
            }

        required_fields = ["model_name", "provider", "display_name"]
        missing_fields = [field for field in required_fields if not model_info.get(field)]

        if missing_fields:
            return {
                "ready": False,
                "errors": [f"Missing required fields: {', '.join(missing_fields)}"]
            }

        return {
            "ready": True,
            "model_info": model_info
        }

    def reset_cache(self):

        self.models_cache = {}
        self.cache_timestamp = 0

    def get_provider_models(self, provider: str) -> List[Dict[str, Any]]:

        return self.models_cache.get(provider, [])

    def get_available_providers(self) -> List[str]:

        return list(self.models_cache.keys())

    def find_model_by_name(self, model_name: str, provider: str = None) -> Optional[Dict[str, Any]]:

        if provider:
            models = self.get_provider_models(provider)
            for model in models:
                if model.get("model_name") == model_name:
                    return model
        else:

            for provider_models in self.models_cache.values():
                for model in provider_models:
                    if model.get("model_name") == model_name:
                        return model

        return None

_model_manager = None

def get_model_manager() -> ModelManager:

    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager