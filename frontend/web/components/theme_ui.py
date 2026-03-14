

import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional, Callable

class ThemeUIComponent:

    def __init__(self):

        self.base_path = Path(__file__).parent
        while not (self.base_path / "pyproject.toml").exists() and self.base_path.parent != self.base_path:
            self.base_path = self.base_path.parent

        self.css_dir = self.base_path / "frontend" / "static" / "css"

    def load_theme_css(self, theme: str = "dark") -> str:

        css_file = self.css_dir / f"{theme}_theme.css"

        try:
            with open(css_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"테마 CSS 파일 로드 오류: {str(e)}")
            return ""

    def apply_theme_css(self, theme: str = "dark"):

        css = self.load_theme_css(theme)

        if css:

            colors = self._get_theme_colors(theme)

            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

            # Inject HUD Design Tokens
            tokens = {
                "hud_primary": colors['active_border'],
                "hud_bg": colors['agent_bg'],
                "hud_border": colors['agent_border'],
                "hud_text": colors['agent_text'],
                "chat_message_bg": colors['message_bg'],
                "chat_message_border": colors['chat_border'],
                "chat_message_text": colors['sidebar_text'],
                "chat_message_user_bg": "rgba(30, 41, 59, 0.4)",
                "chat_message_user_border": "rgba(148, 163, 184, 0.2)",
                "chat_message_user_text": "#f8fafc",
                "chat_message_assistant_bg": colors['message_bg'],
                "chat_message_assistant_border": colors['chat_border'],
                "chat_message_assistant_text": colors['sidebar_text'],
                "chat_message_active_border": colors['active_border'],
                "chat_message_active_shadow": colors['active_shadow'],
                "chat_message_completed_border": colors['completed_border'],
                "chat_message_completed_shadow": "none",
                "chat_message_error_border": "#ef4444",
                "chat_message_error_shadow": "rgba(239, 68, 68, 0.2)",
                "chat_message_warning_border": "#f59e0b",
                "chat_message_warning_shadow": "rgba(245, 158, 11, 0.2)"
            }
            self._apply_hud_design_tokens(tokens)

            override_css = self._generate_theme_overrides(colors, theme)
            st.markdown(override_css, unsafe_allow_html=True)

            self._load_additional_css_files()

    def _get_theme_colors(self, theme: str) -> Dict[str, str]:

        if theme == "dark":
            return {
                "sidebar_bg": "#0B0B12",
                "sidebar_text": "#FAFAFA",
                "toggle_bg": "#1e293b", # Slate-800
                "toggle_text": "#FAFAFA",
                "toggle_border": "rgba(255, 255, 255, 0.1)",
                "button_bg": "#1e293b",
                "button_text": "#FAFAFA",
                "button_border": "#334155", # Slate-700
                "button_hover_bg": "#334155",
                "button_hover_text": "#FFFFFF",
                "button_active_bg": "#ef4444", # Danger Red
                "button_active_text": "#FFFFFF",
                "agent_bg": "rgba(15, 23, 42, 0.8)", # Slate-900
                "agent_border": "rgba(148, 163, 184, 0.2)",
                "agent_text": "#94a3b8", # Slate-400
                "active_bg": "rgba(16, 185, 129, 0.1)", # Emerald
                "active_border": "#10b981", # Emerald
                "active_shadow": "rgba(16, 185, 129, 0.4)",
                "active_text_shadow": "rgba(16, 185, 129, 0.5)",
                "completed_bg": "rgba(30, 41, 59, 0.5)", # Slate-800
                "completed_border": "#475569", # Slate-600
                "header_text": "#f8fafc", # Slate-50
                "header_border": "rgba(255, 255, 255, 0.05)",
                "message_bg": "rgba(15, 23, 42, 0.6)",
                "terminal_bg": "#020617", # Slate-950
                "terminal_text": "#e2e8f0",
                "terminal_header_bg": "#0f172a",
                "terminal_header_text": "#94a3b8",
                "terminal_prompt": "#22c55e",
                "terminal_command": "#f59e0b",
                "terminal_output": "#94a3b8",
                "terminal_cursor": "#f8fafc",
                "terminal_shadow": "rgba(0, 0, 0, 0.5)",
                "chat_container_bg": "#020617",
                "chat_input_bg": "#0f172a",
                "chat_input_text": "#f8fafc",
                "chat_border": "#1e293b"
            }
        else:
            return {
                "sidebar_bg": "#FFFFFF",
                "sidebar_text": "#31333F",
                "toggle_bg": "#F0F2F6",
                "toggle_text": "#31333F",
                "toggle_border": "rgba(49, 51, 63, 0.2)",
                "button_bg": "#F0F2F6",
                "button_text": "#31333F",
                "button_border": "#DCDCDC",
                "button_hover_bg": "#E0E0E0",
                "button_hover_text": "#000000",
                "button_active_bg": "#FF4B4B",
                "button_active_text": "#FFFFFF",
                "agent_bg": "linear-gradient(to right, #F8F9FA, #E9ECEF, #F8F9FA)",
                "agent_border": "#DCDCDC",
                "agent_text": "#31333F",
                "agent_hover_bg": "linear-gradient(to right, #E9ECEF, #DEE2E6, #E9ECEF)",
                "active_bg": "linear-gradient(to right, #FFF5F5, #FFE3E3, #FFF5F5)",
                "active_border": "#FF4B4B",
                "active_shadow": "rgba(255, 75, 75, 0.6)",
                "active_text_shadow": "rgba(255, 75, 75, 0.4)",
                "completed_bg": "linear-gradient(to right, #F6FFF6, #E6FFE6, #F6FFF6)",
                "completed_border": "#4CAF50",
                "header_text": "#31333F",
                "header_border": "rgba(0, 0, 0, 0.1)",
                "message_bg": "rgba(240, 242, 246, 0.5)",
                "terminal_bg": "#F8F9FA",
                "terminal_text": "#31333F",
                "terminal_header_bg": "#E9ECEF",
                "terminal_header_text": "#31333F",
                "terminal_prompt": "#008080",
                "terminal_command": "#000080",
                "terminal_output": "#31333F",
                "terminal_cursor": "#31333F",
                "terminal_shadow": "rgba(0, 0, 0, 0.1)",
                "chat_container_bg": "#FFFFFF",
                "chat_input_bg": "#F0F2F6",
                "chat_input_text": "#31333F",
                "chat_border": "#DCDCDC"
            }

    def _generate_theme_overrides(self, colors: Dict[str, str], theme: str) -> str:
        """
        Generates tactical HUD overrides and staggered animations.
        """
        if theme != "dark":
            return ""

        return f"""
        <style>
        :root {{
            --hud-primary: {colors['active_border']};
            --hud-bg: {colors['agent_bg']};
            --hud-border: {colors['agent_border']};
            --hud-text: {colors['agent_text']};
        }}

        /* Staggered Reveal Animation */
        @keyframes reveal-staggered {{
            0% {{ opacity: 0; transform: translateY(10px); filter: blur(5px); }}
            100% {{ opacity: 1; transform: translateY(0); filter: blur(0); }}
        }}

        .stChatMessage {{
            animation: reveal-staggered 0.4s ease forwards;
            opacity: 0;
            border-radius: 0 !important;
            border-left: 2px solid transparent;
            transition: all 0.3s ease;
        }}

        /* Apply stagger delays to chat messages */
        .stChatMessage:nth-child(1) {{ animation-delay: 0.1s; }}
        .stChatMessage:nth-child(2) {{ animation-delay: 0.2s; }}
        .stChatMessage:nth-child(3) {{ animation-delay: 0.3s; }}
        .stChatMessage:nth-child(4) {{ animation-delay: 0.4s; }}
        .stChatMessage:nth-child(n+5) {{ animation-delay: 0.5s; }}

        /* HUD Pulse */
        @keyframes hud-pulse {{
            0% {{ border-color: rgba(16, 185, 129, 0.2); }}
            50% {{ border-color: rgba(16, 185, 129, 0.6); }}
            100% {{ border-color: rgba(16, 185, 129, 0.2); }}
        }}

        .agent-status.status-active {{
            animation: hud-pulse 2s infinite ease-in-out;
        }}
        
        /* Tactical HUD Scrollbar */
        ::-webkit-scrollbar {{
            width: 4px;
            height: 4px;
        }}
        ::-webkit-scrollbar-track {{
            background: #020617;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #1e293b;
            border-radius: 0;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #334155;
        }}
        </style>
        """

    def _apply_hud_design_tokens(self, colors: Dict[str, str]):
        """
        Applies HUD-style design tokens to Streamlit's CSS variables.
        """
        hud_tokens = f"""
        <style>
        :root {{
            /* General HUD */
            --hud-primary: {colors['hud_primary']};
            --hud-bg: {colors['hud_bg']};
            --hud-border: {colors['hud_border']};
            --hud-text: {colors['hud_text']};

            /* Chat Messages */
            --chat-message-bg: {colors['chat_message_bg']};
            --chat-message-border: {colors['chat_message_border']};
            --chat-message-text: {colors['chat_message_text']};
            --chat-message-user-bg: {colors['chat_message_user_bg']};
            --chat-message-user-border: {colors['chat_message_user_border']};
            --chat-message-user-text: {colors['chat_message_user_text']};
            --chat-message-assistant-bg: {colors['chat_message_assistant_bg']};
            --chat-message-assistant-border: {colors['chat_message_assistant_border']};
            --chat-message-assistant-text: {colors['chat_message_assistant_text']};
            --chat-message-active-border: {colors['chat_message_active_border']};
            --chat-message-active-shadow: {colors['chat_message_active_shadow']};
            --chat-message-completed-border: {colors['chat_message_completed_border']};
            --chat-message-completed-shadow: {colors['chat_message_completed_shadow']};
            --chat-message-error-border: {colors['chat_message_error_border']};
            --chat-message-error-shadow: {colors['chat_message_error_shadow']};
            --chat-message-warning-border: {colors['chat_message_warning_border']};
            --chat-message-warning-shadow: {colors['chat_message_warning_shadow']};
        }}
        </style>
        """
        st.markdown(hud_tokens, unsafe_allow_html=True)

    def _load_additional_css_files(self):

        css_files = [
            "layout.css",
            "model_info.css",
            "input_fix.css"
        ]

        for css_file in css_files:
            css_path = self.css_dir / css_file
            if css_path.exists():
                try:
                    with open(css_path, "r", encoding="utf-8") as f:
                        css = f.read()
                    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
                except Exception as e:
                    print(f"CSS 파일 로드 오류 ({css_file}): {e}")

    def create_theme_toggle(
        self,
        container=None,
        current_theme: str = "dark",
        callback: Optional[Callable] = None
    ) -> bool:

        if container is None:
            container = st

        theme_label = "🌙 Dark" if current_theme == "dark" else "☀️ Light"
        is_dark = current_theme == "dark"

        toggle_value = container.toggle(
            theme_label,
            value=is_dark,
            key="theme_toggle"
        )

        if toggle_value != is_dark:
            new_theme = "dark" if toggle_value else "light"

            if callback:
                callback(new_theme)

            return True

        return False

    def show_theme_preview(self, theme: str = "dark"):

        colors = self._get_theme_colors(theme)

        st.markdown(f"### Theme Preview: {theme.capitalize()}", unsafe_allow_html=True)

    def apply_page_theme(self, theme: str = "dark"):

        st.set_page_config(
            page_title="DECEPTICON",
            page_icon="assets/logo.png",
            layout="wide"
        )

        self.apply_theme_css(theme)