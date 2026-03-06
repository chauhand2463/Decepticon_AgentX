

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

            override_css = self._generate_theme_overrides(colors, theme)
            st.markdown(override_css, unsafe_allow_html=True)

            self._load_additional_css_files()

    def _get_theme_colors(self, theme: str) -> Dict[str, str]:

        if theme == "dark":
            return {
                "sidebar_bg": "
                "sidebar_text": "
                "toggle_bg": "
                "toggle_text": "
                "toggle_border": "rgba(255, 255, 255, 0.2)",
                "button_bg": "
                "button_text": "
                "button_border": "
                "button_hover_bg": "
                "button_hover_text": "
                "button_active_bg": "
                "button_active_text": "
                "agent_bg": "linear-gradient(to right,
                "agent_border": "transparent",
                "agent_text": "
                "agent_hover_bg": "linear-gradient(to right,
                "active_bg": "linear-gradient(to right,
                "active_border": "
                "active_shadow": "rgba(255, 75, 75, 0.9)",
                "active_text_shadow": "rgba(255, 75, 75, 0.8)",
                "completed_bg": "linear-gradient(to right,
                "completed_border": "
                "header_text": "
                "header_border": "rgba(255, 255, 255, 0.1)",
                "message_bg": "rgba(45, 45, 45, 0.5)",
                "terminal_bg": "
                "terminal_text": "
                "terminal_header_bg": "
                "terminal_header_text": "
                "terminal_prompt": "
                "terminal_command": "
                "terminal_output": "
                "terminal_cursor": "
                "terminal_shadow": "rgba(0, 0, 0, 0.5)",
                "chat_container_bg": "
                "chat_input_bg": "
                "chat_input_text": "
                "chat_border": "
            }
        else:
            return {
                "sidebar_bg": "
                "sidebar_text": "
                "toggle_bg": "
                "toggle_text": "
                "toggle_border": "rgba(49, 51, 63, 0.2)",
                "button_bg": "
                "button_text": "
                "button_border": "
                "button_hover_bg": "
                "button_hover_text": "
                "button_active_bg": "
                "button_active_text": "
                "agent_bg": "linear-gradient(to right,
                "agent_border": "
                "agent_text": "
                "agent_hover_bg": "linear-gradient(to right,
                "active_bg": "linear-gradient(to right,
                "active_border": "
                "active_shadow": "rgba(255, 75, 75, 0.6)",
                "active_text_shadow": "rgba(255, 75, 75, 0.4)",
                "completed_bg": "linear-gradient(to right,
                "completed_border": "
                "header_text": "
                "header_border": "rgba(0, 0, 0, 0.1)",
                "message_bg": "rgba(240, 242, 246, 0.5)",
                "terminal_bg": "
                "terminal_text": "
                "terminal_header_bg": "
                "terminal_header_text": "
                "terminal_prompt": "
                "terminal_command": "
                "terminal_output": "
                "terminal_cursor": "
                "terminal_shadow": "rgba(0, 0, 0, 0.1)",
                "chat_container_bg": "
                "chat_input_bg": "
                "chat_input_text": "
                "chat_border": "
            }

    def _generate_theme_overrides(self, colors: Dict[str, str], theme: str) -> str:

        animation_name = "pulse-button-dark" if theme == "dark" else "pulse-button-light"

        return f

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

        st.markdown(f, unsafe_allow_html=True)

    def apply_page_theme(self, theme: str = "dark"):

        st.set_page_config(
            page_title="DECEPTICON",
            page_icon="assets/logo.png",
            layout="wide"
        )

        self.apply_theme_css(theme)