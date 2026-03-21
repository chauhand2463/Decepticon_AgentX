import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from frontend.web.utils.constants import (
    AGENTS_INFO,
    CSS_CLASS_AGENT_STATUS,
    CSS_CLASS_STATUS_ACTIVE,
    CSS_CLASS_STATUS_COMPLETED,
    COMPANY_LINK,
)


class SidebarComponent:
    def __init__(self):
        pass

    def render_agent_status(
        self,
        container,
        active_agent: Optional[str] = None,
        completed_agents: Optional[List[str]] = None,
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

            st.session_state.agent_status_placeholders[agent_id].markdown(
                f"<div class='{CSS_CLASS_AGENT_STATUS} {status_class}'>"
                f"<div>{agent_icon} {agent_name}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    def render_model_info(self, model_info: Optional[Dict[str, Any]] = None):
        if model_info:
            model_name = model_info.get(
                "display_name", model_info.get("model", "Unknown")
            )
            provider = model_info.get("provider", "Unknown")

            st.sidebar.markdown(
                f"""
            <div style="padding: 1rem; border-radius: 0.5rem; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                <div style="font-size: 0.8rem; color: #888;">Active Model</div>
                <div style="font-weight: bold; color: #ff4b4b;">{model_name}</div>
                <div style="font-size: 0.7rem; color: #666;">Provider: {provider}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.warning("No model selected")

    def render_navigation_buttons(self, callbacks: Optional[Dict[str, Callable[..., Any]]] = None):
        if callbacks is None:
            callbacks = {}

        if st.sidebar.button("🔁 Change Model", use_container_width=True):
            if "on_change_model" in callbacks:
                callbacks["on_change_model"]()
            else:
                st.switch_page("streamlit_app.py")

        if st.sidebar.button("📋 Chat History", use_container_width=True):
            if "on_chat_history" in callbacks:
                callbacks["on_chat_history"]()
            else:
                st.switch_page("pages/02_Chat_History.py")

        if st.sidebar.button("✨ New Chat", use_container_width=True):
            if "on_new_chat" in callbacks:
                callbacks["on_new_chat"]()

        # Terminal Toggle
        is_terminal_visible = st.session_state.get("terminal_visible", True)
        label = "🐚 Hide Terminal" if is_terminal_visible else "🐚 Show Terminal"
        if st.sidebar.button(
            label, use_container_width=True, key="sidebar_terminal_toggle"
        ):
            if "on_toggle_terminal" in callbacks:
                callbacks["on_toggle_terminal"]()
            else:
                st.session_state.terminal_visible = not is_terminal_visible
                st.rerun()

    def render_settings_section(self, callbacks: Optional[Dict[str, Callable[..., Any]]] = None):
        st.sidebar.markdown("### Systems Control")
        
        # Theme Selection
        current_theme = st.session_state.get("theme", "extreme")
        theme_options = {"extreme": "🔥 Extreme HUD", "dark": "🌑 Stealth Dark", "light": "☀️ Tactical Light"}
        selected_theme_label = st.sidebar.selectbox(
            "Visual Interface",
            options=list(theme_options.values()),
            index=list(theme_options.keys()).index(current_theme) if current_theme in theme_options else 0
        )
        
        # Reverse lookup for theme key
        new_theme = next((k for k, v in theme_options.items() if v == selected_theme_label), "extreme")
        if new_theme != current_theme:
            st.session_state.theme = new_theme
            st.rerun()

        current_debug = st.session_state.get("debug_mode", False)
        debug_mode = st.sidebar.checkbox("🐞 Verbose Debug", value=current_debug)
        if debug_mode != current_debug:
            if callbacks and "on_debug_mode_change" in callbacks:
                callbacks["on_debug_mode_change"](debug_mode)
            else:
                st.session_state.debug_mode = debug_mode

    def render_session_stats(self, stats: Dict[str, Any]):
        with st.sidebar.expander("📊 Session Stats", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", stats.get("messages_count", 0))
                st.metric("Events", stats.get("events_count", 0))
            with col2:
                st.metric("Steps", stats.get("steps_count", 0))
                st.metric("Time", f"{stats.get('elapsed_time', 0)}s")

    def render_debug_info(self, debug_info: Dict[str, Any]):
        if not st.session_state.get("debug_mode"):
            return
        with st.sidebar.expander("🔍 Debug Info", expanded=False):
            st.json(debug_info)

    def render_complete_sidebar(
        self,
        model_info=None,
        active_agent=None,
        completed_agents=None,
        session_stats=None,
        debug_info=None,
        callbacks=None,
    ):
        with st.sidebar:
            st.markdown(f"### [DECEPTICON]({COMPANY_LINK})", unsafe_allow_html=True)
            self.render_agent_status(st.container(), active_agent, completed_agents)
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
        st.markdown(
            "<style>section[data-testid='stSidebar'] { display: none; }</style>",
            unsafe_allow_html=True,
        )
