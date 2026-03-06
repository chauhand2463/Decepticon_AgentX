

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
                "sidebar_bg": "#0B0B12",
                "sidebar_text": "#FAFAFA",
                "toggle_bg": "#262730",
                "toggle_text": "#FAFAFA",
                "toggle_border": "rgba(255, 255, 255, 0.2)",
                "button_bg": "#262730",
                "button_text": "#FAFAFA",
                "button_border": "#404040",
                "button_hover_bg": "#404040",
                "button_hover_text": "#FFFFFF",
                "button_active_bg": "#FF4B4B",
                "button_active_text": "#FFFFFF",
                "agent_bg": "linear-gradient(to right, #222222, #2d2d2d, #222222)",
                "agent_border": "transparent",
                "agent_text": "#f0f0f0",
                "agent_hover_bg": "linear-gradient(to right, #262626, #323232, #262626)",
                "active_bg": "linear-gradient(to right, #3a1515, #4a1f1f, #3a1515)",
                "active_border": "#ff4b4b",
                "active_shadow": "rgba(255, 75, 75, 0.9)",
                "active_text_shadow": "rgba(255, 75, 75, 0.8)",
                "completed_bg": "linear-gradient(to right, #152315, #1e3a1e, #152315)",
                "completed_border": "#4CAF50",
                "header_text": "#f0f0f0",
                "header_border": "rgba(255, 255, 255, 0.1)",
                "message_bg": "rgba(45, 45, 45, 0.5)",
                "terminal_bg": "#1E1E1E",
                "terminal_text": "#FFFFFF",
                "terminal_header_bg": "#333333",
                "terminal_header_text": "#FFFFFF",
                "terminal_prompt": "#4EC9B0",
                "terminal_command": "#DCDCAA",
                "terminal_output": "#CCCCCC",
                "terminal_cursor": "#FFFFFF",
                "terminal_shadow": "rgba(0, 0, 0, 0.5)",
                "chat_container_bg": "#0e1117",
                "chat_input_bg": "#262730",
                "chat_input_text": "#FAFAFA",
                "chat_border": "#404040"
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

        animation_name = "pulse-button-dark" if theme == "dark" else "pulse-button-light"

        return f"""
        <style>
        @keyframes {animation_name} {{
            0% {{ box-shadow: 0 0 0 0 {colors['active_shadow']}; }}
            70% {{ box-shadow: 0 0 0 10px rgba(0, 0, 0, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }}
        }}
        </style>
        """

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