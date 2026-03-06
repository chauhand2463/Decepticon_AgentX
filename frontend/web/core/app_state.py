

import streamlit as st
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.utils.memory import (
    create_thread_config,
    create_memory_namespace
)
from src.utils.logging.logger import get_logger
from src.utils.logging.replay import get_replay_system

class AppStateManager:

    def __init__(self):

        self.logger = None
        self.replay_system = None
        self._initialize_session_state()
        self._initialize_user_session()
        self._initialize_logging()

    def _initialize_session_state(self):

        defaults = {

            "executor_ready": False,
            "direct_executor": None,

            "messages": [],
            "structured_messages": [],
            "terminal_messages": [],
            "event_history": [],

            "current_model": None,
            "models_by_provider": {},
            "models_cache_timestamp": 0,

            "workflow_running": False,
            "initialization_in_progress": False,
            "initialization_error": None,

            "active_agent": None,
            "completed_agents": [],
            "current_step": 0,
            "agent_status_placeholders": {},

            "terminal_placeholder": None,
            "terminal_history": [],
            "keep_initial_ui": True,
            "show_controls": False,

            "session_start_time": time.time(),
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",

            "replay_mode": False,
            "replay_session_id": None,
            "replay_completed": False,

            "logging_session_id": None,
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def _initialize_user_session(self):

        if "user_id" not in st.session_state:
            browser_info = f"{st.session_state.get('_session_id', '')}{datetime.now().strftime('%Y%m%d')}"
            user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:8]
            st.session_state.user_id = f"user_{user_hash}"

        if "thread_config" not in st.session_state:
            st.session_state.thread_config = create_thread_config(
                user_id=st.session_state.user_id,
                conversation_id=None
            )

        if "memory_namespace" not in st.session_state:
            st.session_state.memory_namespace = create_memory_namespace(
                user_id=st.session_state.user_id,
                namespace_type="memories"
            )

    def _initialize_logging(self):

        if "logger" not in st.session_state:
            st.session_state.logger = get_logger()
            st.session_state.replay_system = get_replay_system()
            self.logger = st.session_state.logger
            self.replay_system = st.session_state.replay_system

    def reset_session(self, keep_model: bool = True):

        if hasattr(st.session_state, 'logger') and st.session_state.logger and st.session_state.logger.current_session:
            st.session_state.logger.end_session()

        reset_keys = [
            "executor_ready", "messages", "structured_messages", "terminal_messages",
            "workflow_running", "active_agent", "completed_agents", "current_step",
            "agent_status_placeholders", "terminal_placeholder", "event_history",
            "initialization_in_progress", "initialization_error", "terminal_history",
            "keep_initial_ui", "show_controls"
        ]

        if not keep_model:
            reset_keys.extend([
                "current_model", "models_by_provider", "models_cache_timestamp"
            ])

        replay_keys = ["replay_mode", "replay_session_id", "replay_completed"]
        reset_keys.extend(replay_keys)

        st.session_state.session_start_time = time.time()

        for key in reset_keys:
            if key in st.session_state:
                if key in ["agent_status_placeholders"]:
                    st.session_state[key] = {}
                elif key in ["messages", "structured_messages", "terminal_messages",
                           "completed_agents", "event_history", "terminal_history"]:
                    st.session_state[key] = []
                elif key in ["current_step"]:
                    st.session_state[key] = 0
                elif key in ["keep_initial_ui"]:
                    st.session_state[key] = True
                else:
                    st.session_state[key] = False if key not in ["current_model", "terminal_placeholder", "direct_executor"] else None

        if "direct_executor" in st.session_state:
            st.session_state.direct_executor = None

    def create_new_conversation(self):

        new_conversation_id = str(uuid.uuid4())
        st.session_state.thread_config = create_thread_config(
            user_id=st.session_state.user_id,
            conversation_id=new_conversation_id
        )

        self.reset_session(keep_model=True)

        return new_conversation_id

    def get_env_config(self) -> Dict[str, Any]:

        return {
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
            "theme": os.getenv("THEME", "dark"),
            "docker_container": os.getenv("DOCKER_CONTAINER", "decepticon-kali"),
            "chat_height": int(os.getenv("CHAT_HEIGHT", "700"))
        }

    def set_debug_mode(self, mode: bool):

        st.session_state.debug_mode = mode

    def get_session_stats(self) -> Dict[str, Any]:

        session_start_time = getattr(st.session_state, 'session_start_time', time.time())
        elapsed_time = int(time.time() - session_start_time)

        structured_messages = getattr(st.session_state, 'structured_messages', [])
        event_history = getattr(st.session_state, 'event_history', [])
        current_step = getattr(st.session_state, 'current_step', 0)
        active_agent = getattr(st.session_state, 'active_agent', None)
        completed_agents = getattr(st.session_state, 'completed_agents', [])

        return {
            "messages_count": len(structured_messages),
            "events_count": len(event_history),
            "steps_count": current_step,
            "elapsed_time": elapsed_time,
            "active_agent": active_agent,
            "completed_agents_count": len(completed_agents)
        }

    def get_debug_info(self) -> Dict[str, Any]:

        debug_info = {
            "user_id": st.session_state.get("user_id", "Not set"),
            "thread_id": st.session_state.get("thread_config", {}).get("configurable", {}).get("thread_id", "Not set"),
            "executor_ready": getattr(st.session_state, 'executor_ready', False),
            "workflow_running": getattr(st.session_state, 'workflow_running', False),
        }

        if hasattr(st.session_state, 'logger') and st.session_state.logger and st.session_state.logger.current_session:
            current_session = st.session_state.logger.current_session
            debug_info["logging"] = {
                "session_id": current_session.session_id,
                "events_count": len(current_session.events),
            }

        return debug_info

    def is_ready(self) -> bool:

        return (
            st.session_state.executor_ready and
            st.session_state.current_model is not None and
            not st.session_state.initialization_in_progress
        )

_app_state_manager = None

def get_app_state_manager() -> AppStateManager:

    global _app_state_manager
    if _app_state_manager is None:
        _app_state_manager = AppStateManager()
    return _app_state_manager