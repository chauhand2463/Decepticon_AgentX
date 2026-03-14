
import streamlit as st
from frontend.web.utils.float import float_css_helper

class TerminalUIComponent:
    def __init__(self):
        pass

    def apply_terminal_css(self):
        st.markdown("""
            <style>
            #terminal-body::-webkit-scrollbar {
                width: 8px;
            }
            #terminal-body::-webkit-scrollbar-track {
                background: #000;
            }
            #terminal-body::-webkit-scrollbar-thumb {
                background: #333;
                border-radius: 4px;
            }
            #terminal-body::-webkit-scrollbar-thumb:hover {
                background: #444;
            }
            .terminal-entry {
                margin-bottom: 5px;
                line-height: 1.4;
            }
            .terminal-command {
                color: #00ff00;
                font-weight: bold;
            }
            .terminal-output {
                color: #cccccc;
                white-space: pre-wrap;
            }
            .terminal-timestamp {
                color: #666;
                font-size: 0.7rem;
                margin-right: 8px;
            }
            </style>
        """, unsafe_allow_html=True)

    def create_floating_terminal(self, history):
        history_html = ""
        for entry in history:
            timestamp = entry.get("timestamp", "")
            type = entry.get("type", "output")
            content = entry.get("content", "")
            
            if type == "command":
                history_html += f'<div class="terminal-entry"><span class="terminal-timestamp">[{timestamp}]</span><span class="terminal-command">$ {content}</span></div>'
            else:
                history_html += f'<div class="terminal-entry"><span class="terminal-timestamp">[{timestamp}]</span><span class="terminal-output">{content}</span></div>'

        if not history_html:
            history_html = '<div style="color: #444; font-style: italic;">No terminal activity...</div>'

        terminal_html = f"""
        <div id="terminal-window" style="width: 100%; height: 100%; display: flex; flex-direction: column; color: #00ff00; font-family: 'Courier New', Courier, monospace; background: #000;">
            <div id="terminal-header" style="padding: 10px; background: #1a1a1a; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: bold; font-size: 0.8rem; letter-spacing: 1px;">TERMINAL - root@kali</div>
                <div style="display: flex; gap: 5px;">
                    <div style="width: 12px; height: 12px; border-radius: 50%; background: #ff5f56;"></div>
                    <div style="width: 12px; height: 12px; border-radius: 50%; background: #ffbd2e;"></div>
                    <div style="width: 12px; height: 12px; border-radius: 50%; background: #27c93f;"></div>
                </div>
            </div>
            <div id="terminal-body" style="flex-grow: 1; overflow-y: auto; padding: 15px; font-size: 0.85rem;">
                {history_html}
            </div>
        </div>
        """

        float_css = float_css_helper(
            width="800px",
            height="450px",
            bottom="100px",
            right="30px",
            background="rgba(10, 10, 10, 0.98)",
            border="1px solid #ff4b4b",
            border_radius="8px",
            box_shadow="0 20px 50px rgba(0,0,0,0.8)",
            z_index="99999",
            transition="all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
        )

        st.markdown(f"""
            <div class="st-float-container" style="{float_css}">
                {terminal_html}
            </div>
        """, unsafe_allow_html=True)

    def create_floating_toggle_button(self, is_visible: bool) -> bool:
        icon = "🐚" if is_visible else "🐚"
        text = "Hide Terminal" if is_visible else "Show Terminal"
        
        float_css = float_css_helper(
            width="180px",
            height="50px",
            bottom="30px",
            right="30px",
            background="#ff4b4b" if is_visible else "#222",
            border="none",
            border_radius="25px",
            box_shadow="0 8px 32px rgba(255, 75, 75, 0.3)" if is_visible else "0 8px 32px rgba(0, 0, 0, 0.3)",
            z_index="100000",
            transition="all 0.3s ease"
        )
        
        # We use a trick: the visual button is HTML, the actual click is a Streamlit button
        # hidden or positioned exactly over it.
        st.markdown(f"""
            <div class="st-float-container" style="{float_css}; pointer-events: none;">
                <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; gap: 8px;">
                    <span>{icon}</span> <span>{text}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # The real button that captures clicks
        # We place it in the same spot using a Streamlit container and the same float logic if possible
        # but Streamlit's st.button is harder to float without JS.
        # For now, we'll place it in the sidebar or a consistent spot.
        if st.sidebar.button(f"{'Hide' if is_visible else 'Show'} Terminal Shell", key="terminal_toggle_btn", use_container_width=True):
            return True
        return False