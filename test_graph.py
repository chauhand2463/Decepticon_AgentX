"""
Run this to test the fixed graph works end-to-end.
Save as: test_graph.py
Run:     python test_graph.py
"""
import asyncio
from langchain_anthropic import ChatAnthropic
from src.swarm.graph_fixed import run_mission

async def main():
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

    # Test 1: VULN_SCAN (no exploitation)
    print("\n=== TEST 1: VULN_SCAN ===")
    result = await run_mission(
        "Scan 192.168.1.1 for vulnerabilities — VULN_SCAN only, no exploitation",
        llm,
        mcp_config=None   # no MCP tools in test
    )
    # Should show: PHANTOM  SHADOW  ORACLE  CIPHER (skips BREACH)
    print(f"Phase: {result.get('phase')} | CVEs: {len(result.get('cves', []))}")

    # Test 2: FULL_PENTEST
    print("\n=== TEST 2: FULL_PENTEST ===")
    result = await run_mission(
        "Full pentest on 10.10.10.5 — exploit everything you find",
        llm,
        mcp_config=None
    )
    # Should show: PHANTOM  SHADOW  ORACLE  BREACH  CIPHER
    print(f"Phase: {result.get('phase')} | Exploited: {result.get('exploitation_success')}")

asyncio.run(main())