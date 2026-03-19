"""
DECEPTICON — Fixed Swarm Graph
ROOT CAUSE: Graph had no add_edge() calls connecting agents.
PHANTOM planned but then graph hit END immediately.

FIX: Wire all 5 agents with edges + conditional routing based on findings.

DROP THIS FILE into your project at:
  src/swarm/graph.py  (or wherever your graph is defined)

Then import and use:
  from src.swarm.graph import build_decepticon_graph, DecepticonState
"""

import json
import asyncio
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage


# 
# STATE — carries everything between agents
# 

class DecepticonState(TypedDict):
    # Core message history (all agents read/write this)
    messages:   Annotated[list, add_messages]

    # Mission metadata (set by PHANTOM)
    mission_type:  str       # RECON_ONLY | VULN_SCAN | FULL_PENTEST | WEB_AUDIT | BUG_BOUNTY
    target:        str
    phase:         str       # planning | recon | research | exploitation | reporting | done

    # SHADOW (recon) output
    open_ports:    List[dict]
    services:      List[dict]
    subdomains:    List[str]
    web_services:  List[dict]

    # ORACLE (researcher) output
    cves:          List[dict]
    exploits:      List[dict]
    attack_order:  List[str]

    # BREACH (access) output
    shells:        List[dict]
    credentials:   List[dict]
    exploitation_success: bool

    # CIPHER (summary) output
    final_report:  str


# 
# ROUTING FUNCTIONS
# 

def route_after_planner(state: DecepticonState) -> str:
    """
    After PHANTOM plans, always go to SHADOW for recon.
    PHANTOM's job is only to plan — SHADOW always executes first.
    """
    mission_type = state.get("mission_type", "FULL_PENTEST")

    # Extract mission_type from the last AI message if state field not set yet
    if not mission_type or mission_type == "FULL_PENTEST":
        for msg in reversed(state.get("messages", [])):
            if hasattr(msg, "content") and isinstance(msg.content, str):
                content = msg.content
                if "RECON_ONLY" in content:
                    mission_type = "RECON_ONLY"
                    break
                elif "VULN_SCAN" in content:
                    mission_type = "VULN_SCAN"
                    break
                elif "BUG_BOUNTY" in content:
                    return "guardian"  # Bug bounty  scope check first
                elif "FULL_PENTEST" in content or "WEB_AUDIT" in content:
                    mission_type = "FULL_PENTEST"
                    break

    # All mission types start with recon
    return "shadow"


def route_after_recon(state: DecepticonState) -> str:
    """
    After SHADOW scans, decide next step based on what was found.
    RECON_ONLY  skip to cipher (report only)
    Otherwise   always go to oracle (research CVEs)
    """
    mission_type = state.get("mission_type", "FULL_PENTEST")

    # Check messages for mission type if state not set
    for msg in reversed(state.get("messages", [])):
        content = getattr(msg, "content", "")
        if "RECON_ONLY" in content:
            mission_type = "RECON_ONLY"
            break

    if mission_type == "RECON_ONLY":
        return "cipher"   # Recon only — skip exploitation, just report

    return "oracle"       # Everything else goes to vulnerability research


def route_after_research(state: DecepticonState) -> str:
    """
    After ORACLE finds CVEs, decide whether to exploit.
    VULN_SCAN     report only (no exploitation)
    FULL_PENTEST  exploit if high/critical findings exist
    """
    mission_type = state.get("mission_type", "FULL_PENTEST")

    for msg in reversed(state.get("messages", [])):
        content = getattr(msg, "content", "")
        if "VULN_SCAN" in content:
            mission_type = "VULN_SCAN"
            break

    if mission_type == "VULN_SCAN":
        return "cipher"   # Scan only — no exploitation

    # Check if there are exploitable findings
    cves = state.get("cves", [])
    has_critical = any(
        v.get("severity", "").upper() in ("CRITICAL", "HIGH")
        for v in cves
    )

    # Also check last oracle message for critical/high keywords
    if not cves:
        for msg in reversed(state.get("messages", [])):
            content = getattr(msg, "content", "").lower()
            if "critical" in content or "high" in content:
                if "cvss" in content or "exploit" in content or "cve-" in content:
                    has_critical = True
                    break

    if has_critical:
        return "breach"   # Found exploitable vulns  go exploit them
    return "cipher"       # Nothing exploitable  just report


