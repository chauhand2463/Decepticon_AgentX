

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from typing import Dict, Any, List, Optional
from frontend.web.utils.constants import (
    CSS_PATH_TERMINAL,
    CSS_CLASS_TERMINAL_CONTAINER,
    CSS_CLASS_MAC_TERMINAL_HEADER
)

class TerminalUIComponent:

    def __init__(self):

        self.placeholder = None

    def apply_terminal_css(self):

        try:
            with open(CSS_PATH_TERMINAL, "r", encoding="utf-8") as f:
                css = f.read()
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except Exception as e:
            print(f"Error loading terminal CSS: {e}")

    def create_terminal_header(self) -> str:

        return

    def create_terminal(self, container):

        container.markdown(self.create_terminal_header(), unsafe_allow_html=True)

        self.placeholder = container.empty()

        return self.placeholder

    def render_terminal_display(self, terminal_history: List[Dict[str, Any]]):

        if not self.placeholder:
            return

        terminal_content = ""
        for entry in terminal_history:
            entry_type = entry.get("type", "output")
            content = entry.get("content", "")

            if entry_type == "command":

                terminal_content += (
                    f'<div class="terminal-prompt">'
                    f'<span class="terminal-user">root@kali</span>'
                    f'<span class="terminal-prompt-text">:~$ </span>'
                    f'<span class="terminal-command-text">{content}</span>'
                    f'</div>'
                )
            elif entry_type == "output":
                terminal_content += f'<div class="terminal-output">{content}</div>'

        terminal_content += (
            '<div class="terminal-prompt">'
            '<span class="terminal-user">root@kali</span>'
            '<span class="terminal-prompt-text">:~$ </span>'
            '<span class="terminal-cursor"></span>'
            '</div>'
        )

        terminal_html = f

        self.placeholder.markdown(terminal_html, unsafe_allow_html=True)

    def display_command_entry(self, command: str, timestamp: str = None):

        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")

        st.markdown(
            f'<div class="terminal-prompt">'
            f'<span class="terminal-user">root@kali</span>'
            f'<span class="terminal-prompt-text">:~$ </span>'
            f'<span class="terminal-command-text">{command}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    def display_output_entry(self, output: str):

        st.markdown(
            f'<div class="terminal-output">{output}</div>',
            unsafe_allow_html=True
        )

    def create_floating_terminal(self, terminal_history: List[Dict[str, Any]]) -> st.container:

        from frontend.web.utils.float import float_css_helper

        terminal_container = st.container()

        with terminal_container:

            self.apply_terminal_css()

            st.markdown('<div class="terminal-wrapper">', unsafe_allow_html=True)

            self.create_terminal(st.container())

            self.render_terminal_display(terminal_history)

            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.get("debug_mode", False):
                st.write(f"Debug - terminal_history: {len(terminal_history)}")

        terminal_css = float_css_helper(
            width="350px",
            height="500px",
            right="40px",
            top="50%",
            transform="translateY(-50%)",
            z_index="1000",
            border_radius="12px",
            box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            backdrop_filter="blur(16px)",
            background="linear-gradient(145deg,
            border="1px solid
            max_height="500px",
            overflow_y="auto"
        )

        terminal_container.float(terminal_css)

        return terminal_container

    def create_floating_toggle_button(self, is_visible: bool) -> st.container:

        from frontend.web.utils.float import float_css_helper

        toggle_container = st.container()

        with toggle_container:

            if is_visible:
                button_text = "💻 Hide Terminal"
                button_type = "secondary"
            else:
                button_text = "💻 Show Terminal"
                button_type = "primary"

            if st.button(button_text, type=button_type, use_container_width=True):
                return True

        toggle_css = float_css_helper(
            width="140px",
            right="40px",
            bottom="20px",
            z_index="1001",
            border_radius="12px",
            box_shadow="0 8px 32px rgba(0,0,0,0.12)",
            backdrop_filter="blur(16px)",
            background="rgba(255, 255, 255, 0.9)"
        )

        toggle_container.float(toggle_css)

        return False

    def clear_terminal(self):

        if self.placeholder:
            self.placeholder.empty()

    def display_terminal_in_container(self, container, terminal_history: List[Dict[str, Any]]):

        with container:
            self.apply_terminal_css()

            st.markdown('<div class="terminal-wrapper">', unsafe_allow_html=True)
            placeholder = self.create_terminal(st.container())
            self.render_terminal_display(terminal_history)
            st.markdown('</div>', unsafe_allow_html=True)

    def show_terminal_loading(self, message: str = "Loading terminal..."):

        if self.placeholder:
            with self.placeholder:
                st.spinner(message)

    def show_terminal_error(self, error_msg: str):

        if self.placeholder:
            with self.placeholder:
                st.error(f"Terminal Error: {error_msg}")

    def process_structured_messages(self, messages: List[Dict[str, Any]]):

        try:
            from frontend.web.core.terminal_processor import get_terminal_processor
            terminal_processor = get_terminal_processor()

            terminal_processor.initialize_terminal_state()

            terminal_entries = terminal_processor.process_structured_messages(messages)

            if terminal_entries:
                terminal_processor.update_terminal_history(terminal_entries)

            if not hasattr(self, 'terminal_history'):
                self.terminal_history = []
            self.terminal_history = terminal_processor.get_terminal_history()

        except Exception as e:

            if not hasattr(self, 'terminal_history'):
                self.terminal_history = []
            print(f"Error processing structured messages: {e}")

def load_terminal_css():

    try:
        with open(CSS_PATH_TERMINAL, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        print(f"Warning: Could not load terminal.css: {e}")

def create_floating_terminal(terminal_ui_component, terminal_history: List[Dict[str, Any]]):

    return terminal_ui_component.create_floating_terminal(terminal_history)

def create_floating_toggle_button(terminal_ui_component, is_visible: bool):

    return terminal_ui_component.create_floating_toggle_button(is_visible)