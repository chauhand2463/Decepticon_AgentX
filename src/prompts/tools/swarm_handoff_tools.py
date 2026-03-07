SWARM_HANDOFF_TOOLS_PROMPT = """
HANDOFF PROTOCOL:
If your specific task is complete, or if you encounter a blocker outside your persona's capabilities, you MUST invoke the appropriate transfer tool (e.g., 'transfer_to_planner') to hand off the operation.
Do NOT attempt to call tools that are not in your allowed list.
"""