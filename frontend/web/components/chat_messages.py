import streamlit as st
import re
import time
from typing import Dict, Any, List
from frontend.web.utils.constants import CSS_PATH_CHAT_UI, CSS_PATH_AGENT_STATUS
from src.utils.agents import AgentManager


class ChatMessagesComponent:
    def __init__(self):

        self._setup_styles()

        if "message_counter" not in st.session_state:
            st.session_state.message_counter = 0

    def _setup_styles(self):

        try:
            with open(CSS_PATH_CHAT_UI, "r", encoding="utf-8") as f:
                chat_css = f.read()
            st.html(f"<style>{chat_css}</style>")

            with open(CSS_PATH_AGENT_STATUS, "r", encoding="utf-8") as f:
                agent_status_css = f.read()
            st.html(f"<style>{agent_status_css}</style>")

        except Exception as e:
            print(f"Error loading CSS: {e}")

    def simulate_typing(self, text: str, placeholder, speed: float = 0.005):

        code_blocks = []
        code_block_pattern = r"```.*?```"
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            code_blocks.append((match.start(), match.end()))

        result = ""
        i = 0
        chars_per_update = 5

        while i < len(text):
            code_block_to_add = None

            for start, end in code_blocks:
                if i == start:
                    code_block_to_add = text[start:end]
                    break
                elif start < i < end:
                    i += 1
                    continue

            if code_block_to_add:
                result += code_block_to_add
                i = end
                placeholder.markdown(result)
                time.sleep(speed * 2)
            else:
                end_pos = min(i + chars_per_update, len(text))

                for block_start, _ in code_blocks:
                    if block_start > i:
                        end_pos = min(end_pos, block_start)
                        break

                result += text[i:end_pos]
                i = end_pos

                placeholder.markdown(result)
                time.sleep(speed)

    def display_messages(
        self, structured_messages: List[Dict[str, Any]], container=None
    ):

        if container is None:
            container = st

        for message in structured_messages:
            message_type = message.get("type", "")

            if message_type == "user":
                self.display_user_message(message, container)
            elif message_type == "ai":
                self.display_agent_message(message, container, streaming=False)
            elif message_type == "tool":
                self.display_tool_message(message, container)

    def display_user_message(self, message: Dict[str, Any], container=None):

        if container is None:
            container = st

        content = message.get("content", "")

        with container.chat_message("user"):
            st.markdown(
                f'<div style="text-align: left;">{content}</div>',
                unsafe_allow_html=True,
            )

    def display_agent_message(
        self, message: Dict[str, Any], container=None, streaming: bool = True
    ):

        if container is None:
            container = st

        display_name = message.get("display_name", "Agent")
        avatar = message.get("avatar", "🤖")

        if "data" in message and isinstance(message["data"], dict):
            content = message["data"].get("content", "")
            tool_calls = message.get("tool_calls", [])
        else:
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])

        namespace = message.get("namespace", "")
        if namespace:
            if isinstance(namespace, str):
                namespace_list = [namespace]
            else:
                namespace_list = namespace

            from src.utils.message import get_agent_name

            agent_name_for_color = get_agent_name(namespace_list)
            if agent_name_for_color == "Unknown":
                agent_name_for_color = display_name
        else:
            agent_name_for_color = display_name

        agent_color = AgentManager.get_frontend_color(agent_name_for_color)
        agent_class = AgentManager.get_css_class(agent_name_for_color)

        st.session_state.message_counter += 1

        with container.chat_message("assistant", avatar=avatar):
            st.markdown(
                f'<div class="agent-header {agent_class}"><strong style="color: {agent_color}">{display_name}</strong></div>',
                unsafe_allow_html=True,
            )

            if content:
                text_placeholder = st.empty()

                is_replay_mode = st.session_state.get("replay_mode", False)
                if streaming and len(content) > 50 and not is_replay_mode:
                    self.simulate_typing(content, text_placeholder, speed=0.005)
                else:
                    text_placeholder.write(content)
            elif not tool_calls:
                st.write("No content available")

            if tool_calls:
                for i, tool_call in enumerate(tool_calls):
                    self._display_tool_call(tool_call)

    def _display_tool_call(self, tool_call: Dict[str, Any]):

        tool_name = tool_call.get("name", "Unknown Tool")
        tool_args = tool_call.get("args", {})

        try:
            from src.utils.message import parse_tool_call

            tool_call_message = parse_tool_call(tool_call)
        except Exception as e:
            tool_call_message = f"Tool call error: {str(e)}"

        with st.expander(f"**{tool_call_message}**", expanded=False):
            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown("**Tool:**")
                st.markdown("**ID:**")
                if tool_args:
                    st.markdown("**Arguments:**")

            with col2:
                st.markdown(f"`{tool_name}`")
                st.markdown(f"`{tool_call.get('id', 'N/A')}`")
                if tool_args:
                    import json

                    st.code(json.dumps(tool_args, indent=2), language="json")
                else:
                    st.markdown("`No arguments`")

    def display_tool_message(self, message: Dict[str, Any], container=None):

        if container is None:
            container = st

        tool_display_name = message.get("tool_display_name", "Tool")
        content = message.get("content", "")

        tool_color = AgentManager.get_frontend_color("tool")
        tool_class = "tool-message"

        st.session_state.message_counter += 1

        with container.chat_message("tool", avatar="🔧"):
            st.markdown(
                f'<div class="agent-header {tool_class}"><strong style="color: {tool_color}">{tool_display_name}</strong></div>',
                unsafe_allow_html=True,
            )

            if content:
                if len(content) > 5000:
                    st.code(content[:5000] + "\n[Output truncated...]")
                    with st.expander("More.."):
                        st.text(content)
                else:
                    st.code(content)

    def show_processing_status(
        self, label: str = "Processing...", expanded: bool = True
    ):

        return st.status(label, expanded=expanded)

    def display_loading_message(self, message: str = "Loading..."):

        with st.spinner(message):
            time.sleep(0.1)

    def display_error_message(self, error_msg: str):

        st.error(error_msg)

    def display_success_message(self, success_msg: str):

        st.success(success_msg)

    def display_warning_message(self, warning_msg: str):

        st.warning(warning_msg)

    def display_info_message(self, info_msg: str):

        st.info(info_msg)
