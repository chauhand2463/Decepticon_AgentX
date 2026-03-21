"""
DECEPTICON — Swarm Graph Builder
Uses the fixed StateGraph from graph_fixed.py with proper edge wiring.
Agents execute in sequence: PHANTOM -> SHADOW -> ORACLE -> BREACH -> CIPHER
"""

import json
import os
import logging

from src.swarm.graph_fixed import (
    build_decepticon_graph,
    build_decepticon_graph_no_mcp,
    make_initial_state,  # FIX: was not exported but needed by executor.py
)
from src.utils.llm.config_manager import get_current_llm
from src.utils.memory import get_checkpointer, get_store

logger = logging.getLogger(__name__)

checkpointer = get_checkpointer()
store = get_store()


def _load_mcp_config() -> dict:
    """Load and return the full mcp_config.json dict."""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(base_dir, "mcp_config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("mcp_config.json not found at %s", config_path)
        return {}


async def create_dynamic_swarm():
    """
    Build the full 5-agent DECEPTICON graph with MCP tool integration.
    Flow: PHANTOM -> SHADOW -> ORACLE -> BREACH -> CIPHER
    """
    logger.info("Creating dynamic swarm with fixed StateGraph")

    llm = get_current_llm()
    mcp_config = _load_mcp_config()

    if mcp_config:
        graph = await build_decepticon_graph(llm, mcp_config)
    else:
        graph = await build_decepticon_graph_no_mcp(llm)

    logger.info("Swarm graph compiled — agents wired with conditional edges")
    return graph


async def create_fixed_swarm(llm=None):
    """Create the swarm graph without MCP tools (for testing)."""
    if llm is None:
        llm = get_current_llm()
    logger.info("Creating fixed swarm graph (no MCP)")
    graph = await build_decepticon_graph_no_mcp(llm)
    logger.info("Fixed swarm graph created")
    return graph


# Re-export make_initial_state so callers can do:
#   from src.graphs.swarm import make_initial_state
__all__ = [
    "create_dynamic_swarm",
    "create_fixed_swarm",
    "make_initial_state",
]
