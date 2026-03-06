import sys
import os

sys.path.append('.')

try:
    print("Testing imports...")
    import rich
    print("Rich imported")
    from dotenv import load_dotenv
    load_dotenv()
    print("dotenv loaded")
    import langchain_core
    print("langchain_core imported")
    from src.utils.llm.models import list_available_models
    print("src.utils.llm.models imported")
    models = list_available_models()
    print(f"Available models: {len(models)}")
    print("All imports successful")
except Exception as e:
    print(f"Error during import test: {str(e)}")
    import traceback
    traceback.print_exc()
