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

def import_langgraph_prebuilt(): from langgraph.prebuilt import create_react_agent
def import_prompt_loader(): from src.prompts.prompt_loader import load_prompt
def import_handoff(): from src.tools.handoff import handoff_to_planner
def import_mcp_adapter(): from langchain_mcp_adapters.client import MultiServerMCPClient
def import_langmem(): from langmem import create_manage_memory_tool
def import_llm_config(): from src.utils.llm.config_manager import get_current_llm
def import_mcp_loader(): from src.utils.mcp.mcp_loader import load_mcp_tools

print("--- Recon Import Dependency Test ---")
test_step("langgraph.prebuilt", import_langgraph_prebuilt)
test_step("src.prompts.prompt_loader", import_prompt_loader)
test_step("src.tools.handoff", import_handoff)
test_step("langchain_mcp_adapters", import_mcp_adapter)
test_step("langmem", import_langmem)
test_step("src.utils.llm.config_manager", import_llm_config)
test_step("src.utils.mcp.mcp_loader", import_mcp_loader)
print("--- Test Complete ---")
