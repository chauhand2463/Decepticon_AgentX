"""
DECEPTICON - Fixed Swarm Graph
ROOT CAUSE: Graph had no add_edge() calls connecting agents.
PHANTOM planned but then graph hit END immediately.

FIX: Wire all 5 agents with edges + conditional routing based on findings.
"""

import json
import re
from typing import TypedDict, Annotated, List, Optional, Any
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage


def safe_parse_json(text: str) -> dict:
    """
    Robustly extract JSON from LLM output with markdown fences, comments, or extra text.
    """
    if not text or not isinstance(text, str):
        return {"raw": text, "parse_error": "Empty or non-string input"}

    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.strip("`")

    # Remove single-line comments // ...
    text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)

    # Remove multi-line comments /* ... */
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)

    # Find the first complete JSON object
    start = text.find("{")
    if start == -1:
        return {"raw": text, "parse_error": "No JSON object found (missing '{')"}

    # Walk to find matching closing brace
    depth = 0
    end_index = -1

    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_index = i + 1
                break

    if end_index == -1:
        return {"raw": text, "parse_error": "Incomplete JSON object (missing '}')"}

    json_str = text[start:end_index]

    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        return {"raw": text, "parse_error": f"JSON decode error: {str(e)}"}


# ─────────────────────────────────────────────────────────────
# STATE - carries everything between agents
# ─────────────────────────────────────────────────────────────

class DecepticonState(TypedDict):
    # Raw input and target
    input: str
    target: str

    # Per-agent outputs (structured, not messages)
    phantom_plan: dict
    shadow_recon: dict
    oracle_vulns: List[dict]
    breach_results: dict
    cipher_report: str

    # Shared message bus (only for current agent's LLM turn)
    messages: Annotated[list, add_messages]

    # Control flow and error handling
    error: str
    phase: str

    # Legacy fields (kept for compatibility)
    mission_type: str
    open_ports: List[dict]
    services: List[dict]
    subdomains: List[str]
    web_services: List[dict]
    cves: List[dict]
    exploits: List[dict]
    attack_order: List[str]
    shells: List[dict]
    credentials: List[dict]
    exploitation_success: bool
    final_report: str

    # Tools and LLM (for fallback access)
    llm: Optional[Any]
    recon_tools: List[Any]
    research_tools: List[Any]
    access_tools: List[Any]


# ─────────────────────────────────────────────────────────────
# ROUTING FUNCTIONS
# ─────────────────────────────────────────────────────────────

def route_after_planner(state: DecepticonState) -> str:
    if state.get("error"):
        return "abort"

    mission_type = state.get("mission_type", "FULL_PENTEST")

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
                    return "guardian"
                elif "FULL_PENTEST" in content or "WEB_AUDIT" in content:
                    mission_type = "FULL_PENTEST"
                    break

    return "shadow"


def route_after_recon(state: DecepticonState) -> str:
    mission_type = state.get("mission_type", "FULL_PENTEST")

    for msg in reversed(state.get("messages", [])):
        content = getattr(msg, "content", "")
        if "RECON_ONLY" in content:
            mission_type = "RECON_ONLY"
            break

    if mission_type == "RECON_ONLY":
        return "cipher"

    return "oracle"


def route_after_research(state: DecepticonState) -> str:
    mission_type = state.get("mission_type", "FULL_PENTEST")

    for msg in reversed(state.get("messages", [])):
        content = getattr(msg, "content", "")
        if "VULN_SCAN" in content:
            mission_type = "VULN_SCAN"
            break

    if mission_type == "VULN_SCAN":
        return "cipher"

    cves = state.get("cves", [])
    has_critical = any(
        v.get("severity", "").upper() in ("CRITICAL", "HIGH")
        for v in cves
    )

    if not cves:
        for msg in reversed(state.get("messages", [])):
            content = getattr(msg, "content", "").lower()
            if "critical" in content or "high" in content:
                if "cvss" in content or "exploit" in content or "cve-" in content:
                    has_critical = True
                    break

    if has_critical:
        return "breach"
    return "cipher"


