import sys
import os
import time

sys.path.append('.')

def test_step(name, func):
    print(f"Testing {name}...", end='', flush=True)
    start = time.time()
    try:
        func()
        print(f" SUCCESS ({time.time()-start:.2f}s)")
    except Exception as e:
        print(f" FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

def import_rich(): import rich
def import_dotenv(): from dotenv import load_dotenv; load_dotenv()
def import_langchain(): import langchain_core
def import_models(): from src.utils.llm.models import list_available_models
def import_memory(): from src.utils.memory import get_store
def import_swarm(): from src.graphs.swarm import create_dynamic_swarm

print("--- Granular Import Test ---")
test_step("rich", import_rich)
test_step("dotenv", import_dotenv)
test_step("langchain_core", import_langchain)
test_step("src.utils.llm.models", import_models)
test_step("src.utils.memory", import_memory)
test_step("src.graphs.swarm", import_swarm)
print("--- Test Complete ---")
