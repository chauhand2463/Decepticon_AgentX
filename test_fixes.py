#!/usr/bin/env python3
"""
Test script to verify the graph_fixed.py fixes work correctly.
This script tests the core functionality without requiring full MCP setup.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.swarm.graph_fixed import build_decepticon_graph_no_mcp, make_initial_state
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Try to load .env if it exists
load_dotenv()


async def test_basic_functionality():
    """Test basic graph functionality without MCP tools."""
    print("🧪 Testing DECEPTICON graph fixes...")
    print("=" * 60)

    try:
        # Test with a simple mock LLM (this will use the actual LLM if available)
        # For testing purposes, we'll use a simple model
        llm = ChatAnthropic(model="claude-3-haiku-20240307")

        print("✅ LLM initialized successfully")

        # Build the graph without MCP
        print("🏗️  Building graph without MCP...")
        graph = await build_decepticon_graph_no_mcp(llm)
        print("✅ Graph built successfully")

        # Test with a simple input
        test_input = "Scan 192.168.1.1 for vulnerabilities"
        state = make_initial_state(test_input)

        print(f"📝 Test input: {test_input}")
        print("🚀 Running mission...")

        # Run the mission
        result = await graph.ainvoke(state)

        print("✅ Mission completed successfully!")
        print("=" * 60)
        print("📊 Results:")
        print(f"   Phase: {result.get('phase', 'unknown')}")
        print(f"   Target: {result.get('target', 'unknown')}")
        print(f"   Mission Type: {result.get('mission_type', 'unknown')}")
        print(f"   Open Ports: {len(result.get('open_ports', []))}")
        print(f"   CVEs Found: {len(result.get('cves', []))}")
        print(f"   Exploitation Success: {result.get('exploitation_success', False)}")
        print(
            f"   Final Report Length: {len(result.get('final_report', ''))} characters"
        )

        # Check if we got expected results
        success_indicators = [
            result.get("phase") == "done",
            len(result.get("final_report", "")) > 0,
            result.get("mission_type") in ["FULL_PENTEST", "RECON_ONLY", "VULN_SCAN"],
        ]

        if all(success_indicators):
            print("\n🎉 All tests passed! The graph fixes are working correctly.")
            return True
        else:
            print(f"\n⚠️  Some tests failed. Success indicators: {success_indicators}")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_error_handling():
    """Test that error handling works correctly."""
    print("\n" + "=" * 60)
    print("🧪 Testing error handling...")

    try:
        # Test with potentially problematic input
        problematic_input = (
            "This is an invalid request with no target or clear objective"
        )
        state = make_initial_state(problematic_input)

        llm = ChatAnthropic(model="claude-3-haiku-20240307")
        graph = await build_decepticon_graph_no_mcp(llm)

        result = await graph.ainvoke(state)

        # Should still complete without crashing
        if result.get("phase") == "done":
            print(
                "✅ Error handling test passed - graph completed despite problematic input"
            )
            return True
        else:
            print("❌ Error handling test failed - graph did not complete")
            return False

    except Exception as e:
        print(f"❌ Error handling test failed with exception: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("DECEPTICON Graph Fixes Test Suite")
    print("=" * 60)
    print(f"Calendar: {datetime.now().strftime('%Y-%m%d %H:%M:%S')}")
    print()

    # Check if API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not found in environment.")
        print("📝 Testing with limited functionality (some tests may be skipped)")

    # Run tests
    test1_result = await test_basic_functionality()
    test2_result = await test_error_handling()

    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"   Basic Functionality: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Error Handling: {'✅ PASS' if test2_result else '❌ FAIL'}")

    if test1_result and test2_result:
        print("\n🎉 All tests passed! The graph fixes appear to be working correctly.")
        print("💡 The CLI should now work better with improved error handling.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user.")
    except Exception as e:
        print(f"\n💥 Fatal error during testing: {str(e)}")
