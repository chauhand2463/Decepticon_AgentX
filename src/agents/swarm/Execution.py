from langgraph.prebuilt import create_react_agent
from src.prompts.prompt_loader import load_prompt
from src.tools.handoff import handoff_to_persistence
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_store
from langchain_anthropic import ChatAnthropic
from src.utils.mcp.mcp_loader import load_mcp_tools


async def make_execution_agent():
    llm = get_current_llm()
    if llm is None:
        llm = ChatAnthropic(model_name="claude-3-5-sonnet-latest", temperature=0)

    store = get_store()

    # Load tools for execution agent (metasploit, terminal, etc.)
    mcp_tools = await load_mcp_tools(agent_name=["execution"])

    swarm_tools = [handoff_to_persistence]

    tools = mcp_tools + swarm_tools

    agent = create_react_agent(
        llm,
        tools=tools,
        store=store,
        name="Execution",
        prompt=load_prompt("execution", "swarm"),
    )
    return agent