def route_after_exploitation(state: DecepticonState) -> str:
    """After BREACH, always go to CIPHER for final report."""
    return "cipher"


# 
# AGENT NODE WRAPPERS
# 

def make_agent_node(agent, node_name: str):
    """
    Wraps a LangGraph ReAct agent as a graph node.
    Extracts structured data from agent output and updates state.
    """
    async def node_fn(state: DecepticonState) -> dict:
        print(f"\n{'='*60}")
        print(f" DECEPTICON — {node_name.upper()} EXECUTING")
        print(f"{'='*60}")

        # Run the agent
        result = await agent.ainvoke(state)
        new_messages = result.get("messages", [])

        # Try to extract structured data from the last message
        updates = {"messages": new_messages, "phase": node_name}

        last_content = ""
        for msg in reversed(new_messages):
            if hasattr(msg, "content") and isinstance(msg.content, str):
                last_content = msg.content
                break

        # Extract structured state updates from agent output
        if node_name == "phantom":
            updates.update(_extract_planner_data(last_content))

        elif node_name == "shadow":
            updates.update(_extract_recon_data(last_content))

        elif node_name == "oracle":
            updates.update(_extract_research_data(last_content))

        elif node_name == "breach":
            updates.update(_extract_exploitation_data(last_content))

        elif node_name == "cipher":
            updates["final_report"] = last_content
            updates["phase"] = "done"

        print(f" {node_name.upper()} complete")
        return updates

    node_fn.__name__ = f"{node_name}_node"
    return node_fn


def _extract_planner_data(content: str) -> dict:
    """Extract mission_type and target from PHANTOM's JSON plan."""
    updates = {}
    try:
        # Find JSON block in content
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start >= 0 and end > start:
            plan = json.loads(content[start:end])
            updates["mission_type"] = plan.get("mission_type", "FULL_PENTEST")
            updates["target"]       = plan.get("target", "")
    except Exception:
        # Can't parse JSON — use keyword detection
        if "RECON_ONLY" in content:
            updates["mission_type"] = "RECON_ONLY"
        elif "VULN_SCAN" in content:
            updates["mission_type"] = "VULN_SCAN"
        else:
            updates["mission_type"] = "FULL_PENTEST"
    return updates


def _extract_recon_data(content: str) -> dict:
    """Extract open ports, services, subdomains from SHADOW's JSON output."""
    updates = {"open_ports": [], "services": [], "subdomains": [], "web_services": []}
    try:
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            active = data.get("active_recon", {})
            updates["open_ports"]   = active.get("open_ports", [])
            updates["services"]     = active.get("open_ports", [])  # same field
            updates["web_services"] = active.get("web_services", [])
            passive = data.get("passive_recon", {})
            updates["subdomains"]   = passive.get("subdomains", [])
    except Exception:
        pass
    return updates


def _extract_research_data(content: str) -> dict:
    """Extract CVEs and attack order from ORACLE's JSON output."""
    updates = {"cves": [], "exploits": [], "attack_order": []}
    try:
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            updates["cves"]         = data.get("vulnerabilities", [])
            updates["exploits"]     = data.get("vulnerabilities", [])
            updates["attack_order"] = data.get("attack_order", [])
    except Exception:
        pass
    return updates


def _extract_exploitation_data(content: str) -> dict:
    """Extract shells and credentials from BREACH's JSON output."""
    updates = {"shells": [], "credentials": [], "exploitation_success": False}
    try:
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            success = data.get("successful_exploits", [])
            updates["shells"]               = success
            updates["exploitation_success"] = len(success) > 0
            # Extract any credentials found
            for s in success:
                if s.get("credentials_obtained"):
                    updates["credentials"].extend(s["credentials_obtained"])
    except Exception:
        pass
    return updates


# 
# GRAPH BUILDER — THE MAIN FIX
# 

