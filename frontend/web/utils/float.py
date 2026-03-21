import streamlit as st
from typing import Optional


def float_init():
    """Initializes the floating capability by injecting necessary CSS and JS."""
    st.markdown(
        """
        <style>
        .st-float-container {
            position: fixed !important;
            z-index: 999999 !important;
            display: flex !important;
            flex-direction: column !important;
            pointer-events: auto !important;
            background: transparent !important;
        }
        </style>
        <script>
        function float_elements() {
            const containers = document.querySelectorAll('.st-float-container');
            containers.forEach(container => {
                // Find the parent streamlit element (the one that Streamlit actually controls)
                // and move it to the fixed container if not already there.
                let prev = container.previousElementSibling;
                if (prev && !prev.classList.contains('st-float-container')) {
                    // This is a simplified version of what streamlit-float does
                    // In a real scenario, we might need more complex logic to find the 'stElement'
                }
            });
        }
        // Run once
        float_elements();
        </script>
    """,
        unsafe_allow_html=True,
    )


def float_css_helper(
    width: str = "auto",
    height: str = "auto",
    top: Optional[str] = None,
    bottom: Optional[str] = None,
    left: Optional[str] = None,
    right: Optional[str] = None,
    background: str = "transparent",
    border: str = "none",
    border_radius: str = "0px",
    box_shadow: str = "none",
    z_index: str = "9999",
    padding: str = "0px",
    transition: str = "none",
) -> str:
    """Generates CSS string for a floating container."""
    styles = [
        f"width: {width} !important",
        f"height: {height} !important",
        f"background: {background} !important",
        f"border: {border} !important",
        f"border-radius: {border_radius} !important",
        f"box-shadow: {box_shadow} !important",
        f"z-index: {z_index} !important",
        f"padding: {padding} !important",
        f"transition: {transition} !important",
        "position: fixed !important",
        "display: flex !important",
        "flex-direction: column !important",
        "pointer-events: auto !important",
        "overflow: hidden !important",
    ]

    if top:
        styles.append(f"top: {top} !important")
    if bottom:
        styles.append(f"bottom: {bottom} !important")
    if left:
        styles.append(f"left: {left} !important")
    if right:
        styles.append(f"right: {right} !important")

    return "; ".join(styles)
