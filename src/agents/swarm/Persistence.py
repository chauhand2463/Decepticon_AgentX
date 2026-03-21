from langgraph.prebuilt import create_react_agent
from src.prompts.prompt_loader import load_prompt
from src.tools.handoff import handoff_to_privilege_escalation
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_store
from langchain_anthropic import ChatAnthropic
from src.utils.mcp.mcp_loader import load_mcp_tools


async def make_persistence_agent():
    llm = get_current_llm()
    if llm is None:
        llm = ChatAnthropic(model_name="claude-3-5-sonnet-latest", temperature=0)

    store = get_store()

    mcp_tools = await load_mcp_tools(agent_name=["persistence"])

    swarm_tools = [handoff_to_privilege_escalation]

    tools = mcp_tools + swarm_tools

    agent = create_react_agent(
        llm,
        tools=tools,
        store=store,
        name="Persistence",
        prompt=load_prompt("persistence", "swarm"),
    )
    return agent
