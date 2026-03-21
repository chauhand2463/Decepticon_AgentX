import streamlit as st
from typing import Dict, Any, Optional
from frontend.web.utils.constants import (
    SESSION_KEY_CURRENT_MODEL,
    SESSION_KEY_EXECUTOR_READY,
    PROVIDERS,
)


def check_model_required() -> bool:

    return bool(st.session_state.get(SESSION_KEY_CURRENT_MODEL))


def validate_session_state() -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

    required_keys = [SESSION_KEY_EXECUTOR_READY, SESSION_KEY_CURRENT_MODEL]

    for key in required_keys:
        if key not in st.session_state:
            validation_result["errors"].append(f"Missing session state: {key}")
            validation_result["valid"] = False

    if not st.session_state.get(SESSION_KEY_EXECUTOR_READY, False):
        validation_result["warnings"].append("Executor not ready")

    return validation_result


def validate_user_input(user_input: str) -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"valid": True, "errors": [], "cleaned_input": ""}

    if not user_input:
        validation_result["errors"].append("Empty input")
        validation_result["valid"] = False
        return validation_result

    cleaned = user_input.strip()

    if not cleaned:
        validation_result["errors"].append("Input contains only whitespace")
        validation_result["valid"] = False
        return validation_result

    if len(cleaned) > 5000:
        validation_result["errors"].append("Input too long (max 5000 characters)")
        validation_result["valid"] = False
        return validation_result

    validation_result["cleaned_input"] = cleaned
    return validation_result


def validate_model_info(model_info: Dict[str, Any]) -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"valid": True, "errors": []}

    if not isinstance(model_info, dict):
        validation_result["errors"].append("Model info must be a dictionary")
        validation_result["valid"] = False
        return validation_result

    required_fields = ["model_name", "provider", "display_name"]

    for field in required_fields:
        if field not in model_info:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False
        elif not model_info[field]:
            validation_result["errors"].append(f"Empty required field: {field}")
            validation_result["valid"] = False

    if "provider" in model_info:
        provider = model_info["provider"]

        provider_found = any(provider.lower() == p.lower() for p in PROVIDERS)
        if not provider_found:
            validation_result["errors"].append(f"Unknown provider: {provider}")
            validation_result["valid"] = False

    return validation_result


def validate_message_format(message: Dict[str, Any]) -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"valid": True, "errors": []}

    if not isinstance(message, dict):
        validation_result["errors"].append("Message must be a dictionary")
        validation_result["valid"] = False
        return validation_result

    required_fields = ["type", "content", "id"]

    for field in required_fields:
        if field not in message:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False

    valid_types = ["user", "ai", "tool"]
    if "type" in message and message["type"] not in valid_types:
        validation_result["errors"].append(f"Invalid message type: {message['type']}")
        validation_result["valid"] = False

    return validation_result


def validate_terminal_entry(entry: Dict[str, Any]) -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"valid": True, "errors": []}

    if not isinstance(entry, dict):
        validation_result["errors"].append("Terminal entry must be a dictionary")
        validation_result["valid"] = False
        return validation_result

    required_fields = ["type", "content", "timestamp"]

    for field in required_fields:
        if field not in entry:
            validation_result["errors"].append(f"Missing required field: {field}")
            validation_result["valid"] = False

    valid_types = ["command", "output"]
    if "type" in entry and entry["type"] not in valid_types:
        validation_result["errors"].append(
            f"Invalid terminal entry type: {entry['type']}"
        )
        validation_result["valid"] = False

    return validation_result


def validate_file_path(
    file_path: str, required_extension: Optional[str] = None
) -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"valid": True, "errors": []}

    if not file_path:
        validation_result["errors"].append("Empty file path")
        validation_result["valid"] = False
        return validation_result

    if required_extension:
        if not file_path.endswith(required_extension):
            validation_result["errors"].append(
                f"File must have {required_extension} extension"
            )
            validation_result["valid"] = False

    if ".." in file_path:
        validation_result["errors"].append("Path traversal detected")
        validation_result["valid"] = False

    return validation_result


def is_safe_html_content(content: str) -> bool:

    dangerous_tags = ["<script", "<iframe", "<object", "<embed", "<link", "<meta"]

    content_lower = content.lower()

    for tag in dangerous_tags:
        if tag in content_lower:
            return False

    return True


def validate_workflow_execution_state() -> Dict[str, Any]:

    validation_result: Dict[str, Any] = {"can_execute": True, "errors": []}

    if not st.session_state.get(SESSION_KEY_EXECUTOR_READY, False):
        validation_result["errors"].append("Executor not ready")
        validation_result["can_execute"] = False

    if st.session_state.get("workflow_running", False):
        validation_result["errors"].append("Another workflow is already running")
        validation_result["can_execute"] = False

    if not st.session_state.get(SESSION_KEY_CURRENT_MODEL):
        validation_result["errors"].append("No model selected")
        validation_result["can_execute"] = False

    return validation_result