def route_after_exploitation(state: DecepticonState) -> str:
    return "cipher"


# ─────────────────────────────────────────────────────────────
# AGENT NODE WRAPPERS
# ─────────────────────────────────────────────────────────────

def make_agent_node(agent, node_name: str):
    """
    Wraps a LangGraph ReAct agent as a graph node.
    """
    async def node_fn(state: DecepticonState) -> dict:
        print(f"\n{'='*60}")
        print(f" DECEPTICON - {node_name.upper()} EXECUTING")
        print(f"{'='*60}")

        updates = {"phase": node_name}

        if state.get("error"):
            updates["error"] = ""

        try:
            if hasattr(agent, "ainvoke"):
                prompt_messages = _build_isolated_prompt(state, node_name)

                result = await agent.ainvoke({"messages": prompt_messages})

                if isinstance(result, dict):
                    new_messages = result.get("messages", [])
                elif isinstance(result, list):
                    new_messages = result
                else:
                    new_messages = [result] if result else []

                if not new_messages and result:
                    print(f" [DEBUG] Agent {node_name} returned no messages but got result: {type(result)}")

                has_tool_calls = any(hasattr(m, "tool_calls") and m.tool_calls for m in new_messages)
                if not has_tool_calls and node_name in ["shadow", "oracle", "breach"]:
                    print(f" [DEBUG] {node_name.upper()} returned prose, attempting manual tool fallback...")
                    fallback_data = await _force_execution_fallback(state, node_name)
                    if fallback_data:
                        updates.update(fallback_data)
            else:
                new_messages = []
        except Exception as e:
            error_msg = f"Agent {node_name} failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            updates["error"] = error_msg
            new_messages = []

        # DEBUG: Print the last few messages
        for msg in new_messages[-3:]:
            msg_type = msg.__class__.__name__
            content = (msg.content[:100] + "...") if isinstance(msg.content, str) and len(msg.content) > 100 else msg.content
            print(f" [{node_name}] {msg_type}: {content}")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                print(f" [{node_name}] TOOL CALLS: {[tc['name'] for tc in msg.tool_calls]}")

        # Extract structured data
        last_content = ""
        for msg in reversed(new_messages):
            if hasattr(msg, "content") and isinstance(msg.content, str):
                last_content = msg.content
                break

        if node_name == "phantom":
            print(f"[PHANTOM DEBUG] Input: '{state.get('input', 'MISSING')}'")
            print(f"[PHANTOM DEBUG] Target: '{state.get('target', 'MISSING')}'")
            print(f"[PHANTOM DEBUG] Last content: '{last_content[:100] if last_content else 'EMPTY'}'")

        try:
            if node_name == "phantom":
                if not last_content:
                    error_msg = "PHANTOM received empty content - input was lost"
                    print(f"[ERROR] {error_msg}")
                    updates["error"] = error_msg
                    updates["phase"] = "aborted"
                    updates["messages"] = new_messages
                    return updates

                plan_data = _extract_planner_data_safe(last_content, state.get("input", ""))
                updates.update(plan_data)
                if plan_data.get("target"):
                    updates["target"] = plan_data.get("target")
                updates["phantom_plan"] = plan_data

            elif node_name == "shadow":
                recon_data = _extract_recon_data_safe(last_content)
                updates.update(recon_data)
                updates["shadow_recon"] = recon_data

            elif node_name == "oracle":
                vuln_data = _extract_research_data_safe(last_content)
                updates.update(vuln_data)
                updates["oracle_vulns"] = vuln_data.get("cves", [])

            elif node_name == "breach":
                exploit_data = _extract_exploitation_data_safe(last_content)
                updates.update(exploit_data)
                updates["breach_results"] = exploit_data

            elif node_name == "cipher":
                updates["cipher_report"] = last_content
                updates["final_report"] = last_content
                updates["phase"] = "done"
        except Exception as e:
            print(f"[ERROR] Failed to extract structured data from {node_name}: {str(e)}")
            updates["error"] = f"Data extraction failed: {str(e)}"

        updates["messages"] = new_messages

        print(f" {node_name.upper()} complete")
        return updates

    node_fn.__name__ = f"{node_name}_node"
    return node_fn


