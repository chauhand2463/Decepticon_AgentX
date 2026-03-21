import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.utils.mcp.config_loader import load_mcp_config
from src.swarm.graph_fixed import build_decepticon_graph_with_tools
from langchain_core.messages import AIMessage
from typing import List, Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class MockLLM(BaseChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="mock"))])

    @property
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
            print(f"[ERROR] {r} NOT found in config")

    # 3. Build graph
    print("Building graph with parallel MCP...")
    try:
        graph, tools = await build_decepticon_graph_with_tools(MockLLM(), config)
        print("[OK] Graph built successfully")
        
        # 4. Check nodes
        nodes = graph.nodes
        print(f"Graph nodes: {list(nodes.keys())}")
        
    except Exception as e:
        print(f"[FAILED] Graph building failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify())
