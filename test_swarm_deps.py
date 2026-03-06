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

def call_get_checkpointer(): from src.utils.memory import get_checkpointer; get_checkpointer()
def call_get_store(): from src.utils.memory import get_store; get_store()
def import_recon(): from src.agents.swarm.Recon import make_recon_agent
def import_initaccess(): from src.agents.swarm.InitAccess import make_initaccess_agent
def import_planner(): from src.agents.swarm.Planner import make_planner_agent
def import_summary(): from src.agents.swarm.Summary import make_summary_agent

print("--- Swarm Dependency Test ---")
test_step("get_checkpointer()", call_get_checkpointer)
test_step("get_store()", call_get_store)
test_step("import Recon", import_recon)
test_step("import InitAccess", import_initaccess)
test_step("import Planner", import_planner)
test_step("import Summary", import_summary)
print("--- Test Complete ---")
