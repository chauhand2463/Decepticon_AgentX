from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List
import subprocess
import uuid
import time
import os

mcp = FastMCP("terminal", port=3003)

CONTAINER_NAME = "attacker"

def run(command: List[str]) -> subprocess.CompletedProcess:

    return subprocess.run(
        ["docker", "exec", CONTAINER_NAME] + command,
        capture_output=True, text=True, encoding='utf-8'
    )

def tmux_run(command: List[str]) -> subprocess.CompletedProcess:

    return run(["tmux"] + command)

@mcp.tool(description="Create new terminal sessions")
def create_session(
    session_names: Annotated[List[str], "Session names to create"]
) -> Annotated[List[str], "List of created session names"]:

    created_sessions = []

    for session_name in session_names:
        result = tmux_run(["new-session", "-d", "-s", session_name])
        if result.returncode != 0:
            raise Exception(f"Failed to create session '{session_name}': {result.stderr}")
        created_sessions.append(session_name)

    return created_sessions

@mcp.tool(description="List all active sessions")
def session_list() -> Annotated[List[str], "List of session IDs"]:
    result = tmux_run(["list-sessions"])
    if result.returncode != 0:
        return []
    return [line.split(":")[0].strip() for line in result.stdout.strip().split('\n') if line.strip()]

@mcp.tool(description="Execute command in session")
def command_exec(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
) -> Annotated[str, "Command output"]:

    try:
        channel = f"done-{session_id}-{uuid.uuid4().hex[:8]}"
        timestamp = int(time.time())
        output_file = f"/tmp/cmd_output_{session_id}_{timestamp}.txt"
        status_file = f"/tmp/cmd_status_{session_id}_{timestamp}.txt"

        full_command = f"({command}) > {output_file} 2>&1; echo $? > {status_file}; tmux wait-for -S {channel}"

        result = tmux_run(["send-keys", "-t", session_id, full_command, "Enter"])
        if result.returncode != 0:
            raise Exception(f"Failed to execute command: {result.stderr}")

        wait_result = tmux_run(["wait-for", channel])
        if wait_result.returncode != 0:
            raise Exception(f"Command execution monitoring failed: {wait_result.stderr}")

        try:

            status_result = run(["cat", status_file])
            if status_result.returncode != 0:
                raise Exception(f"Failed to read status file: {status_result.stderr}")

            try:
                exit_code = int(status_result.stdout.strip())
            except ValueError:
                raise Exception(f"Invalid exit code: {status_result.stdout.strip()}")

            output_result = run(["cat", output_file])
            if output_result.returncode != 0:
                raise Exception(f"Failed to read output file: {output_result.stderr}")

            output = output_result.stdout

            run(["rm", "-f", output_file, status_file])

            if exit_code != 0:
                raise Exception(f"Command failed with exit code {exit_code}: {output.strip()}")

            return output.strip()

        except Exception as e:

            run(["rm", "-f", output_file, status_file])
            raise Exception(f"Failed to process command result: {str(e)}")

    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")

@mcp.tool(description="Kill terminal sessions")
def kill_session(
    session_names: Annotated[List[str], "Session names to kill"]
) -> Annotated[List[str], "Results for each session"]:

    results = []

    for session_name in session_names:
        try:
            result = tmux_run(["kill-session", "-t", session_name])
            if result.returncode == 0:
                results.append(f"Session {session_name} killed successfully")
            else:
                results.append(f"Session {session_name} killed (with warning: {result.stderr})")
        except Exception as e:
            results.append(f"Failed to kill session {session_name}: {str(e)}")

    return results

@mcp.tool(description="Kill server, Kill all session")
def kill_server() -> Annotated[str, "Result"]:
    try:
        tmux_run(["kill-server"])
        return f"Server killed"

    except Exception as e:
        return f"Server killed (with warning: {str(e)})"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")