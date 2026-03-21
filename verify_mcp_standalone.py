import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.utils.mcp.config_loader import load_mcp_config
from src.swarm.graph_fixed import build_decepticon_graph_with_tools
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage


from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class MockLLM(BaseChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="mock"))])

    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        return self


async def verify():
    print("--- DECEPTICON MCP VERIFICATION ---")

    # 1. Load config
    config = load_mcp_config()
    print(f"Loaded config keys: {list(config.keys())}")

    # 2. Check for required keys
    required = ["reconnaissance", "researcher", "initial_access"]
    for r in required:
        if r in config:
            print(f"[OK] {r} found in config")
        else:
            print(f"[ERROR] {r} MISSING from config")

    # 3. Build graph and get tools
    # We use a mock LLM because we only care about tool loading in the builder
    mock_llm = MockLLM()

    print("\nBuilding graph and loading tools (this may take a moment)...")
    try:
        graph, tools_dict = await build_decepticon_graph_with_tools(mock_llm, config)

        print("\n--- RESULTS ---")
        for agent, tools in tools_dict.items():
            print(f"Agent: {agent:20} | Tools loaded: {len(tools)}")
            if len(tools) > 0:
                print(f"  Example tools: {[t.name for t in tools[:3]]}")
    except Exception as e:
        print(f"[ERROR] Error during verification: {e}")


if __name__ == "__main__":
    asyncio.run(verify())
