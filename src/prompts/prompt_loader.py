
from src.prompts.base.terminal import BASE_TERMINAL_PROMPT

from src.prompts.elite_prompts import (
    PLANNER_SYSTEM_PROMPT,
    RECON_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    ACCESS_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT
)

# Keep old imports for reference or if needed for other architectures
from src.prompts.personas.reconnaissance_persona import RECONNAISSANCE_PERSONA_PROMPT
from src.prompts.personas.initial_access_persona import INITIAL_ACCESS_PERSONA_PROMPT
from src.prompts.personas.planner_persona import PLANNER_PERSONA_PROMPT
from src.prompts.personas.summary_persona import SUMMARY_PERSONA_PROMPT
from src.prompts.personas.supervisor_persona import SUPERVISOR_PERSONA_PROMPT
from src.prompts.personas.bounty_persona import BOUNTY_PERSONA_PROMPT
from src.prompts.personas.scout_persona import SCOUT_PERSONA_PROMPT
from src.prompts.personas.triage_persona import TRIAGE_PERSONA_PROMPT
from src.prompts.personas.guardian_persona import GUARDIAN_PERSONA_PROMPT
from src.prompts.personas.analyst_persona import ANALYST_PERSONA_PROMPT

from src.prompts.swarm.summary import SWARM_SUMMARY_PROMPT
from src.prompts.swarm.planner import SWARM_PLANNER_PROMPT
from src.prompts.swarm.recon import SWARM_RECON_PROMPT
from src.prompts.swarm.initaccess import SWARM_INITACCESS_PROMPT
from src.prompts.swarm.researcher import SWARM_RESEARCHER_PROMPT

from src.prompts.tools.swarm_handoff_tools import SWARM_HANDOFF_TOOLS_PROMPT

PERSONA_PROMPTS = {
    "reconnaissance": RECON_SYSTEM_PROMPT,
    "initial_access": ACCESS_SYSTEM_PROMPT,
    "planner": PLANNER_SYSTEM_PROMPT,
    "summary": SUMMARY_SYSTEM_PROMPT,
    "supervisor": SUPERVISOR_PERSONA_PROMPT,
    "researcher": RESEARCHER_SYSTEM_PROMPT,
    "bounty": BOUNTY_PERSONA_PROMPT,
    "scout": SCOUT_PERSONA_PROMPT,
    "triage": TRIAGE_PERSONA_PROMPT,
    "guardian": GUARDIAN_PERSONA_PROMPT,
    "analyst": ANALYST_PERSONA_PROMPT
}

SWARM_PROMPTS = {
    "reconnaissance": SWARM_RECON_PROMPT,
    "initial_access": SWARM_INITACCESS_PROMPT,
    "planner": SWARM_PLANNER_PROMPT,
    "summary": SWARM_SUMMARY_PROMPT,
    "researcher": SWARM_RESEARCHER_PROMPT,
    "supervisor": ""
}

def load_prompt(agent_name: str, architecture: str = "swarm"):

    if agent_name not in PERSONA_PROMPTS:
        available_agents = list(PERSONA_PROMPTS.keys())
        raise ValueError(f"Unknown agent: {agent_name}. Available agents: {available_agents}")

    prompt = BASE_TERMINAL_PROMPT + PERSONA_PROMPTS[agent_name]

    if architecture == "swarm" and agent_name != "supervisor":
        swarm_prompt = SWARM_PROMPTS.get(agent_name, "")
        if swarm_prompt:
            prompt += swarm_prompt
        prompt += SWARM_HANDOFF_TOOLS_PROMPT

    return prompt

def get_available_agents():

    return list(PERSONA_PROMPTS.keys())

def get_supported_architectures():

    return ["swarm", "hierarchical", "standalone"]

def get_terminal_base_prompt():

    return BASE_TERMINAL_PROMPT