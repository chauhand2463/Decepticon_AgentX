

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from frontend.web.utils.constants import ICON, ICON_TEXT, COMPANY_LINK
import time

class ChatHistoryComponent:

    def __init__(self):

        pass

    def render_page_header(self):

        st.logo(ICON_TEXT, icon_image=ICON, size="large", link=COMPANY_LINK)
        st.title("📊 :red[Session Logs]")

    def render_back_button(self, callback: Callable = None) -> bool:

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", use_container_width=True):
                if callback:
                    callback()
                return True
        return False

    def render_empty_state(self):

        st.info("📭 No chat sessions found")
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start New Chat", use_container_width=True, type="primary"):
                return True
        return False

    def render_sessions_header(self, session_count: int, total_count: int = None):

        st.subheader("📋 Recent Sessions")
        if total_count and total_count > session_count:
            st.caption(f"Showing {session_count} of {total_count} sessions")
        else:
            st.caption(f"Showing {session_count} recent sessions")

    def render_filter_options(self) -> Dict[str, str]:

        with st.expander("🔍 Filter Options", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                date_filter = st.selectbox(
                    "Filter by Date",
                    options=["All", "Today", "Last 7 days", "Last 30 days"],
                    index=0
                )

            with col2:
                sort_option = st.selectbox(
                    "Sort by",
                    options=["Newest First", "Oldest First", "Most Events"],
                    index=0
                )

        return {
            "date_filter": date_filter,
            "sort_option": sort_option
        }

    def format_session_time(self, session_time: str) -> str:

        try:
            dt = datetime.fromisoformat(session_time.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return session_time[:19] if len(session_time) > 19 else session_time

    def render_session_card(
        self,
        session: Dict[str, Any],
        index: int,
        callbacks: Optional[Dict[str, Callable]] = None
    ) -> Optional[str]:

        if callbacks is None:
            callbacks = {}

        session_id = session.get('session_id', 'Unknown')

        with st.container():

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:

                time_str = self.format_session_time(session.get('start_time', ''))
                st.markdown(f"**🕒 {time_str}**")
                st.caption(f"Session: {session_id[:16]}...")

                preview_text = session.get('preview', "No user input found")
                if len(preview_text) > 100:
                    preview_text = preview_text[:100] + "..."
                st.caption(f"💬 {preview_text}")

                model_info = session.get('model')
                if model_info:
                    st.caption(f"🤖 Model: {model_info}")

            with col2:
                st.metric("Events", session.get('event_count', 0))

            with col3:

                if st.button("📄 Details", key=f"details_{index}", use_container_width=True):
                    return "details"

            with col4:

                if st.button("🎬 Replay", key=f"replay_{index}", use_container_width=True, type="primary"):
                    if "on_replay" in callbacks:
                        callbacks["on_replay"](session_id)
                    return "replay"

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col4:
                export_filename = f"session_{session_id[:8]}_{datetime.now().strftime('%Y%m%d')}.json"

                if "get_export_data" in callbacks:
                    export_data = callbacks["get_export_data"](session_id)
                    if export_data:
                        st.download_button(
                            label="💾 Export",
                            data=export_data,
                            file_name=export_filename,
                            mime="application/json",
                            key=f"export_{index}",
                            use_container_width=True
                        )
                    else:
                        st.button("❌ Export", disabled=True, key=f"export_disabled_{index}", use_container_width=True)

            st.divider()

        return None

    def render_session_details(self, session: Dict[str, Any]):

        session_id = session.get('session_id', 'Unknown')

        with st.expander(f"Session Details - {session_id[:16]}...", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Session Info:**")
                session_info = {
                    "Session ID": session_id,
                    "Start Time": session.get('start_time', 'Unknown'),
                    "Event Count": session.get('event_count', 0),
                    "Model": session.get('model', 'Unknown')
                }
                st.json(session_info)

            with col2:
                st.markdown("**Preview:**")
                preview = session.get('preview', 'No preview available')
                st.text_area("Content", value=preview, height=100, disabled=True)

    def render_sessions_list(
        self,
        sessions: List[Dict[str, Any]],
        callbacks: Optional[Dict[str, Callable]] = None
    ):

        filter_options = self.render_filter_options()

        filtered_sessions = sessions

        st.divider()

        for i, session in enumerate(filtered_sessions):
            action = self.render_session_card(session, i, callbacks)

            if action == "details":
                self.render_session_details(session)

    def render_complete_history_page(
        self,
        sessions: List[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None
    ):

        self.hide_sidebar()

        self.render_page_header()

        if self.render_back_button():
            if callbacks and "on_back" in callbacks:
                callbacks["on_back"]()

        if not sessions:
            if self.render_empty_state():
                if callbacks and "on_new_chat" in callbacks:
                    callbacks["on_new_chat"]()
        else:

            self.render_sessions_header(len(sessions))

            self.render_sessions_list(sessions, callbacks)

    def hide_sidebar(self):

        st.markdown("<style>section[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)

    def show_loading_state(self, message: str = "Loading sessions..."):

        with st.spinner(message):
            time.sleep(0.1)

    def show_error_state(self, error_msg: str):

        st.error(f"Error loading sessions: {error_msg}")

        if st.button("🔄 Retry", use_container_width=True):
            return True
        return False

    def show_replay_start_message(self, session_id: str):

        pass