import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    TOOL_COMMAND = "tool_command"
    TOOL_OUTPUT = "tool_output"


@dataclass
class Event:
    event_type: EventType
    timestamp: str
    content: str
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

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
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            content=data["content"],
            agent_name=data.get("agent_name"),
            tool_name=data.get("tool_name"),
            tool_calls=data.get("tool_calls"),
        )


@dataclass
class Session:
    session_id: str
    start_time: str
    events: List[Event]
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "events": [event.to_dict() for event in self.events],
        }
        if self.model:
            result["model"] = self.model
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            events=[Event.from_dict(e) for e in data["events"]],
            model=data.get("model"),
        )


class Logger:
    def __init__(self, base_path: str = "logs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.current_session: Optional[Session] = None

    def _get_session_file_path(self, session_id: str) -> Path:

        date_str = datetime.now().strftime("%Y/%m/%d")
        session_dir = self.base_path / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"session_{session_id}.json"

    def start_session(self, model_info: Optional[str] = None) -> str:

        session_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()

        self.current_session = Session(
            session_id=session_id, start_time=start_time, events=[], model=model_info
        )
        return session_id

    def log_user_input(self, content: str):

        if self.current_session:
            event = Event(
                event_type=EventType.USER_INPUT,
                timestamp=datetime.now().isoformat(),
                content=content,
            )
            self.current_session.events.append(event)

    def log_agent_response(
        self,
        agent_name: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ):

        if self.current_session:
            event = Event(
                event_type=EventType.AGENT_RESPONSE,
                timestamp=datetime.now().isoformat(),
                content=content,
                agent_name=agent_name,
                tool_calls=tool_calls,
            )
            self.current_session.events.append(event)

    def log_tool_command(self, tool_name: str, command: str):

        if self.current_session:
            event = Event(
                event_type=EventType.TOOL_COMMAND,
                timestamp=datetime.now().isoformat(),
                content=command,
                tool_name=tool_name,
            )
            self.current_session.events.append(event)

    def log_tool_output(self, tool_name: str, output: str):

        if self.current_session:
            event = Event(
                event_type=EventType.TOOL_OUTPUT,
                timestamp=datetime.now().isoformat(),
                content=output,
                tool_name=tool_name,
            )
            self.current_session.events.append(event)

    def save_session(self) -> bool:

        if not self.current_session:
            return False

        if not self.current_session.events or len(self.current_session.events) == 0:
            print(
                f"Session {self.current_session.session_id} has no events, skipping save."
            )
            return False

        try:
            file_path = self._get_session_file_path(self.current_session.session_id)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.current_session.to_dict(), f, indent=2, ensure_ascii=False
                )
            print(
                f"Session {self.current_session.session_id} saved with {len(self.current_session.events)} events."
            )
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False

    def end_session(self) -> Optional[str]:

        if not self.current_session:
            return None

        session_id = self.current_session.session_id
        self.save_session()
        self.current_session = None
        return session_id

    def load_session(self, session_id: str) -> Optional[Session]:

        try:
            for session_file in self.base_path.rglob(f"session_{session_id}.json"):
                if session_file.exists():
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)
                    return Session.from_dict(session_data)
            return None
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return None

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:

        sessions = []

        try:
            for session_file in self.base_path.rglob("session_*.json"):
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)

                    session_info = {
                        "session_id": session_data["session_id"],
                        "start_time": session_data["start_time"],
                        "event_count": len(session_data.get("events", [])),
                        "file_path": str(session_file),
                    }

                    if session_data.get("model"):
                        session_info["model"] = session_data["model"]

                    events = session_data.get("events", [])
                    preview = "No user input found"
                    for event in events:
                        if event.get("event_type") == "user_input":
                            preview = event.get("content", "")[:100]
                            if len(preview) < len(event.get("content", "")):
                                preview += "..."
                            break

                    session_info["preview"] = preview
                    sessions.append(session_info)

                except Exception:
                    continue

            sessions.sort(key=lambda x: x["start_time"], reverse=True)

        except Exception as e:
            print(f"Error listing sessions: {e}")

        return sessions[:limit]


_logger: Optional[Logger] = None


def get_logger() -> Logger:

    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger
