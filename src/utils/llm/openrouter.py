from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import os


def create_openrouter_model(model_name: str, temperature: float = 0.0):

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY . "
            ".env  OPENROUTER_API_KEY=your-key ."
        )

    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        model_kwargs={"max_tokens": 4000},
        default_headers={
            "HTTP-Referer": "https://decepticon.cyber",
            "X-Title": "Decepticon",
            "Authorization": f"Bearer {api_key}",
        },
    )


def get_openrouter_api_key() -> str:

    return os.getenv("OPENROUTER_API_KEY", "")


def is_openrouter_available() -> bool:

    return bool(get_openrouter_api_key())