async def build_decepticon_graph(llm, mcp_config: dict):
    """
    Builds and compiles the full DECEPTICON swarm graph.

    Args:
        llm:        Your LangChain LLM instance (Claude, GPT-4, etc.)
        mcp_config: Dict from your mcp_config.json

    Returns:
        Compiled LangGraph graph ready to invoke.

    Usage:
        graph = await build_decepticon_graph(llm, mcp_config)
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="Scan 192.168.1.1 for vulns")],
            "mission_type": "",
            "target": "",
            "phase": "planning",
            "open_ports": [], "services": [], "subdomains": [], "web_services": [],
            "cves": [], "exploits": [], "attack_order": [],
            "shells": [], "credentials": [], "exploitation_success": False,
            "final_report": "",
        })
    """
    from src.prompts.elite_prompts import (
        PLANNER_SYSTEM_PROMPT,
        RECON_SYSTEM_PROMPT,
        RESEARCHER_SYSTEM_PROMPT,
        ACCESS_SYSTEM_PROMPT,
        SUMMARY_SYSTEM_PROMPT,
    )

    #  Load MCP tools  
    async def get_tools(agent_key: str) -> list:
        servers = mcp_config.get(agent_key, {})
        if not servers or "note" in servers:
            return []
        try:
            client = MultiServerMCPClient(servers)
            return await client.get_tools()
        except Exception as e:
            print(f"[WARN] Could not load MCP tools for {agent_key}: {e}")
            return []

    nmap_tools    = await get_tools("recon_agent")
    nuclei_tools  = await get_tools("researcher_agent")
    access_tools  = await get_tools("access_agent")

    print(f"[DECEPTICON] Loaded tools: nmap={len(nmap_tools)}, nuclei={len(nuclei_tools)}, access={len(access_tools)}")

    #  Create agents  
    phantom = create_react_agent(llm, tools=[],
                                 state_modifier=PLANNER_SYSTEM_PROMPT)

    shadow  = create_react_agent(llm, tools=nmap_tools,
                                 state_modifier=RECON_SYSTEM_PROMPT)

    oracle  = create_react_agent(llm, tools=nuclei_tools,
                                 state_modifier=RESEARCHER_SYSTEM_PROMPT)

    breach  = create_react_agent(llm, tools=access_tools,
                                 state_modifier=ACCESS_SYSTEM_PROMPT)

    cipher  = create_react_agent(llm, tools=[],
                                 state_modifier=SUMMARY_SYSTEM_PROMPT)

    #  Build graph  
    graph = StateGraph(DecepticonState)

    # Add all agent nodes
    graph.add_node("phantom", make_agent_node(phantom, "phantom"))
    graph.add_node("shadow",  make_agent_node(shadow,  "shadow"))
    graph.add_node("oracle",  make_agent_node(oracle,  "oracle"))
    graph.add_node("breach",  make_agent_node(breach,  "breach"))
    graph.add_node("cipher",  make_agent_node(cipher,  "cipher"))

    #  THE CRITICAL PART: Wire the edges  
    #
    # THIS IS WHAT WAS MISSING. Without these edges, the graph
    # terminates after PHANTOM because it has nowhere to go.
    #
    #   PHANTOM  (conditional)  SHADOW  (conditional)  ORACLE
    #            (conditional)  BREACH  CIPHER  END

    # Entry point
    graph.set_entry_point("phantom")

    # PHANTOM  routes to SHADOW (always) or GUARDIAN (bug bounty)
    graph.add_conditional_edges(
        "phantom",
        route_after_planner,
        {
            "shadow":   "shadow",
            "guardian": "shadow",  # fallback to shadow if no guardian
        }
    )

    # SHADOW  routes based on mission type
    graph.add_conditional_edges(
        "shadow",
        route_after_recon,
        {
            "oracle": "oracle",
            "cipher": "cipher",   # RECON_ONLY skips research
        }
    )

    # ORACLE  routes based on mission type + findings
    graph.add_conditional_edges(
        "oracle",
        route_after_research,
        {
            "breach": "breach",
            "cipher": "cipher",   # VULN_SCAN or no exploitable findings
        }
    )

    # BREACH  always goes to CIPHER for report
    graph.add_edge("breach", "cipher")

    # CIPHER  END
    graph.add_edge("cipher", END)

    return graph.compile()


