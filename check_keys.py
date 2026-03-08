import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")

if not key or key == "your-api-key" or key.startswith("sk-or-v1-"):
    print(f"Checking key: {key[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://decepticon.ai",
        "X-Title": "Decepticon Diagnostic"
    }
    
    try:
        response = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No valid looking OpenRouter key found.")
