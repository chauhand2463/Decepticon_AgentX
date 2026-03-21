import json
import os
import re
from pathlib import Path


def load_mcp_config() -> dict:
    """
    Robustly load mcp_config.json.
    Searches several candidate paths so it works whether the process is
    started from the project root, a sub-directory, or the frontend folder.
    Supports // single-line comments (JSONC) so developers can annotate the file.
    """
    # FIX: original logic checked paths in a fixed order that could miss the file
    # when the working directory differed from the script location.
    # Now we build candidates from __file__ (reliable) AND os.getcwd() (fallback).

    script_dir = Path(__file__).resolve().parent  # src/utils/mcp/
    project_root_from_file = script_dir.parent.parent.parent  # three levels up

    candidates = [
        # Most likely: alongside pyproject.toml / langgraph.json
        project_root_from_file / "mcp_config.json",
        # Legacy location used in files/
        project_root_from_file / "files" / "mcp_config.json",
        # CWD-based fallbacks (useful when running pytest from project root)
        Path(os.getcwd()) / "mcp_config.json",
        Path(os.getcwd()) / "files" / "mcp_config.json",
    ]

    config_path = None
    for p in candidates:
        if p.exists():
            config_path = p
            break

    if not config_path:
        print(
            "[WARN] mcp_config.json not found in any of the following locations:\n"
            + "\n".join(f"  {c}" for c in candidates)
        )
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip // style single-line comments (JSONC support)
    # Guard: don't strip lines where // is inside a string value (e.g. URLs).
    # A simple heuristic: only strip when // appears outside of double-quoted strings.
    def strip_line_comments(text: str) -> str:
        lines = []
        for line in text.splitlines():
            # Remove inline // comments that are not inside strings
            result = re.sub(r'(?<!:)//(?![^"]*"[^"]*(?:"[^"]*"[^"]*)*$).*', "", line)
            lines.append(result)
        return "\n".join(lines)

    clean_json = strip_line_comments(content)

    try:
        return json.loads(clean_json)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse mcp_config.json: {e}")
        return {}
