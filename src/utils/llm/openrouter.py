

from langchain_openai import ChatOpenAI
import os

def create_openrouter_model(model_name: str, temperature: float = 0.0):

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일에 OPENROUTER_API_KEY=your-key 를 추가하세요."
        )

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=4000,
        model_kwargs={
            "extra_headers": {
                "HTTP-Referer": "https://decepticon.cyber",
                "X-Title": "Decepticon",
            }
        }
    )

def get_openrouter_api_key() -> str:

    return os.getenv("OPENROUTER_API_KEY", "")

def is_openrouter_available() -> bool:

    return bool(get_openrouter_api_key())