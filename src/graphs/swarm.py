from src.agents.swarm.Recon import make_recon_agent
from src.agents.swarm.InitAccess import make_initaccess_agent
from src.agents.swarm.Planner import make_planner_agent
from src.agents.swarm.Summary import make_summary_agent
from src.agents.swarm.Researcher import make_researcher_agent
from src.agents.swarm.Bounty import make_bounty_agent
from src.agents.swarm.Scout import make_scout_agent
from src.agents.swarm.Triage import make_triage_agent
from src.agents.swarm.Guardian import make_guardian_agent
from src.agents.swarm.Analyst import make_analyst_agent
from src.utils.swarm.swarm import create_swarm
from src.utils.memory import get_checkpointer, get_store
import asyncio
import logging

logger = logging.getLogger(__name__)

checkpointer = get_checkpointer()
store = get_store()

async def create_agents():

    recon = await make_recon_agent()
    initaccess = await make_initaccess_agent()
    planner = await make_planner_agent()
    summary = await make_summary_agent()
    researcher = await make_researcher_agent()
    bounty = await make_bounty_agent()
    scout = await make_scout_agent()
    triage = await make_triage_agent()
    guardian = await make_guardian_agent()
    analyst = await make_analyst_agent()
    return [recon, initaccess, planner, summary, researcher, bounty, scout, triage, guardian, analyst]

async def create_dynamic_swarm():

    logger.info("Creating dynamic swarm with InMemory persistence")

    agents = await create_agents()
    workflow = create_swarm(
        agents=agents,
        default_active_agent="Planner",
    )

    compiled_workflow = workflow.compile(
        checkpointer=checkpointer,
        store=store
    )

    logger.info("Swarm compiled with InMemory checkpointer and store")
    return compiled_workflow