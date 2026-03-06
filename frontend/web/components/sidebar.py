

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from frontend.web.utils.constants import (
    AGENTS_INFO,
    CSS_CLASS_AGENT_STATUS,
    CSS_CLASS_STATUS_ACTIVE,
    CSS_CLASS_STATUS_COMPLETED,
    COMPANY_LINK
)
from src.utils.agents import AgentManager

class SidebarComponent:

    def __init__(self):

        pass

    def render_agent_status(
        self,
        container,
        active_agent: Optional[str] = None,
        completed_agents: Optional[List[str]] = None
    ):

        if completed_agents is None:
            completed_agents = []

        if "agent_status_placeholders" not in st.session_state:
            st.session_state.agent_status_placeholders = {}

        is_initial_ui = st.session_state.get("keep_initial_ui", True)

        for agent in AGENTS_INFO:
            agent_id = agent["id"]
            agent_name = agent["name"]
            agent_icon = agent["icon"]

            if agent_id not in st.session_state.agent_status_placeholders:
                st.session_state.agent_status_placeholders[agent_id] = container.empty()

            status_class = ""

            if not is_initial_ui:

                if agent_id == active_agent:
                    status_class = CSS_CLASS_STATUS_ACTIVE

                elif agent_id in completed_agents:
                    status_class = CSS_CLASS_STATUS_COMPLETED

            st.session_state.agent_status_placeholders[agent_id].html(
                f"<div class='{CSS_CLASS_AGENT_STATUS} {status_class}'>" +
                f"<div>{agent_icon} {agent_name}</div>" +
                f"</div>"
            )

    def render_model_info(self, model_info: Optional[Dict[str, Any]] = None):

        if model_info:
            model_name = model_info.get('display_name', 'Unknown Model')
            provider = model_info.get('provider', 'Unknown')

            is_dark = st.session_state.get('dark_mode', True)

            if is_dark:
                bg_color = "
                border_color = "
                text_color = "
                subtitle_color = "
                icon_color = "
            else:
                bg_color = "
                border_color = "
                text_color = "
                subtitle_color = "
                icon_color = "

            st.markdown(f, unsafe_allow_html=True)
        else:

            is_dark = st.session_state.get('dark_mode', True)

            if is_dark:
                bg_color = "
                border_color = "
                text_color = "
                icon_color = "
            else:
                bg_color = "
                border_color = "
                text_color = "
                icon_color = "

            st.markdown(f, unsafe_allow_html=True)

    def render_navigation_buttons(self, callbacks: Dict[str, Callable] = None):

        if callbacks is None:
            callbacks = {}

        if st.button("🔁 Change Model", use_container_width=True):
            if "on_change_model" in callbacks:
                callbacks["on_change_model"]()
            else:
                st.switch_page("streamlit_app.py")

        if st.button("📋 Chat History", use_container_width=True):
            if "on_chat_history" in callbacks:
                callbacks["on_chat_history"]()
            else:
                st.switch_page("pages/02_Chat_History.py")

        if st.button("✨ New Chat", use_container_width=True):
            if "on_new_chat" in callbacks:
                callbacks["on_new_chat"]()

    def render_settings_section(self, callbacks: Dict[str, Callable] = None):

        if callbacks is None:
            callbacks = {}

        st.markdown("

        if "on_theme_toggle" in callbacks:
            theme_manager = st.session_state.get('theme_manager')
            if theme_manager:
                theme_manager.create_theme_toggle(st)

        current_debug = st.session_state.get('debug_mode', False)
        debug_mode = st.checkbox("🐞 Debug Mode", value=current_debug)

        if debug_mode != current_debug:
            if "on_debug_mode_change" in callbacks:
                callbacks["on_debug_mode_change"](debug_mode)

    def render_session_stats(self, stats: Dict[str, Any]):

        with st.expander("📊 Session Stats", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", stats.get("messages_count", 0))
                st.metric("Events", stats.get("events_count", 0))
            with col2:
                st.metric("Steps", stats.get("steps_count", 0))
                st.metric("Time", f"{stats.get('elapsed_time', 0)}s")

    def render_debug_info(self, debug_info: Dict[str, Any]):

        if not st.session_state.get('debug_mode'):
            return

        with st.expander("🔍 Debug Info", expanded=False):
            st.markdown("**Session Info:**")
            session_info = {
                "user_id": debug_info.get("user_id", "Not set"),
                "thread_id": debug_info.get("thread_id", "Not set")[:8] + "..." if len(debug_info.get("thread_id", "")) > 8 else debug_info.get("thread_id", "Not set"),
            }
            st.json(session_info)

            if "logging" in debug_info:
                st.markdown("**Logging Info:**")
                st.json(debug_info["logging"])

    def render_complete_sidebar(
        self,
        model_info: Optional[Dict[str, Any]] = None,
        active_agent: Optional[str] = None,
        completed_agents: Optional[List[str]] = None,
        session_stats: Optional[Dict[str, Any]] = None,
        debug_info: Optional[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ):

        with st.sidebar:

            agents_container = st.container()
            self.render_agent_status(agents_container, active_agent, completed_agents)

            st.divider()

            self.render_model_info(model_info)
            st.divider()

            self.render_navigation_buttons(callbacks)

            st.divider()

            self.render_settings_section(callbacks)

            if session_stats:
                self.render_session_stats(session_stats)

            if debug_info:
                self.render_debug_info(debug_info)

    def hide_sidebar(self):

        st.markdown(, unsafe_allow_html=True)

    def show_back_button(self, callback: Callable = None, text: str = "← Back"):

        if st.button(text, use_container_width=True):
            if callback:
                callback()
                return True
            return True
        return False