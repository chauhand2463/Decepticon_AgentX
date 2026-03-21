import json
import os
from langchain_mcp_adapters.client import MultiServerMCPClient


async def load_mcp_tools(agent_name=None):

    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    config_path = os.path.join(base_dir, "mcp_config.json")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        return []

    if agent_name:
        selected_agents = {
            agent: config[agent] for agent in agent_name if agent in config
        }
    else:
        selected_agents = {
            k: v for k, v in config.items() if k != "models" and isinstance(v, dict)
        }

    tools = []

    for agent_label, servers in selected_agents.items():
        if not isinstance(servers, dict):
            continue

        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict):
                continue

            if "transport" not in server_config:
                server_config["transport"] = (
                    "streamable_http" if "url" in server_config else "stdio"
                )

            # Resolve relative paths in args to absolute paths
            if "args" in server_config:
                new_args = []
                for arg in server_config["args"]:
                    if isinstance(arg, str) and not os.path.isabs(arg):
                        # Try to resolve relative to base_dir
                        abs_path = os.path.normpath(os.path.join(base_dir, arg))
                        if os.path.exists(abs_path):
                            new_args.append(abs_path)
                        else:
                            # Fallback to the original arg if file not found locally
                            new_args.append(arg)
                    else:
                        new_args.append(arg)
                server_config["args"] = new_args

            client = MultiServerMCPClient({server_name: server_config})
            try:
                # Add a small timeout or error handling for server initialization
                current_tools = await client.get_tools() if client else []
            except Exception as e:
                print(
                    f"Warning: Failed to load tools from MCP server '{server_name}': {e}"
                )
                # Log more detail if possible
                if "No such file or directory" in str(e):
                    print(
                        f"  Check if the server script exists: {server_config.get('args', [])}"
                    )
                current_tools = []

            if current_tools:
                tools.extend(current_tools)

    return tools if tools else []
