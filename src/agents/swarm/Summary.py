from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.prompts.prompt_loader import load_prompt
from src.tools.handoff import (
    handoff_to_initial_access,
    handoff_to_reconnaissance,
    handoff_to_planner,
    handoff_to_researcher,
)
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_store

from src.utils.mcp.mcp_loader import load_mcp_tools


async def make_summary_agent():

    llm = get_current_llm()
    if llm is None:
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(
            model_name="claude-3-5-sonnet-latest", temperature=0, timeout=60, stop=None
        )
        print("Warning: Using default LLM model (Claude 3.5 Sonnet)")

    store = get_store()

    mcp_tools = await load_mcp_tools(agent_name=["summary"])

    swarm_tools = [
        handoff_to_reconnaissance,
        handoff_to_researcher,
        handoff_to_initial_access,
        handoff_to_planner,
    ]

    mem_tools = [
        create_manage_memory_tool(namespace=("memories",)),
        create_search_memory_tool(namespace=("memories",)),
    ]

    tools = mcp_tools + swarm_tools + mem_tools

    agent = create_react_agent(
        llm,
        tools=tools,
        store=store,
        name="Summary",
        prompt=load_prompt("summary", "swarm"),
    )
    return agent
