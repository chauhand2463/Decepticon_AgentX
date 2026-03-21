from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool
from src.prompts.prompt_loader import load_prompt
from src.tools.handoff import handoff_to_bounty, handoff_to_guardian, handoff_to_analyst
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_store
from langchain_anthropic import ChatAnthropic
from src.utils.mcp.mcp_loader import load_mcp_tools


async def make_triage_agent():
    llm = get_current_llm()
    if llm is None:
        llm = ChatAnthropic(
            model_name="claude-3-5-sonnet-latest", temperature=0, timeout=60, stop=None
        )
        print("Warning: Using default LLM model (Claude 3.5 Sonnet)")

    store = get_store()

    mcp_tools = await load_mcp_tools(agent_name=["triage"])

    swarm_tools = [handoff_to_bounty, handoff_to_guardian, handoff_to_analyst]

    mem_tools = [
        create_manage_memory_tool(namespace=("memories",)),
        create_search_memory_tool(namespace=("memories",)),
    ]

    tools = mcp_tools + swarm_tools + mem_tools

    agent = create_react_agent(
        llm,
        tools=tools,
        store=store,
        name="Triage",
        prompt=load_prompt("triage", "swarm"),
    )
    return agent