# 
# CONVENIENCE: build graph without MCP (for testing)
# 

async def build_decepticon_graph_no_mcp(llm):
    """
    Same graph but with NO MCP tools — agents use their built-in knowledge.
    Useful for testing the graph routing without running actual tools.
    """
    from src.prompts.elite_prompts import (
        PLANNER_SYSTEM_PROMPT,
        RECON_SYSTEM_PROMPT,
        RESEARCHER_SYSTEM_PROMPT,
        ACCESS_SYSTEM_PROMPT,
        SUMMARY_SYSTEM_PROMPT,
    )

    phantom = create_react_agent(llm, tools=[], state_modifier=PLANNER_SYSTEM_PROMPT)
    shadow  = create_react_agent(llm, tools=[], state_modifier=RECON_SYSTEM_PROMPT)
    oracle  = create_react_agent(llm, tools=[], state_modifier=RESEARCHER_SYSTEM_PROMPT)
    breach  = create_react_agent(llm, tools=[], state_modifier=ACCESS_SYSTEM_PROMPT)
    cipher  = create_react_agent(llm, tools=[], state_modifier=SUMMARY_SYSTEM_PROMPT)

    graph = StateGraph(DecepticonState)
    graph.add_node("phantom", make_agent_node(phantom, "phantom"))
    graph.add_node("shadow",  make_agent_node(shadow,  "shadow"))
    graph.add_node("oracle",  make_agent_node(oracle,  "oracle"))
    graph.add_node("breach",  make_agent_node(breach,  "breach"))
    graph.add_node("cipher",  make_agent_node(cipher,  "cipher"))

    graph.set_entry_point("phantom")
    graph.add_conditional_edges("phantom", route_after_planner, {"shadow": "shadow", "guardian": "shadow"})
    graph.add_conditional_edges("shadow",  route_after_recon,   {"oracle": "oracle", "cipher": "cipher"})
    graph.add_conditional_edges("oracle",  route_after_research, {"breach": "breach", "cipher": "cipher"})
    graph.add_edge("breach", "cipher")
    graph.add_edge("cipher", END)

    return graph.compile()


# 
# INITIAL STATE HELPER
# 

def make_initial_state(user_input: str) -> DecepticonState:
    """Create a properly initialised state for a new mission."""
    return {
        "messages":             [HumanMessage(content=user_input)],
        "mission_type":         "",
        "target":               "",
        "phase":                "planning",
        "open_ports":           [],
        "services":             [],
        "subdomains":           [],
        "web_services":         [],
        "cves":                 [],
        "exploits":             [],
        "attack_order":         [],
        "shells":               [],
        "credentials":          [],
        "exploitation_success": False,
        "final_report":         "",
    }


# 
# PLUG INTO YOUR CLI — replace your existing run_swarm call with this
# 

async def run_mission(user_input: str, llm, mcp_config: dict = None) -> dict:
    """
    Drop-in replacement for whatever currently calls the planner-only graph.

    Before (broken):
        result = await planner.ainvoke({"messages": [...]})
        #  stops here, only PHANTOM ran

    After (fixed):
        result = await run_mission("Scan 192.168.1.1", llm, mcp_config)
        #  PHANTOM  SHADOW  ORACLE  BREACH  CIPHER all run
    """
    if mcp_config:
        graph = await build_decepticon_graph(llm, mcp_config)
    else:
        graph = await build_decepticon_graph_no_mcp(llm)

    state = make_initial_state(user_input)

    print(f"\n DECEPTICON MISSION STARTING")
    print(f"Input: {user_input[:80]}...")
    print("Flow: PHANTOM  SHADOW  ORACLE  BREACH  CIPHER\n")

    result = await graph.ainvoke(state)

    print(f"\n{'='*60}")
    print(f" MISSION COMPLETE | Phase: {result.get('phase')}")
    print(f"Ports found: {len(result.get('open_ports', []))}")
    print(f"CVEs found:  {len(result.get('cves', []))}")
    print(f"Exploited:   {result.get('exploitation_success', False)}")
    print(f"{'='*60}\n")

    return result