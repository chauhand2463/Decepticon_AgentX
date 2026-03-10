from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.prompts.prompt_loader import load_prompt
from src.tools.handoff import handoff_to_scout, handoff_to_guardian, handoff_to_triage, handoff_to_analyst, handoff_to_planner
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_store
from langchain_anthropic import ChatAnthropic
from src.utils.mcp.mcp_loader import load_mcp_tools

async def make_bounty_agent():
    llm = get_current_llm()
    if llm is None:
        from langchain_openai import ChatOpenAI
        import os
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), max_tokens=4000)
        print("Warning: Using fallback LLM model (OpenAI gpt-4o-mini)")

    store = get_store()

    mcp_tools = await load_mcp_tools(agent_name=["bounty"])

    swarm_tools = [
        handoff_to_scout,
        handoff_to_guardian,
        handoff_to_triage,
        handoff_to_analyst,
        handoff_to_planner
    ]

    mem_tools = [
        create_manage_memory_tool(namespace=("memories",)),
        create_search_memory_tool(namespace=("memories",))
    ]

    tools = mcp_tools + swarm_tools + mem_tools

    agent = create_react_agent(
        llm,
        tools=tools,
        store=store,
        name="Bounty",
        prompt=load_prompt("bounty", "swarm")
    )
    return agent
