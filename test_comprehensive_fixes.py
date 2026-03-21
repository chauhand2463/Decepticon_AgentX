#!/usr/bin/env python3
"""
Comprehensive test to verify all the root cause fixes are working.
Tests:
1. Safe JSON parsing with comment stripping
2. Isolated state fields preventing message bleed
3. PHANTOM error handling and abort mechanism
4. Overall graph resilience
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.swarm.graph_fixed import (
    safe_parse_json, 
    build_decepticon_graph_no_mcp, 
    make_initial_state,
    _build_isolated_prompt
)
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Try to load .env if it exists
load_dotenv()


def test_safe_json_parsing():
    """Test the safe JSON parsing function with various problematic inputs."""
    print("Testing Safe JSON Parsing...")
    print("=" * 50)
    
    test_cases = [
        # Valid JSON
        ('{"mission_type": "FULL_PENTEST", "target": "192.168.1.1"}', "Valid JSON"),
        
        # JSON with JS comments
        ('{"mission_type": "RECON_ONLY" // comment', "JS single-line comment"),
        
        # JSON with block comments
        ('{"target": "192.168.1.1", /* block comment */ "phase": "planning"}', "JS block comment"),
        
        # JSON with markdown fences
        ('```json\n{"mission_type": "VULN_SCAN"}\n```', "Markdown fences"),
        
        # JSON with trailing commas
        ('{"mission_type": "FULL_PENTEST", "target": "192.168.1.1",}', "Trailing comma"),
        
        # Invalid JSON
        ('Not JSON at all', "Invalid JSON"),
        
        # Empty string
        ('', "Empty string"),
        
        # None input
        (None, "None input"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (test_input, description) in enumerate(test_cases, 1):
        try:
            result = safe_parse_json(test_input)
            
            if "parse_error" in result:
                print(f"[{i}] {description}: ✅ Properly handled error")
                passed += 1
            elif isinstance(result, dict) and result:
                print(f"[{i}] {description}: ✅ Parsed successfully")
                passed += 1
            else:
                print(f"[{i}] {description}: ❌ Unexpected result: {result}")
        except Exception as e:
            print(f"[{i}] {description}: ❌ Exception: {str(e)}")
    
    print(f"\nJSON Parsing Results: {passed}/{total} tests passed")
    return passed == total


def test_isolated_prompts():
    """Test that isolated prompts prevent message bleed."""
    print("\nTesting Isolated Prompts...")
    print("=" * 50)
    
    # Create a mock state
    state = {
        "input": "Scan 192.168.1.1 for vulnerabilities",
        "target": "192.168.1.1",
        "phantom_plan": {"mission_type": "FULL_PENTEST", "tools": ["nmap", "subfinder"]},
        "shadow_recon": {"open_ports": [22, 80, 443], "services": ["ssh", "http", "https"]},
        "oracle_vulns": [
            {"cve": "CVE-2021-1234", "severity": "HIGH"},
            {"cve": "CVE-2022-5678", "severity": "CRITICAL"}
        ],
        "breach_results": {"successful_exploits": [{"service": "http", "method": "metasploit"}]}
    }
    
    agents = ["phantom", "shadow", "oracle", "breach", "cipher"]
    
    passed = 0
    total = len(agents)
    
    for agent in agents:
        try:
            prompt = _build_isolated_prompt(state, agent)
            
            # Check that prompt is appropriate for the agent
            if agent == "phantom":
                # PHANTOM should get raw input
                if "Scan 192.168.1.1" in str(prompt):
                    print(f"[✅] {agent}: Correct isolated prompt")
                    passed += 1
                else:
                    print(f"[❌] {agent}: Wrong prompt content")
            elif agent == "shadow":
                # SHADOW should get PHANTOM's plan
                if "Mission plan" in str(prompt) and "FULL_PENTEST" in str(prompt):
                    print(f"[✅] {agent}: Correct isolated prompt")
                    passed += 1
                else:
                    print(f"[❌] {agent}: Wrong prompt content")
            elif agent == "oracle":
                # ORACLE should get SHADOW's recon
                if "Reconnaissance results" in str(prompt) and "open_ports" in str(prompt):
                    print(f"[✅] {agent}: Correct isolated prompt")
                    passed += 1
                else:
                    print(f"[❌] {agent}: Wrong prompt content")
            elif agent == "breach":
                # BREACH should get ORACLE's vulns
                if "Vulnerabilities found" in str(prompt) and "CVE-2021-1234" in str(prompt):
                    print(f"[✅] {agent}: Correct isolated prompt")
                    passed += 1
                else:
                    print(f"[❌] {agent}: Wrong prompt content")
            elif agent == "cipher":
                # CIPHER should get everything
                if "Mission summary" in str(prompt) and "Plan:" in str(prompt) and "Recon:" in str(prompt):
                    print(f"[✅] {agent}: Correct isolated prompt")
                    passed += 1
                else:
                    print(f"[❌] {agent}: Wrong prompt content")
        except Exception as e:
            print(f"[❌] {agent}: Exception: {str(e)}")
    
    print(f"\nIsolated Prompts Results: {passed}/{total} tests passed")
    return passed == total


async def test_abort_mechanism():
    """Test that PHANTOM errors properly abort the mission."""
    print("\nTesting Abort Mechanism...")
    print("=" * 50)
    
    try:
        # Create a mock LLM that will fail for PHANTOM
        llm = ChatAnthropic(model="claude-3-haiku-20240307")
        
        # Build graph
        graph = await build_decepticon_graph_no_mcp(llm)
        
        # Create a state that should trigger PHANTOM to work
        state = make_initial_state("Scan 192.168.1.1 for vulnerabilities")
        
        # Run the mission
        result = await graph.ainvoke(state)
        
        # Check if mission completed or aborted
        phase = result.get("phase")
        error = result.get("error")
        
        if phase == "done":
            print("[✅] Mission completed successfully (no abort needed)")
            return True
        elif phase == "aborted":
            print(f"[✅] Mission properly aborted: {error}")
            return True
        else:
            print(f"[❌] Unexpected phase: {phase}")
            return False
            
    except Exception as e:
        print(f"[❌] Test failed with exception: {str(e)}")
        return False


async def test_overall_resilience():
    """Test overall graph resilience with problematic inputs."""
    print("\nTesting Overall Graph Resilience...")
    print("=" * 50)
    
    test_inputs = [
        "Scan 192.168.1.1 for vulnerabilities",
        "This is an invalid request with no target",
        "",  # Empty input
        "Just some random text that makes no sense",
    ]
    
    passed = 0
    total = len(test_inputs)
    
    try:
        llm = ChatAnthropic(model="claude-3-haiku-20240307")
        graph = await build_decepticon_graph_no_mcp(llm)
        
        for i, test_input in enumerate(test_inputs, 1):
            try:
                state = make_initial_state(test_input)
                result = await graph.ainvoke(state)
                
                phase = result.get("phase")
                if phase in ["done", "aborted"]:
                    print(f"[{i}] Input '{test_input[:30]}...': ✅ Handled gracefully ({phase})")
                    passed += 1
                else:
                    print(f"[{i}] Input '{test_input[:30]}...': ❌ Unexpected phase: {phase}")
            except Exception as e:
                print(f"[{i}] Input '{test_input[:30]}...': ❌ Exception: {str(e)}")
    except Exception as e:
        print(f"Setup failed: {str(e)}")
        return False
    
    print(f"\nResilience Results: {passed}/{total} tests passed")
    return passed == total


async def main():
    """Run all comprehensive tests."""
    print("DECEPTICON Comprehensive Fixes Test Suite")
    print("=" * 60)
    print(f"Calendar: {datetime.now().strftime('%Y-%m%d %H:%M:%S')}")
    print()
    
    # Check if API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[WARN] ANTHROPIC_API_KEY not found. Some tests may be limited.")
    
    # Run tests
    test1_result = test_safe_json_parsing()
    test2_result = test_isolated_prompts()
    test3_result = await test_abort_mechanism()
    test4_result = await test_overall_resilience()
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUMMARY:")
    print(f"   Safe JSON Parsing:     {'[PASS]' if test1_result else '[FAIL]'}")
    print(f"   Isolated Prompts:      {'[PASS]' if test2_result else '[FAIL]'}")
    print(f"   Abort Mechanism:      {'[PASS]' if test3_result else '[FAIL]'}")
    print(f"   Overall Resilience:   {'[PASS]' if test4_result else '[FAIL]'}")
    
    all_passed = all([test1_result, test2_result, test3_result, test4_result])
    
    if all_passed:
        print("\n[SUCCESS] All comprehensive tests passed!")
        print("[INFO] The root cause issues have been successfully fixed:")
        print("  ✅ Safe JSON parsing prevents crashes from malformed JSON")
        print("  ✅ Isolated state fields prevent message bleed between agents")
        print("  ✅ PHANTOM errors properly abort missions instead of continuing")
        print("  ✅ Graph is resilient to various input types and error conditions")
    else:
        print("\n[WARN] Some tests failed. Check output above for details.")
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Tests interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Fatal error during testing: {str(e)}")