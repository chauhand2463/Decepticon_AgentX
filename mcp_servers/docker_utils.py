import subprocess

CONTAINER_NAME = "attacker"


def run_in_container(cmd: str, timeout: int = 300) -> dict:
    """Run a command inside the attacker Docker container."""
    try:
        # Check if container is running
        check_cmd = [
            "docker",
            "ps",
            "--filter",
            f"name={CONTAINER_NAME}",
            "--format",
            "{{.Names}}",
        ]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if CONTAINER_NAME not in result.stdout:
            # Try to start it
            subprocess.run(["docker", "start", CONTAINER_NAME], capture_output=True)

        # Execute the command
        full_cmd = ["docker", "exec", CONTAINER_NAME, "sh", "-c", cmd]

        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=timeout
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1,
            "success": False,
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}
