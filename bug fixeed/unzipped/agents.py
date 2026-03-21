import json
from pathlib import Path
from typing import Dict, Optional


class AgentManager:

    _config = None
    _config_path = None

    @classmethod
    def _load_config(cls):
        if cls._config is None:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent

            # FIX: original path was "static/config/agents.json" which doesn't exist.
            # The actual file lives at frontend/static/config/agents.json
            config_path = project_root / "frontend" / "static" / "config" / "agents.json"

            cls._config_path = config_path

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cls._config = json.load(f)
            except FileNotFoundError:
                # Graceful fallback so the app doesn't crash when config is missing
                cls._config = {
                    "colors": {
                        "cli": {"default": "blue"},
                        "frontend": {"default": "#adb5bd"},
                    },
                    "avatars": {"default": "🤖"},
                    "css_classes": {"default": "agent-message"},
                    "display_names": {"default": "Unknown Agent"},
                }

        return cls._config

    @classmethod
    def normalize_agent_name(cls, agent_name: str) -> str:
        if not agent_name or not isinstance(agent_name, str):
            return ""

        agent_name_lower = agent_name.lower()

        if "planner" in agent_name_lower:
            return "planner"
        elif "reconnaissance" in agent_name_lower:
            return "reconnaissance"
        elif "initial_access" in agent_name_lower or "initial" in agent_name_lower:
            return "initial_access"
        elif "execution" in agent_name_lower:
            return "execution"
        elif "persistence" in agent_name_lower:
            return "persistence"
        elif "privilege_escalation" in agent_name_lower or "privilege" in agent_name_lower:
            return "privilege_escalation"
        elif (
            "defense_evasion" in agent_name_lower
            or "defense" in agent_name_lower
            or "evasion" in agent_name_lower
        ):
            return "defense_evasion"
        elif "summary" in agent_name_lower:
            return "summary"
        elif "tool" in agent_name_lower:
            return "tool"
        elif "supervisor" in agent_name_lower:
            return "supervisor"
        else:
            return ""

    @classmethod
    def get_cli_color(cls, agent_name: str) -> str:
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        if normalized:
            return config["colors"]["cli"].get(
                normalized, config["colors"]["cli"].get("default", "blue")
            )
        return config["colors"]["cli"].get("default", "blue")

    @classmethod
    def get_frontend_color(cls, agent_name: str) -> str:
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        if normalized:
            return config["colors"]["frontend"].get(
                normalized, config["colors"]["frontend"].get("default", "#adb5bd")
            )
        return config["colors"]["frontend"].get("default", "#adb5bd")

    @classmethod
    def get_avatar(cls, agent_name: str) -> str:
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        if normalized:
            return config["avatars"].get(normalized, config["avatars"].get("default", "🤖"))
        return config["avatars"].get("default", "🤖")

    @classmethod
    def get_css_class(cls, agent_name: str) -> str:
        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)
        if normalized:
            return config["css_classes"].get(
                normalized, config["css_classes"].get("default", "agent-message")
            )
        return config["css_classes"].get("default", "agent-message")

    @classmethod
    def get_display_name(cls, agent_name: str) -> str:
        if not agent_name or agent_name == "Unknown":
            config = cls._load_config()
            return config["display_names"].get("default", "Unknown Agent")

        config = cls._load_config()
        normalized = cls.normalize_agent_name(agent_name)

        if normalized:
            return config["display_names"].get(
                normalized, cls._format_fallback_name(agent_name)
            )

        return cls._format_fallback_name(agent_name)

    @classmethod
    def _format_fallback_name(cls, agent_name: str) -> str:
        if "_" in agent_name:
            return agent_name.replace("_", " ").title()
        return agent_name.capitalize()

    @classmethod
    def get_agent_info(cls, agent_name: str) -> Dict[str, str]:
        return {
            "cli_color": cls.get_cli_color(agent_name),
            "frontend_color": cls.get_frontend_color(agent_name),
            "avatar": cls.get_avatar(agent_name),
            "css_class": cls.get_css_class(agent_name),
            "display_name": cls.get_display_name(agent_name),
            "normalized_name": cls.normalize_agent_name(agent_name),
        }

    @classmethod
    def list_all_agents(cls) -> Dict[str, Dict[str, str]]:
        config = cls._load_config()
        agents = {}
        for agent_key in config["colors"]["cli"].keys():
            if agent_key != "default":
                agents[agent_key] = cls.get_agent_info(agent_key)
        return agents

    @classmethod
    def reload_config(cls):
        cls._config = None
        return cls._load_config()

    @classmethod
    def get_config_path(cls) -> Optional[str]:
        cls._load_config()
        return str(cls._config_path) if cls._config_path else None
