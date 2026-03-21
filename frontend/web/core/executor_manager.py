import streamlit as st
from typing import Optional, Dict, Any
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from frontend.web.core.executor import Executor
from src.utils.logging.logger import get_logger


class ExecutorManager:
    def __init__(self):

        self.executor = None
        self._ensure_executor()

    def _ensure_executor(self):

        if (
            "direct_executor" not in st.session_state
            or st.session_state.direct_executor is None
        ):
            st.session_state.direct_executor = Executor()

        self.executor = st.session_state.direct_executor

    def is_ready(self) -> bool:

        self._ensure_executor()
        return self.executor.is_ready() if self.executor else False

    async def initialize_with_model(self, model_info: Dict[str, Any]) -> bool:

        try:
            if "logger" not in st.session_state or st.session_state.logger is None:
                st.session_state.logger = get_logger()

            model_display_name = model_info.get("display_name", "Unknown Model")
            session_id = st.session_state.logger.start_session(model_display_name)
            st.session_state.logging_session_id = session_id

            self._ensure_executor()
            await self.executor.initialize_swarm(model_info)

            st.session_state.current_model = model_info
            st.session_state.executor_ready = True
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = None

            return True

        except Exception as e:
            error_msg = f"Failed to initialize AI agents: {str(e)}"

            st.session_state.executor_ready = False
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = error_msg

            return False

    async def initialize_default(self) -> bool:

        try:
            if "logger" not in st.session_state or st.session_state.logger is None:
                st.session_state.logger = get_logger()

            self._ensure_executor()
            await self.executor.initialize_swarm()

            st.session_state.executor_ready = True
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = None

            return True

        except Exception as e:
            error_msg = f"Failed to initialize AI agents: {str(e)}"

            st.session_state.executor_ready = False
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = error_msg

            return False

    def reset(self):

        st.session_state.direct_executor = Executor()
        self.executor = st.session_state.direct_executor
        st.session_state.executor_ready = False

    def get_executor(self) -> Optional[Executor]:

        self._ensure_executor()
        return self.executor

    async def execute_workflow(self, user_input: str, config: Dict[str, Any]):

        if not self.is_ready():
            raise RuntimeError("Executor not ready")

        if "logger" in st.session_state and st.session_state.logger:
            st.session_state.logger.log_user_input(user_input)

        async for event in self.executor.execute_workflow(user_input, config=config):
            yield event


_executor_manager = None


def get_executor_manager() -> ExecutorManager:

    global _executor_manager
    if _executor_manager is None:
        _executor_manager = ExecutorManager()
    return _executor_manager
