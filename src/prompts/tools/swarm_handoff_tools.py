SWARM_HANDOFF_TOOLS_PROMPT = """
HANDOFF PROTOCOL:
You have access to a 'transfer_back_to_supervisor' tool. 
If your specific task is complete, or if you encounter a blocker outside your persona's capabilities, you MUST invoke this tool immediately to return control to the Overlord.
"""