from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from rich import markup
from typing import Dict, Any, List, Optional


def parse_tool_name(tool_name: str) -> str:

    if tool_name.startswith("transfer_to_"):
        target_agent = tool_name.replace("transfer_to_", "").replace("_", " ").title()
        return f"Transfer to {target_agent}"

    return tool_name.replace("_", " ").title()


def parse_tool_call(tool_call_data: dict) -> str:

    try:
        tool_name = tool_call_data.get("name", "Unknown Tool")
        tool_args = tool_call_data.get("args", {})

        if tool_name.startswith("transfer_to_"):
            target_agent = (
                tool_name.replace("transfer_to_", "").replace("_", " ").title()
            )
            return f"Transfer to {target_agent}..."

        if tool_args:
            command_parts = [tool_name]

            param_order = ["options", "target"]

            for param in param_order:
                if param in tool_args and tool_args[param]:
                    if isinstance(tool_args[param], list):
                        value = " ".join(str(opt) for opt in tool_args[param] if opt)
                    else:
                        value = str(tool_args[param]).strip()

                    if value:
                        command_parts.append(value)

            for key, value in tool_args.items():
                if key not in param_order and value:
                    if isinstance(value, list):
                        formatted_value = " ".join(str(opt) for opt in value if opt)
                    else:
                        formatted_value = str(value).strip()

                    if formatted_value:
                        command_parts.append(formatted_value)

            if len(command_parts) > 1:
                return " ".join(command_parts)
            else:
                return f"{tool_name}..."
        else:
            return f"{tool_name}..."

    except Exception as e:
        return f"Tool call... (parsing error: {str(e)})"


def get_tool_call_status_message(tool_call_data: dict) -> str:

    try:
        tool_name = tool_call_data.get("name", "Unknown Tool")

        if tool_name.startswith("transfer_to_"):
            target_agent = (
                tool_name.replace("transfer_to_", "").replace("_", " ").title()
            )
            return f"Transferring to {target_agent}..."
        else:
            display_name = parse_tool_name(tool_name)
            return f"Executing {display_name}..."
    except Exception:
        return "Processing..."


def get_agent_name(namespace):

    if not namespace:
        return "Unknown"

    if len(namespace) > 0:
        namespace_str = namespace[0]
        if ":" in namespace_str:
            return namespace_str.split(":")[0]

    return "Unknown"


def get_message_type(message):

    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "ai"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        return None


def extract_message_content(message, escape_markup=True):

    try:
        if hasattr(message, "content"):
            content = message.content
        else:
            content = str(message)

        if isinstance(content, str):
            result = content.strip() if content else ""
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and "text" in item:
                        text_parts.append(item["text"])
                    elif "text" in item:
                        text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
            result = "\n".join(text_parts) if text_parts else str(content)
        else:
            result = str(content)

        if escape_markup:
            result = markup.escape(result)

        return result
    except Exception as e:
        error_msg = f"Content extraction error: {str(e)}\n{str(message)}"

        if escape_markup:
            error_msg = markup.escape(error_msg)
        return error_msg


def extract_tool_calls(
    message, event_data: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:

    tool_calls = []

    if message and hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:
            tool_calls.append(
                {
                    "id": tool_call.get("id", ""),
                    "name": tool_call.get("name", "Unknown Tool"),
                    "args": tool_call.get("args", {}),
                }
            )

    return tool_calls