def _build_isolated_prompt(state: DecepticonState, node_name: str) -> list:
    """Build isolated prompt for each agent to prevent message bleed."""
    messages = []

    if node_name == "phantom":
        input_text = state.get("input")
        if not input_text:
            for msg in state.get("messages", []):
                if isinstance(msg, HumanMessage) and msg.content:
                    input_text = msg.content
                    break
        messages.append(HumanMessage(content=input_text or ""))
    elif node_name == "shadow":
        plan = state.get("phantom_plan", {})
        target = state.get("target", state.get("input", ""))
        prompt = f"Target: {target}\nMission plan: {plan}\nExecute reconnaissance now."
        messages.append(HumanMessage(content=prompt))
    elif node_name == "oracle":
        recon = state.get("shadow_recon", {})
        prompt = f"Reconnaissance results: {recon}\nAnalyze vulnerabilities now."
        messages.append(HumanMessage(content=prompt))
    elif node_name == "breach":
        vulns = state.get("oracle_vulns", [])
        prompt = f"Vulnerabilities found: {vulns}\nAttempt exploitation now."
        messages.append(HumanMessage(content=prompt))
    elif node_name == "cipher":
        plan = state.get("phantom_plan", {})
        recon = state.get("shadow_recon", {})
        vulns = state.get("oracle_vulns", [])
        exploits = state.get("breach_results", {})
        prompt = f"Mission summary:\nPlan: {plan}\nRecon: {recon}\nVulnerabilities: {vulns}\nExploitation: {exploits}\nGenerate final report."
        messages.append(HumanMessage(content=prompt))

    return messages


def unwrap_exception_group(eg, depth=0):
    """Recursively unwrap nested ExceptionGroups to find root causes."""
    prefix = "  " * depth
    for exc in eg.exceptions:
        if type(exc).__name__ == "ExceptionGroup":
            unwrap_exception_group(exc, depth + 1)
        else:
            print(f"{prefix} [MCP ROOT CAUSE] {type(exc).__name__}: {exc}")


