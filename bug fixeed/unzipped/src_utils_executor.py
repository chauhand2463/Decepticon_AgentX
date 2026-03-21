import uuid
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator

from src.graphs.swarm import create_dynamic_swarm
# FIX: use make_initial_state to build the input dict instead of a raw dict literal.
# The raw literal in the original had a duplicate "messages" key which silently
# discarded the HumanMessage, leaving PHANTOM with no user input.
from src.swarm.graph_fixed import make_initial_state
from src.utils.llm.config_manager import (
    update_llm_config,
    get_current_llm_config,
    get_current_llm,
)
from src.utils.message import (
    extract_message_content,
    get_agent_name,
    parse_tool_name,
)


class Executor:

    def __init__(self):
        self._initialized = False
        self._swarm = None
        self._config = None
        self._thread_id = None
        self._current_model = None
        self._current_llm = None
        self._processed_message_ids = set()

    @property
    def swarm(self):
        return self._swarm

    @property
    def thread_id(self):
        return self._thread_id

    @property
    def current_model(self):
        return self._current_model

    async def initialize_swarm(
        self,
        model_info: Optional[Dict[str, Any]] = None,
        thread_config: Optional[Dict[str, Any]] = None,
    ):
        try:
            self._initialized = False
            self._swarm = None

            if thread_config:
                self._config = thread_config
                self._thread_id = thread_config["configurable"]["thread_id"]
            else:
                self._thread_id = str(uuid.uuid4())
                self._config = {
                    "configurable": {
                        "thread_id": self._thread_id,
                    }
                }

            if model_info:
                self._current_model = model_info
                update_llm_config(
                    model_name=model_info["model_name"],
                    provider=model_info["provider"],
                    display_name=model_info["display_name"],
                    temperature=0.0,
                )

            self._current_llm = get_current_llm()
            self._swarm = await create_dynamic_swarm()
            self._initialized = True

            return self._thread_id

        except Exception as e:
            self._initialized = False
            self._swarm = None
            raise Exception(f"Swarm initialization failed: {str(e)}")

    async def execute_workflow(
        self,
        user_input: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:

        if not self.is_ready():
            raise Exception("Executor not ready - swarm not initialized")

        execution_config = config if config else self._config
        self._processed_message_ids = set()

        # FIX: replaced bare dict literal (which had a duplicate "messages" key)
        # with the helper that builds the state correctly.
        inputs = make_initial_state(user_input)

        try:
            step_count = 0

            async for namespace, output in self._swarm.astream(
                inputs,
                stream_mode="updates",
                config=execution_config,
                subgraphs=True,
            ):
                step_count += 1

                for node, value in output.items():
                    agent_name = get_agent_name(namespace)

                    if "messages" in value and value["messages"]:
                        messages = value["messages"]
                        if messages:
                            latest_message = messages[-1]
                            should_display, message_type = self._should_display_message(
                                latest_message, agent_name, step_count
                            )

                            if should_display:
                                event_data = {
                                    "type": "message",
                                    "message_type": message_type,
                                    "agent_name": agent_name,
                                    "namespace": namespace,
                                    "content": extract_message_content(latest_message),
                                    "raw_message": latest_message,
                                    "step_count": step_count,
                                    "timestamp": datetime.now().isoformat(),
                                }

                                if message_type == "tool":
                                    tool_name = getattr(
                                        latest_message, "name", "Unknown Tool"
                                    )
                                    event_data["tool_name"] = tool_name
                                    event_data["tool_display_name"] = parse_tool_name(
                                        tool_name
                                    )

                                yield event_data

            yield {
                "type": "workflow_complete",
                "step_count": step_count,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _should_display_message(self, message, agent_name: str, step_count: int):
        message_id = None
        if hasattr(message, "id") and message.id:
            message_id = message.id
        else:
            content = extract_message_content(message)
            message_id = f"{agent_name}_{hash(content)}"

        cls_name = message.__class__.__name__

        if cls_name in ("HumanMessage", "AIMessage", "ToolMessage"):
            if message_id not in self._processed_message_ids:
                self._processed_message_ids.add(message_id)
                return True, cls_name.replace("Message", "").lower()
            return False, None

        return False, None

    def get_current_model_info(self):
        if self._current_model:
            return self._current_model

        try:
            config = get_current_llm_config()
            return {
                "display_name": config.display_name,
                "provider": config.provider,
                "model_name": config.model_name,
            }
        except Exception:
            return {
                "display_name": "Unknown Model",
                "provider": "Unknown",
                "model_name": "unknown",
            }

    async def change_model(self, model_info: Dict[str, Any]):
        try:
            self._current_model = model_info
            update_llm_config(
                model_name=model_info["model_name"],
                provider=model_info["provider"],
                display_name=model_info["display_name"],
                temperature=0.0,
            )
            self._current_llm = get_current_llm()
            self._swarm = await create_dynamic_swarm()
            return True
        except Exception as e:
            raise Exception(f"Model change failed: {str(e)}")

    def is_ready(self):
        return self._initialized and self._swarm is not None

    def reset_session(self):
        self._thread_id = None
        self._config = None
        self._processed_message_ids = set()
        self._initialized = False

    def get_state_dict(self):
        return {
            "initialized": self._initialized,
            "thread_id": self._thread_id,
            "current_model": self._current_model,
            "has_swarm": self._swarm is not None,
        }
