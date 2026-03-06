

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional, Callable
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from frontend.web.core.message_processor import MessageProcessor
from frontend.web.core.executor_manager import get_executor_manager

class WorkflowHandler:

    def __init__(self):

        self.message_processor = MessageProcessor()
        self.executor_manager = get_executor_manager()

    def validate_execution_state(self) -> Dict[str, Any]:

        if not self.executor_manager.is_ready():
            return {
                "can_execute": False,
                "error_message": "AI agents not ready. Please initialize first."
            }

        if st.session_state.workflow_running:
            return {
                "can_execute": False,
                "error_message": "Another workflow is already running. Please wait."
            }

        return {"can_execute": True, "error_message": ""}

    def prepare_user_input(self, user_input: str) -> Dict[str, Any]:

        user_message = self.message_processor._create_user_message(user_input)
        st.session_state.structured_messages.append(user_message)
        return user_message

    async def execute_workflow_logic(
        self,
        user_input: str,
        ui_callbacks: Dict[str, Callable] = None,
        terminal_ui = None
    ) -> Dict[str, Any]:

        if ui_callbacks is None:
            ui_callbacks = {}

        st.session_state.workflow_running = True

        execution_result = {
            "success": False,
            "event_count": 0,
            "agent_activity": {},
            "error_message": "",
            "terminal_ui": terminal_ui
        }

        try:
            event_count = 0
            agent_activity = {}

            async for event in self.executor_manager.execute_workflow(
                user_input,
                config=st.session_state.thread_config
            ):
                event_count += 1
                st.session_state.event_history.append(event)

                try:

                    success = await self._process_event_logic(
                        event,
                        agent_activity,
                        ui_callbacks,
                        terminal_ui
                    )

                    if not success:
                        break

                    self._update_agent_status_logic()

                except Exception as e:
                    if st.session_state.debug_mode:
                        execution_result["error_message"] = f"Event processing error: {str(e)}"

            execution_result.update({
                "success": True,
                "event_count": event_count,
                "agent_activity": agent_activity
            })

        except Exception as e:
            execution_result["error_message"] = f"Workflow execution error: {str(e)}"

        finally:
            st.session_state.workflow_running = False

            if "logger" in st.session_state and st.session_state.logger:
                st.session_state.logger.save_session()

        return execution_result

    async def _process_event_logic(
        self,
        event: Dict[str, Any],
        agent_activity: Dict[str, int],
        ui_callbacks: Dict[str, Callable],
        terminal_ui = None
    ) -> bool:

        event_type = event.get("type", "")

        if event_type == "message":
            return await self._process_message_event_logic(
                event, agent_activity, ui_callbacks, terminal_ui
            )
        elif event_type == "workflow_complete":
            if "on_workflow_complete" in ui_callbacks:
                ui_callbacks["on_workflow_complete"]()
            return True
        elif event_type == "error":
            error_msg = event.get("error", "Unknown error")
            if "on_error" in ui_callbacks:
                ui_callbacks["on_error"](error_msg)
            return False

        return True

    async def _process_message_event_logic(
        self,
        event: Dict[str, Any],
        agent_activity: Dict[str, int],
        ui_callbacks: Dict[str, Callable],
        terminal_ui = None
    ) -> bool:

        frontend_message = self.message_processor.process_cli_event(event)

        if self.message_processor.is_duplicate_message(
            frontend_message, st.session_state.structured_messages
        ):
            return True

        st.session_state.structured_messages.append(frontend_message)

        self._log_message_event(event, frontend_message)

        agent_name = event.get("agent_name", "Unknown")
        if agent_name not in agent_activity:
            agent_activity[agent_name] = 0
        agent_activity[agent_name] += 1

        if "on_message_ready" in ui_callbacks:
            ui_callbacks["on_message_ready"](frontend_message)

        if frontend_message.get("type") == "tool" and terminal_ui:
            try:
                tool_name = frontend_message.get("tool_display_name", "Tool")
                content = frontend_message.get("content", "")

                if tool_name and content:

                    terminal_ui.add_command(tool_name)
                    terminal_ui.add_output(content)

                    if st.session_state.get("debug_mode", False):
                        print(f"Terminal direct update: {tool_name} -> {content[:100]}...")

            except Exception as e:
                if st.session_state.get("debug_mode", False):
                    print(f"Terminal direct update error: {e}")

        elif frontend_message.get("type") == "tool":
            self._process_terminal_message_logic(frontend_message, ui_callbacks)

        return True

    def _process_terminal_message_logic(
        self,
        frontend_message: Dict[str, Any],
        ui_callbacks: Dict[str, Callable]
    ):

        if "terminal_messages" not in st.session_state:
            st.session_state.terminal_messages = []

        st.session_state.terminal_messages.append(frontend_message)

        if "on_terminal_message" in ui_callbacks:
            tool_name = frontend_message.get("tool_display_name", "Tool")
            content = frontend_message.get("content", "")

            if tool_name and content:
                ui_callbacks["on_terminal_message"](tool_name, content)

    def _log_message_event(self, event: Dict[str, Any], frontend_message: Dict[str, Any]):

        if "logger" not in st.session_state or not st.session_state.logger:
            return

        logger = st.session_state.logger
        agent_name = event.get("agent_name", "Unknown")
        message_type = event.get("message_type", "unknown")
        content = event.get("content", "")

        if message_type == "ai":
            logger.log_agent_response(
                agent_name=agent_name,
                content=content,
                tool_calls=frontend_message.get("tool_calls")
            )
        elif message_type == "tool":
            tool_name = event.get("tool_name", "Unknown Tool")
            if "command" in event:
                logger.log_tool_command(
                    tool_name=tool_name,
                    command=event.get("command", content)
                )
            else:
                logger.log_tool_output(
                    tool_name=tool_name,
                    output=content
                )

    def _update_agent_status_logic(self):

        active_agent = None
        for event in reversed(st.session_state.event_history):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    active_agent = agent_name.lower()
                    break

        if active_agent and active_agent != st.session_state.active_agent:
            if st.session_state.active_agent and st.session_state.active_agent not in st.session_state.completed_agents:
                st.session_state.completed_agents.append(st.session_state.active_agent)

            st.session_state.active_agent = active_agent

        if st.session_state.get("keep_initial_ui", True) and (
            st.session_state.active_agent or st.session_state.completed_agents
        ):
            st.session_state.keep_initial_ui = False

    def get_agent_status(self) -> Dict[str, Any]:

        return {
            "active_agent": st.session_state.active_agent,
            "completed_agents": st.session_state.completed_agents,
            "keep_initial_ui": st.session_state.get("keep_initial_ui", True)
        }

_workflow_handler = None

def get_workflow_handler() -> WorkflowHandler:

    global _workflow_handler
    if _workflow_handler is None:
        _workflow_handler = WorkflowHandler()
    return _workflow_handler