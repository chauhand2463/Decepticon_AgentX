import json
import os
from pathlib import Path

def load_mcp_config() -> dict:
    """Robustly load mcp_config.json with support for // comments (JSONC)."""
    # config_path = Path(__file__).parent.parent.parent.parent / "files" / "mcp_config.json"
    # Actually, the user's example shows it in the root or a standard location.
    # Let's check potential paths.
    
    # Check project root first (based on the common structure)
    current_dir = Path(__file__).parent
    potential_paths = [
        current_dir.parent.parent.parent / "files" / "mcp_config.json",
        current_dir.parent.parent.parent / "mcp_config.json",
        Path(os.getcwd()) / "files" / "mcp_config.json",
        Path(os.getcwd()) / "mcp_config.json"
    ]
    
    config_path = None
    for p in potential_paths:
        if p.exists():
            config_path = p
            break
            
    if not config_path:
        print(f" [WARN] could not find mcp_config.json in any standard location.")
        return {}

    with open(config_path, "r") as f:
        content = f.read()
        
    # Strip // style comments (JSONC support)
    lines = []
    for line in content.splitlines():
        # Handle cases where // might be inside a URL string
        # A simple check: if line starts with // or a trimmed line starts with //
        if not line.strip().startswith("//"):
            lines.append(line)
    
    clean_json = "\n".join(lines)
    try:
        return json.loads(clean_json)
    except json.JSONDecodeError as e:
        print(f" [ERROR] Failed to parse mcp_config.json: {e}")
        return {}
