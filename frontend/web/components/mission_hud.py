import streamlit as st
from typing import List, Dict, Any


class MissionHUDComponent:
    """
    A high-tech floating HUD component for Decepticon that displays
    agent status and mission data with animations.
    """

    def render(self, agent_states: List[Dict[str, Any]]):
        """
        Renders the HUD overlay.
        """
        hud_html = self._generate_hud_html(agent_states)
        st.components.v1.html(hud_html, height=150, scrolling=False)

    def _generate_hud_html(self, agent_states: List[Dict[str, Any]]) -> str:
        # Generate the high-tech HUD using HTML/CSS
        # Includes pulsing animations and glowing borders
        items_html = ""
        for agent in agent_states:
            status_class = f"status-{agent.get('status', 'waiting')}"
            items_html += f"""
                <div class="hud-agent {status_class}">
                    <div class="agent-label">{agent.get("name", "UNKNOWN")}</div>
                    <div class="agent-indicator"></div>
                </div>
            """

        return f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@400;700&family=Rajdhani:wght@400;700&display=swap');
            
            :root {{
                --slate-950: #020617;
                --slate-900: #0f172a;
                --cyber-blue: #38bdf8;
                --cyber-green: #10b981;
                --cyber-red: #ef4444;
                --slate-400: #94a3b8;
            }}

            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: 'Orbitron', 'Rajdhani', sans-serif;
                overflow: hidden;
            }}

            .hud-container {{
                display: flex;
                gap: 15px;
                padding: 10px;
                justify-content: center;
                perspective: 1000px;
            }}

            .hud-agent {{
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.2);
                padding: 10px 20px;
                min-width: 120px;
                text-align: center;
                position: relative;
                transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                backdrop-filter: blur(8px);
                border-radius: 0; /* Sharp Brutalist edges */
                clip-path: polygon(0 0, 100% 0, 100% 70%, 85% 100%, 0 100%);
            }}

            .agent-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: var(--slate-400);
                margin-bottom: 5px;
            }}

            .agent-indicator {{
                height: 3px;
                width: 100%;
                background: rgba(148, 163, 184, 0.2);
                position: relative;
                overflow: hidden;
            }}

            /* Active State */
            .hud-agent.status-active {{
                border-color: var(--cyber-blue);
                background: rgba(56, 189, 248, 0.1);
                transform: translateZ(20px);
                box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
            }}

            .hud-agent.status-active .agent-label {{
                color: var(--cyber-blue);
                font-weight: bold;
                text-shadow: 0 0 5px var(--cyber-blue);
            }}

            .hud-agent.status-active .agent-indicator::after {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: var(--cyber-blue);
                animation: scan 1.5s infinite linear;
            }}

            /* Completed State */
            .hud-agent.status-completed {{
                border-color: rgba(148, 163, 184, 0.5);
                opacity: 0.6;
            }}
            
            .hud-agent.status-completed .agent-indicator {{
                background: var(--slate-400);
            }}

            @keyframes scan {{
                0% {{ left: -100%; }}
                100% {{ left: 100%; }}
            }}

            @keyframes pulse {{
                0% {{ opacity: 0.4; }}
                50% {{ opacity: 1; }}
                100% {{ opacity: 0.4; }}
            }}
        </style>
        <div class="hud-container">
            {items_html}
        </div>
        """
