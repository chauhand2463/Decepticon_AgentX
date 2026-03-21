import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import streamlit as st
from enum import Enum


class EventType(Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    TOOL_COMMAND = "tool_command"
    TOOL_OUTPUT = "tool_output"


@dataclass
class ConversationEvent:
    event_type: EventType
    timestamp: str
    content: str
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    event_id: Optional[str] = None

    def __post_init__(self):
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "content": self.content,
        }
        if self.agent_name:
            result["agent_name"] = self.agent_name
        if self.tool_name:
            result["tool_name"] = self.tool_name
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationEvent":
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            content=data["content"],
            agent_name=data.get("agent_name"),
            tool_name=data.get("tool_name"),
        )


@dataclass
class ConversationSession:
    session_id: str
    start_time: str
    events: List[ConversationEvent]
    total_events: int = 0
    total_messages: int = 0
    total_tools_used: int = 0
    agents_used: Optional[List[str]] = None

    def __post_init__(self):
        if self.agents_used is None:
            self.agents_used = []

        self.total_events = len(self.events)
        self.total_messages = len(
            [
                e
                for e in self.events
                if e.event_type in [EventType.USER_INPUT, EventType.AGENT_RESPONSE]
            ]
        )
        self.total_tools_used = len(
            [
                e
                for e in self.events
                if e.event_type in [EventType.TOOL_COMMAND, EventType.TOOL_OUTPUT]
            ]
        )
        self.agents_used = list(
            set([e.agent_name for e in self.events if e.agent_name])
        )

    def add_event(self, event: ConversationEvent):

        self.events.append(event)
        self.__post_init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            events=[ConversationEvent.from_dict(e) for e in data["events"]],
        )


class ConversationLogger:
    def __init__(self, base_path: str = "logs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.current_session: Optional[ConversationSession] = None

    def _get_session_file_path(self, session_id: str) -> Path:

        date_str = datetime.now().strftime("%Y/%m/%d")
        session_dir = self.base_path / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"session_{session_id}.json"

    def start_session(
        self,
        user_id: str = "unknown",
        thread_id: str = "unknown",
        platform: str = "web",
        model_info: Optional[Dict[str, Any]] = None,
    ) -> str:

        session_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()

        self.current_session = ConversationSession(
            session_id=session_id, start_time=start_time, events=[]
        )
        return session_id

    def log_event(
        self,
        event_type: EventType,
        content: Optional[str] = None,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:

        if not self.current_session:
            return None

        event = ConversationEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            content=content or "",
            agent_name=agent_name,
            tool_name=tool_name,
        )

        self.current_session.add_event(event)
        return event.event_id

    def log_user_input(self, content: str) -> Optional[str]:

        return self.log_event(event_type=EventType.USER_INPUT, content=content)

    def log_agent_response(self, agent_name: str, content: str, **kwargs) -> Optional[str]:

        return self.log_event(
            event_type=EventType.AGENT_RESPONSE, agent_name=agent_name, content=content
        )

    def log_tool_execution(self, tool_name: str, content: str, **kwargs) -> Optional[str]:

        return self.log_event(
            event_type=EventType.TOOL_COMMAND, tool_name=tool_name, content=content
        )

    def log_tool_command(self, tool_name: str, command: str):

        return self.log_event(
            event_type=EventType.TOOL_COMMAND, tool_name=tool_name, content=command
        )

    def log_tool_output(self, tool_name: str, output: str):

        return self.log_event(
            event_type=EventType.TOOL_OUTPUT, tool_name=tool_name, content=output
        )

    def log_workflow_start(self, user_input: str) -> Optional[str]:

        return self.log_user_input(user_input)

    def log_workflow_complete(
        self, step_count: int = 0, execution_time: float = 0
    ) -> str:

        return str(uuid.uuid4())

    def log_workflow_error(self, error_message: str) -> str:

        return str(uuid.uuid4())

    def end_session(self) -> Optional[str]:

        if not self.current_session:
            return None

        session_id = self.current_session.session_id
        self.save_session()
        self.current_session = None
        return session_id

    def save_session(self) -> bool:

        if not self.current_session:
            return False

        try:
            file_path = self._get_session_file_path(self.current_session.session_id)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.current_session.to_dict(), f, indent=2, ensure_ascii=False
                )
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[ConversationSession]:

        try:
            for session_file in self.base_path.rglob(f"session_{session_id}.json"):
                if session_file.exists():
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)
                    return ConversationSession.from_dict(session_data)
            return None
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return None

    def list_sessions(
        self, user_id: Optional[str] = None, days_back: int = 30
    ) -> List[Dict[str, Any]]:

        sessions = []

        try:
            for session_file in self.base_path.rglob("session_*.json"):
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)

                    session_info = {
                        "session_id": session_data["session_id"],
                        "user_id": session_data.get("user_id", "unknown"),
                        "start_time": session_data["start_time"],
                        "end_time": session_data.get("end_time"),
                        "platform": session_data.get("platform", "web"),
                        "total_events": len(session_data.get("events", [])),
                        "total_messages": len(
                            [
                                e
                                for e in session_data.get("events", [])
                                if e.get("event_type")
                                in ["user_input", "agent_response"]
                            ]
                        ),
                        "agents_used": list(
                            set(
                                [
                                    e.get("agent_name")
                                    for e in session_data.get("events", [])
                                    if e.get("agent_name")
                                ]
                            )
                        ),
                        "model_info": session_data.get("model_info"),
                        "file_path": str(session_file),
                    }

                    sessions.append(session_info)

                except Exception:
                    continue

            sessions.sort(key=lambda x: x["start_time"], reverse=True)

        except Exception as e:
            print(f"Error listing sessions: {e}")

        return sessions

    def get_session_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:

        sessions = self.list_sessions(user_id=user_id)

        total_messages = sum(s["total_messages"] for s in sessions)
        avg_messages = total_messages / len(sessions) if sessions else 0

        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "total_events": sum(s["total_events"] for s in sessions),
            "unique_agents": list(
                set().union(*[s["agents_used"] for s in sessions if s["agents_used"]])
            ),
            "platforms_used": list(set([s["platform"] for s in sessions])),
            "models_used": list(
                set([s["model_info"] for s in sessions if s.get("model_info")])
            ),
            "avg_messages_per_session": round(avg_messages, 1),
        }


_global_logger: Optional[ConversationLogger] = None


def get_conversation_logger() -> ConversationLogger:

    global _global_logger
    if _global_logger is None:
        _global_logger = ConversationLogger()
    return _global_logger


def set_conversation_logger(logger: ConversationLogger):

    global _global_logger
    _global_logger = logger