def _extract_planner_data_safe(content: str, default_target: str = "") -> dict:
    """Robustly extract mission data from PHANTOM's output with target fallback."""
    updates = {}
    parsed = safe_parse_json(content)

    if "parse_error" in parsed:
        print(f" [DEBUG] PHANTOM JSON parse error: {parsed['parse_error']}")
        updates["mission_type"] = "FULL_PENTEST"
        ip_match = re.search(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', content)
        updates["target"] = ip_match.group(1) if ip_match else default_target
    else:
        updates["mission_type"] = parsed.get("mission_type", "FULL_PENTEST")
        updates["target"] = parsed.get("target") or default_target

    return updates


def _extract_recon_data_safe(content: str) -> dict:
    """Extract recon data using safe JSON parsing."""
    # FIX: was initialising wrong keys and mapping active_recon incorrectly
    updates = {
        "open_ports": [],
        "services": [],
        "subdomains": [],
        "web_services": [],
    }
    parsed = safe_parse_json(content)

    if "parse_error" in parsed:
        print(f"[DEBUG] SHADOW JSON parse error: {parsed['parse_error']}")
        return updates

    active = parsed.get("active_recon", {})
    updates["open_ports"] = active.get("open_ports", [])
    updates["services"] = active.get("open_ports", [])   # same source field
    updates["web_services"] = active.get("web_services", [])

    passive = parsed.get("passive_recon", {})
    updates["subdomains"] = passive.get("subdomains", [])

    return updates


def _extract_research_data_safe(content: str) -> dict:
    """Extract vulnerability data using safe JSON parsing."""
    updates = {"cves": [], "exploits": [], "attack_order": []}
    parsed = safe_parse_json(content)

    if "parse_error" in parsed:
        print(f"[DEBUG] ORACLE JSON parse error: {parsed['parse_error']}")
        return updates

    updates["cves"] = parsed.get("vulnerabilities", [])
    updates["exploits"] = parsed.get("vulnerabilities", [])
    updates["attack_order"] = parsed.get("attack_order", [])

    return updates


def _extract_exploitation_data_safe(content: str) -> dict:
    """Extract exploitation data using safe JSON parsing."""
    # FIX: credentials was referenced before assignment
    updates = {"shells": [], "credentials": [], "exploitation_success": False}
    parsed = safe_parse_json(content)

    if "parse_error" in parsed:
        print(f"[DEBUG] BREACH JSON parse error: {parsed['parse_error']}")
        return updates

    success = parsed.get("successful_exploits", [])
    updates["shells"] = success
    updates["exploitation_success"] = len(success) > 0

    for s in success:
        if s.get("credentials_obtained"):
            updates["credentials"].extend(s["credentials_obtained"])

    return updates


async def _force_execution_fallback(state: DecepticonState, node_name: str) -> dict:
    """Invokes tools directly if the agent's LLM fails to emit tool calls."""
    target = state.get("target", state.get("input", ""))
    if not target:
        return {}

    updates = {}

    try:
        if node_name == "shadow":
            tools = state.get("recon_tools", [])
            for tool in tools:
                if tool.name == "nmap":
                    print(f" [SHADOW FALLBACK] Forcing nmap scan on {target}...")
                    res = await tool.ainvoke({"target_ip": target, "flags": "-sV -T4"})
                    updates.update(_extract_recon_data_safe(str(res)))
                elif tool.name == "subfinder":
                    print(f" [SHADOW FALLBACK] Forcing subdomain search for {target}...")
                    res = await tool.ainvoke({"domain": target})
                    updates.update(_extract_recon_data_safe(str(res)))
    except Exception as e:
        print(f" [WARN] Manual fallback failed for {node_name}: {e}")

    return updates


# ─────────────────────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────────────────────

async def build_decepticon_graph(llm, mcp_config: dict):
    """
    Builds and compiles the full DECEPTICON swarm graph.
    """
    from src.prompts.elite_prompts import (
        PLANNER_SYSTEM_PROMPT,
        RECON_SYSTEM_PROMPT,
        RESEARCHER_SYSTEM_PROMPT,
        ACCESS_SYSTEM_PROMPT,
        SUMMARY_SYSTEM_PROMPT,
    )

    async def get_tools(agent_key: str) -> list:
        agent_data = mcp_config.get(agent_key, {})
        if not agent_data or "note" in agent_data:
            return []

        if isinstance(agent_data, dict) and "servers" in agent_data:
            servers = agent_data["servers"]
        else:
            servers = agent_data

        actual_servers = {
            s_name: s_config for s_name, s_config in servers.items()
            if isinstance(s_config, dict) and s_name != "model"
        }

        if not actual_servers:
            return []

        all_tools = []
        for s_name, s_config in actual_servers.items():
            try:
                print(f" [MCP] Connecting to {s_name}...")
                client = MultiServerMCPClient({s_name: s_config})
                tools = await client.get_tools()
                all_tools.extend(tools)
                print(f" [MCP] Success: Loaded {len(tools)} tools from {s_name}")
            except Exception as e:
                if type(e).__name__ == "ExceptionGroup":
                    print(f" [MCP] {s_name} failed (ExceptionGroup):")
                    unwrap_exception_group(e)
                else:
                    print(f" [WARN] Could not load MCP tools for server '{s_name}' in {agent_key}: {e}")

        return all_tools

    nmap_tools = await get_tools("reconnaissance")
    nuclei_tools = await get_tools("researcher")
    access_tools = await get_tools("initial_access")

    print(f" [DEBUG] Loaded tools: nmap={len(nmap_tools)}, nuclei={len(nuclei_tools)}, access={len(access_tools)}")

    # Create agents
    phantom = create_react_agent(llm, tools=[], prompt=PLANNER_SYSTEM_PROMPT)
    shadow = create_react_agent(llm, tools=nmap_tools, prompt=RECON_SYSTEM_PROMPT)
    oracle = create_react_agent(llm, tools=nuclei_tools, prompt=RESEARCHER_SYSTEM_PROMPT)
    breach = create_react_agent(llm, tools=access_tools, prompt=ACCESS_SYSTEM_PROMPT)
    cipher = create_react_agent(llm, tools=[], prompt=SUMMARY_SYSTEM_PROMPT)

    # Build graph
    graph = StateGraph(DecepticonState)

    graph.add_node("phantom", make_agent_node(phantom, "phantom"))
    graph.add_node("shadow", make_agent_node(shadow, "shadow"))
    graph.add_node("oracle", make_agent_node(oracle, "oracle"))
    graph.add_node("breach", make_agent_node(breach, "breach"))
    graph.add_node("cipher", make_agent_node(cipher, "cipher"))

    def abort_node(state: DecepticonState) -> dict:
        error = state.get("error", "Unknown error")
        print(f"\n{'='*60}")
        print(f" MISSION ABORTED: {error}")
        print(f"{'='*60}")
        return {"phase": "aborted", "error": error}

    graph.add_node("abort", abort_node)

    # Wire edges
    graph.set_entry_point("phantom")

    graph.add_conditional_edges(
        "phantom",
        route_after_planner,
        {
            "shadow": "shadow",
            "guardian": "shadow",
            "abort": "abort",
        }
    )

    graph.add_conditional_edges(
        "shadow",
        route_after_recon,
        {
            "oracle": "oracle",
            "cipher": "cipher",
        }
    )

    graph.add_conditional_edges(
        "oracle",
        route_after_research,
        {
            "breach": "breach",
            "cipher": "cipher",
        }
    )

    graph.add_edge("breach", "cipher")
    graph.add_edge("cipher", END)
    graph.add_edge("abort", END)

    return graph.compile()


async def build_decepticon_graph_no_mcp(llm):
    """Same graph but with NO MCP tools - for testing."""
    from src.prompts.elite_prompts import (
        PLANNER_SYSTEM_PROMPT,
        RECON_SYSTEM_PROMPT,
        RESEARCHER_SYSTEM_PROMPT,
        ACCESS_SYSTEM_PROMPT,
        SUMMARY_SYSTEM_PROMPT,
    )

    phantom = create_react_agent(llm, tools=[], prompt=PLANNER_SYSTEM_PROMPT)
    shadow = create_react_agent(llm, tools=[], prompt=RECON_SYSTEM_PROMPT)
    oracle = create_react_agent(llm, tools=[], prompt=RESEARCHER_SYSTEM_PROMPT)
    breach = create_react_agent(llm, tools=[], prompt=ACCESS_SYSTEM_PROMPT)
    cipher = create_react_agent(llm, tools=[], prompt=SUMMARY_SYSTEM_PROMPT)

    graph = StateGraph(DecepticonState)
    graph.add_node("phantom", make_agent_node(phantom, "phantom"))
    graph.add_node("shadow", make_agent_node(shadow, "shadow"))
    graph.add_node("oracle", make_agent_node(oracle, "oracle"))
    graph.add_node("breach", make_agent_node(breach, "breach"))
    graph.add_node("cipher", make_agent_node(cipher, "cipher"))

    def abort_node(state: DecepticonState) -> dict:
        error = state.get("error", "Unknown error")
        print(f"\n{'='*60}")
        print(f" MISSION ABORTED: {error}")
        print(f"{'='*60}")
        return {"phase": "aborted", "error": error}

    graph.add_node("abort", abort_node)

    graph.set_entry_point("phantom")
    graph.add_conditional_edges(
        "phantom", route_after_planner,
        {"shadow": "shadow", "guardian": "shadow", "abort": "abort"}
    )
    graph.add_conditional_edges(
        "shadow", route_after_recon,
        {"oracle": "oracle", "cipher": "cipher"}
    )
    graph.add_conditional_edges(
        "oracle", route_after_research,
        {"breach": "breach", "cipher": "cipher"}
    )
    graph.add_edge("breach", "cipher")
    graph.add_edge("cipher", END)
    graph.add_edge("abort", END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────
# INITIAL STATE HELPER
# ─────────────────────────────────────────────────────────────

def make_initial_state(
    user_input: str,
    llm=None,
    recon_tools=None,
    research_tools=None,
    access_tools=None,
) -> dict:
    """Initialize the graph state dictionary with correct structure and tools."""
    # Pre-extract target so PHANTOM has a fallback
    target = ""
    ip_match = re.search(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b', user_input)
    if ip_match:
        target = ip_match.group(1)
    else:
        domain_match = re.search(r'\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', user_input)
        if domain_match:
            target = domain_match.group(1)

    # FIX: removed duplicate "messages" key - was defined twice, second one (empty list)
    # silently overwrote the first (HumanMessage), causing PHANTOM to get empty input.
    return {
        "messages": [HumanMessage(content=user_input)],   # single definition
        "input": user_input,
        "target": target,
        "phantom_plan": {},
        "shadow_recon": {},
        "oracle_vulns": [],
        "breach_results": {},
        "cipher_report": "",
        "llm": llm,
        "recon_tools": recon_tools or [],
        "research_tools": research_tools or [],
        "access_tools": access_tools or [],
        "error": "",
        "phase": "planning",
        "mission_type": "FULL_PENTEST",
        "open_ports": [],
        "services": [],
        "subdomains": [],
        "web_services": [],
        "cves": [],
        "exploits": [],
        "attack_order": [],
        "shells": [],
        "credentials": [],
        "exploitation_success": False,
        "final_report": "",
    }


# ─────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────

async def run_mission(user_input: str, llm, tools: dict = None):
    """Entry point for CLI to run the swarm."""
    from src.utils.mcp.config_loader import load_mcp_config

    mcp_config = load_mcp_config()

    graph, tools_dict = await build_decepticon_graph_with_tools(llm, mcp_config)

    if tools:
        for k, v in tools.items():
            if k in tools_dict:
                tools_dict[k].extend(v)
            else:
                tools_dict[k] = v

    initial_state = make_initial_state(
        user_input,
        llm=llm,
        recon_tools=tools_dict.get("recon", []),
        research_tools=tools_dict.get("research", []),
        access_tools=tools_dict.get("access", []),
    )

    print("\n DECEPTICON MISSION STARTING")
    print(f"Input: {user_input[:50]}...")
    print("Flow: PHANTOM -> SHADOW -> ORACLE -> BREACH -> CIPHER\n")

    result = await graph.ainvoke(initial_state)
    return result


async def build_decepticon_graph_with_tools(llm, mcp_config: dict):
    """Special version of builder that also returns the tool lists."""
    graph = await build_decepticon_graph(llm, mcp_config)

    async def get_tools_simple(agent_key: str) -> list:
        agent_data = mcp_config.get(agent_key, {})
        if not agent_data or "note" in agent_data:
            return []

        if isinstance(agent_data, dict) and "servers" in agent_data:
            servers = agent_data["servers"]
        else:
            servers = agent_data

        actual_servers = {
            s_name: s_config for s_name, s_config in servers.items()
            if isinstance(s_config, dict) and s_name != "model"
        }
        if not actual_servers:
            return []

        all_tools = []
        for s_name, s_config in actual_servers.items():
            try:
                client = MultiServerMCPClient({s_name: s_config})
                tools = await client.get_tools()
                all_tools.extend(tools)
            except Exception as e:
                if type(e).__name__ == "ExceptionGroup":
                    print(f" [MCP] {s_name} sub-error (ExceptionGroup):")
                    unwrap_exception_group(e)
                continue
        return all_tools

    recon = await get_tools_simple("reconnaissance")
    research = await get_tools_simple("researcher")
    access = await get_tools_simple("initial_access")

    return graph, {"recon": recon, "research": research, "access": access}
