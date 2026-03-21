import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

from src.utils.logging.logger import get_logger


class ReplaySystem:
    def __init__(self):
        self.logger = get_logger()

    def start_replay(self, session_id: str) -> bool:

        try:
            session = self.logger.load_session(session_id)
            if not session:
                return False

            st.session_state.replay_mode = True
            st.session_state.replay_session = session
            st.session_state.replay_session_id = session_id

            if "frontend_messages" in st.session_state:
                st.session_state.backup_frontend_messages = (
                    st.session_state.frontend_messages.copy()
                )
            else:
                st.session_state.backup_frontend_messages = []

            if "terminal_messages" in st.session_state:
                st.session_state.backup_terminal_messages = (
                    st.session_state.terminal_messages.copy()
                )
            else:
                st.session_state.backup_terminal_messages = []

            if "event_history" in st.session_state:
                st.session_state.backup_event_history = (
                    st.session_state.event_history.copy()
                )
            else:
                st.session_state.backup_event_history = []

            st.session_state.backup_active_agent = st.session_state.get("active_agent")
            st.session_state.backup_completed_agents = st.session_state.get(
                "completed_agents", []
            ).copy()

            st.session_state.frontend_messages = []
            st.session_state.terminal_messages = []
            st.session_state.event_history = []
            st.session_state.active_agent = None
            st.session_state.completed_agents = []

            return True

        except Exception:
            return False

    def stop_replay(self):

        st.session_state.replay_mode = False

        st.session_state.replay_completed = True

        for backup_key in [
            "backup_frontend_messages",
            "backup_terminal_messages",
            "backup_event_history",
            "backup_active_agent",
            "backup_completed_agents",
        ]:
            if backup_key in st.session_state:
                del st.session_state[backup_key]

        for key in ["replay_session", "replay_session_id"]:
            if key in st.session_state:
                del st.session_state[key]

    def is_replay_mode(self) -> bool:

        return st.session_state.get("replay_mode", False)

    async def execute_replay(self, chat_area, agents_container, chat_ui):

        session = st.session_state.get("replay_session")
        if not session or not session.events:
            return

        with st.status("Loading replay session...", expanded=True) as status:
            replay_messages = []
            terminal_messages = []
            agents_involved = set()

            for event in session.events:
                try:
                    frontend_message = self._convert_to_frontend_message(event)

                    if frontend_message:
                        replay_messages.append(frontend_message)

                        if frontend_message.get("type") == "tool":
                            terminal_messages.append(frontend_message)

                        if event.agent_name:
                            agents_involved.add(event.agent_name)

                except Exception as e:
                    print(f"Error processing event: {e}")
                    continue

            if replay_messages:
                st.session_state.frontend_messages = replay_messages

            if terminal_messages:
                st.session_state.terminal_messages = terminal_messages

            if agents_involved:
                completed_agents = (
                    list(agents_involved)[:-1] if len(agents_involved) > 1 else []
                )
                active_agent = (
                    list(agents_involved)[-1].lower() if agents_involved else None
                )

                st.session_state.completed_agents = completed_agents
                st.session_state.active_agent = active_agent

            status.update(
                label=f"✅ Replay Complete! Loaded {len(replay_messages)} messages from {len(session.events)} events.",
                state="complete",
            )

    def _convert_to_frontend_message(self, event) -> Optional[Dict[str, Any]]:

        timestamp = datetime.now().isoformat()

        if event.event_type.value == "user_input":
            return {"type": "user", "content": event.content, "timestamp": timestamp}

        elif event.event_type.value == "agent_response":
            frontend_message = {
                "type": "ai",
                "agent_id": event.agent_name.lower() if event.agent_name else "agent",
                "display_name": event.agent_name or "Agent",
                "avatar": self._get_agent_avatar(event.agent_name),
                "content": event.content,
                "timestamp": timestamp,
                "id": f"replay_agent_{event.agent_name}_{timestamp}",
            }

            if hasattr(event, "tool_calls") and event.tool_calls:
                frontend_message["tool_calls"] = event.tool_calls

            return frontend_message

        elif event.event_type.value == "tool_command":
            return {
                "type": "tool",
                "tool_display_name": event.tool_name or "Tool",
                "content": f"Command: {event.content}",
                "timestamp": timestamp,
                "id": f"replay_tool_cmd_{event.tool_name}_{timestamp}",
            }

        elif event.event_type.value == "tool_output":
            return {
                "type": "tool",
                "tool_display_name": event.tool_name or "Tool Output",
                "content": event.content,
                "timestamp": timestamp,
                "id": f"replay_tool_out_{event.tool_name}_{timestamp}",
            }

        return None

    def _get_agent_avatar(self, agent_name: str) -> str:

        if not agent_name:
            return "🤖"

        agent_avatars = {
            "supervisor": "👨‍💼",
            "planner": "🧠",
            "reconnaissance": "🔍",
            "initial_access": "🔑",
            "execution": "💻",
            "persistence": "🔐",
            "privilege_escalation": "🔒",
            "defense_evasion": "🕵️",
            "summary": "📋",
        }

        agent_key = agent_name.lower()
        for key, avatar in agent_avatars.items():
            if key in agent_key:
                return avatar

        return "🤖"


_replay_system: Optional[ReplaySystem] = None


def get_replay_system() -> ReplaySystem:

    global _replay_system
    if _replay_system is None:
        _replay_system = ReplaySystem()
    return _replay_system
