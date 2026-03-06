

import streamlit as st
import asyncio
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from frontend.web.utils.float import float_init

from frontend.web.components.chat_messages import ChatMessagesComponent
from frontend.web.components.terminal_ui import TerminalUIComponent
from frontend.web.components.sidebar import SidebarComponent
from frontend.web.components.theme_ui import ThemeUIComponent

from frontend.web.core.app_state import get_app_state_manager
from frontend.web.core.executor_manager import get_executor_manager
from frontend.web.core.workflow_handler import get_workflow_handler
from frontend.web.core.terminal_processor import get_terminal_processor

from frontend.web.utils.validation import check_model_required
from frontend.web.utils.constants import ICON, ICON_TEXT, COMPANY_LINK

from frontend.web.core.chat_replay import ReplayManager

app_state = get_app_state_manager()
executor_manager = get_executor_manager()
workflow_handler = get_workflow_handler()
terminal_processor = get_terminal_processor()

theme_ui = ThemeUIComponent()
chat_messages = ChatMessagesComponent()
terminal_ui = TerminalUIComponent()
sidebar = SidebarComponent()

def main():

    try:
        app_state._initialize_session_state()
        app_state._initialize_user_session()
        app_state._initialize_logging()
    except Exception as e:
        st.error(f"앱 상태 초기화 오류: {str(e)}")
        return

    if not check_model_required():
        _show_model_required_message()
        return

    current_theme = "dark" if st.session_state.get('dark_mode', True) else "light"
    theme_ui.apply_theme_css(current_theme)
    float_init()
    terminal_ui.apply_terminal_css()

    st.logo(ICON_TEXT, icon_image=ICON, size="large", link=COMPANY_LINK)

    st.title(":red[DECEPTICON]")

    _setup_sidebar()

    replay_manager = ReplayManager()
    if replay_manager.is_replay_mode():
        _handle_replay_mode(replay_manager)
        return

    _display_main_interface()

def _show_model_required_message():

    st.warning("⚠️ Please select a model first")
    if st.button("Go to Model Selection", type="primary"):
        st.switch_page("streamlit_app.py")

def _setup_sidebar():

    callbacks = {
        "on_change_model": lambda: st.switch_page("streamlit_app.py"),
        "on_chat_history": lambda: st.switch_page("pages/02_Chat_History.py"),
        "on_new_chat": _create_new_chat,
        "on_debug_mode_change": app_state.set_debug_mode
    }

    try:
        current_model = st.session_state.get('current_model')
        active_agent = st.session_state.get('active_agent')
        completed_agents = st.session_state.get('completed_agents', [])
        session_stats = app_state.get_session_stats()
        debug_info = app_state.get_debug_info()
    except Exception as e:
        st.error(f"사이드바 데이터 로드 오류: {str(e)}")

        current_model = None
        active_agent = None
        completed_agents = []
        session_stats = {"messages_count": 0, "events_count": 0, "steps_count": 0, "elapsed_time": 0, "active_agent": None, "completed_agents_count": 0}
        debug_info = {"user_id": "Error", "thread_id": "Error", "executor_ready": False, "workflow_running": False}

    sidebar.render_complete_sidebar(
        model_info=current_model,
        active_agent=active_agent,
        completed_agents=completed_agents,
        session_stats=session_stats,
        debug_info=debug_info,
        callbacks=callbacks
    )

def _display_main_interface():

    if "terminal_visible" not in st.session_state:
        st.session_state.terminal_visible = True

    terminal_processor.initialize_terminal_state()

    chat_height = app_state.get_env_config().get("chat_height", 700)
    chat_container = st.container(height=chat_height, border=False)

    with chat_container:
        messages_area = st.container()
        if not st.session_state.get('workflow_running', False):
            structured_messages = st.session_state.get('structured_messages', [])
            chat_messages.display_messages(structured_messages, messages_area)

    _handle_terminal_toggle()

    _render_floating_terminal()

    _handle_user_input(messages_area)

def _handle_terminal_toggle():

    toggle_clicked = terminal_ui.create_floating_toggle_button(st.session_state.terminal_visible)

    if toggle_clicked:

        st.session_state.terminal_visible = not st.session_state.terminal_visible

        st.rerun()

def _render_floating_terminal():

    if st.session_state.terminal_visible:
        terminal_history = terminal_processor.get_terminal_history()
        terminal_ui.create_floating_terminal(terminal_history)

def _handle_user_input(messages_area):

    user_input = st.chat_input("Type your red team request here...")

    if user_input and not st.session_state.get('workflow_running', False):

        async def execute_workflow():

            validation_result = workflow_handler.validate_execution_state()
            if not validation_result["can_execute"]:
                st.error(validation_result["errors"][0] if validation_result["errors"] else "Cannot execute workflow")
                return

            user_message = workflow_handler.prepare_user_input(user_input)

            with messages_area:
                chat_messages.display_user_message(user_message)

            ui_callbacks = {
                "on_message_ready": lambda msg: _display_message_callback(msg, messages_area),
                "on_terminal_message": _terminal_message_callback,
                "on_workflow_complete": lambda: None,
                "on_error": lambda error: st.error(f"Workflow error: {error}")
            }

            result = await workflow_handler.execute_workflow_logic(
                user_input, ui_callbacks, terminal_ui
            )

            if result["success"]:

                pass
            else:
                if result["error_message"]:
                    st.error(result["error_message"])

        asyncio.run(execute_workflow())

def _display_message_callback(message, messages_area):

    with messages_area:
        message_type = message.get("type", "")
        if message_type == "ai":
            chat_messages.display_agent_message(message, streaming=True)
        elif message_type == "tool":
            chat_messages.display_tool_message(message)

def _terminal_message_callback(tool_name, content):

    pass

def _create_new_chat():

    try:
        conversation_id = app_state.create_new_conversation()
        executor_manager.reset()

        current_model = st.session_state.get('current_model')
        if current_model:
            async def reinitialize():
                await executor_manager.initialize_with_model(current_model)
            asyncio.run(reinitialize())

        terminal_processor.clear_terminal_state()

        st.success("✨ New chat session started!")

    except Exception as e:
        st.error(f"Failed to create new chat: {str(e)}")

def _handle_replay_mode(replay_manager):

    float_init()
    terminal_ui.apply_terminal_css()

    if "terminal_visible" not in st.session_state:
        st.session_state.terminal_visible = True

    terminal_processor.initialize_terminal_state()

    chat_height = app_state.get_env_config().get("chat_height", 700)
    chat_container = st.container(height=chat_height, border=False)

    with chat_container:
        messages_area = st.container()

        replay_handled = replay_manager.handle_replay_in_main_app(
            messages_area, st.sidebar.container(), chat_messages, terminal_ui
        )

        if not replay_handled:

            st.error("재현에 실패했습니다. 세션 데이터를 찾을 수 없습니다.")

    _handle_terminal_toggle()

    _render_floating_terminal()

    if st.session_state.get("replay_completed", False):
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✨ Start New Chat", use_container_width=True, type="primary"):

                for key in ["replay_mode", "replay_session_id", "replay_completed"]:
                    st.session_state.pop(key, None)

                _create_new_chat()

if __name__ == "__main__":
    main()