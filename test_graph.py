import asyncio
import os
import sys
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.swarm.graph_fixed import build_decepticon_graph
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Try to load .env if it exists
load_dotenv()

async def test_recon():
    print("Building graph...")
    # Load MCP config
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "mcp_config.json")
    with open(config_path, "r") as f:
        mcp_config = json.load(f)

    # Use Sonnet 3.7 as per user preference
    llm = ChatAnthropic(model="claude-3-7-sonnet-latest")
    
    graph = await build_decepticon_graph(llm, mcp_config)
    
    state = {
        "messages": [("user", "Scan 192.168.1.1 with nmap for all ports")]
    }
    
    print("Invoking graph...")
    async for event in graph.astream(state):
        for node_name, output in event.items():
            print(f"--- Node: {node_name} ---")
            # We already have debug prints in graph_fixed.py's node_fn
    
    print("Test complete.")

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found in environment.")
    else:
        asyncio.run(test_recon())