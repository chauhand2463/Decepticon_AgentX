"""
DECEPTICON — Nmap MCP Server
Wraps nmap with structured JSON output for the Recon Agent.

Install: pip install mcp
Run:     python mcp_servers/nmap_server.py
"""

import asyncio
import json
import subprocess
import shlex
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("decepticon-nmap")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def run_command(cmd: str, timeout: int = 300) -> dict:
    """Run a shell command and return stdout, stderr, returncode."""
    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Command timed out after {timeout}s", "returncode": -1, "success": False}
    except FileNotFoundError:
        return {"stdout": "", "stderr": "nmap not found. Install with: apt install nmap", "returncode": -1, "success": False}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}


def parse_nmap_xml(xml_output: str) -> dict:
    """Parse nmap XML output into structured dict."""
    try:
        root = ET.fromstring(xml_output)
        results = {"hosts": []}

        for host in root.findall("host"):
            host_data = {"status": "", "addresses": [], "ports": [], "os": [], "scripts": []}

            # Status
            status = host.find("status")
            if status is not None:
                host_data["status"] = status.get("state", "unknown")

            # Addresses
            for addr in host.findall("address"):
                host_data["addresses"].append({
                    "addr": addr.get("addr"),
                    "addrtype": addr.get("addrtype")
                })

            # Ports
            ports_el = host.find("ports")
            if ports_el is not None:
                for port in ports_el.findall("port"):
                    port_data = {
                        "portid": port.get("portid"),
                        "protocol": port.get("protocol"),
                        "state": "",
                        "service": {},
                        "scripts": []
                    }
                    state_el = port.find("state")
                    if state_el is not None:
                        port_data["state"] = state_el.get("state")

                    svc = port.find("service")
                    if svc is not None:
                        port_data["service"] = {
                            "name": svc.get("name", ""),
                            "product": svc.get("product", ""),
                            "version": svc.get("version", ""),
                            "extrainfo": svc.get("extrainfo", ""),
                            "tunnel": svc.get("tunnel", ""),
                            "cpe": [c.text for c in svc.findall("cpe")]
                        }

                    for script in port.findall("script"):
                        port_data["scripts"].append({
                            "id": script.get("id"),
                            "output": script.get("output", "")
                        })

                    host_data["ports"].append(port_data)

            # OS detection
            os_el = host.find("os")
            if os_el is not None:
                for match in os_el.findall("osmatch"):
                    host_data["os"].append({
                        "name": match.get("name"),
                        "accuracy": match.get("accuracy"),
                        "osfamily": match.find(".//osclass").get("osfamily", "") if match.find(".//osclass") is not None else ""
                    })

            results["hosts"].append(host_data)

        return results
    except ET.ParseError:
        return {"error": "Failed to parse XML output", "raw": xml_output[:500]}


# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="nmap_full_port_scan",
            description=(
                "Scan ALL 65535 TCP ports on a target. "
                "Returns list of open ports for further analysis. "
                "Use this FIRST before any other nmap scan."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "IP address, hostname, or CIDR range (e.g. 192.168.1.1 or 10.0.0.0/24)"
                    },
                    "rate": {
                        "type": "integer",
                        "description": "Packet rate limit (default 1000, reduce for stealth)",
                        "default": 1000
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Scan timeout in seconds (default 300)",
                        "default": 300
                    }
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="nmap_service_scan",
            description=(
                "Detect service names and versions on specific ports. "
                "Run AFTER nmap_full_port_scan. Pass the open ports from that scan. "
                "Returns service versions and banners for vulnerability research."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target IP or hostname"},
                    "ports": {
                        "type": "string",
                        "description": "Comma-separated port list (e.g. '22,80,443,8080')"
                    },
                    "timeout": {"type": "integer", "default": 300}
                },
                "required": ["target", "ports"]
            }
        ),
        types.Tool(
            name="nmap_vuln_scan",
            description=(
                "Run nmap NSE vulnerability scripts against specific ports. "
                "Detects known CVEs and common misconfigurations using built-in scripts. "
                "Run AFTER service scan to target correctly."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "ports": {"type": "string", "description": "Ports to scan (e.g. '80,443,22')"},
                    "timeout": {"type": "integer", "default": 300}
                },
                "required": ["target", "ports"]
            }
        ),
        types.Tool(
            name="nmap_os_detection",
            description=(
                "Attempt OS fingerprinting on the target. "
                "Returns OS family, version guess, and confidence level."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "ports": {"type": "string", "description": "Open ports to assist OS detection"},
                    "timeout": {"type": "integer", "default": 120}
                },
                "required": ["target", "ports"]
            }
        ),
        types.Tool(
            name="nmap_custom",
            description=(
                "Run a fully custom nmap command. "
                "Use when you need specific NSE scripts or non-standard options. "
                "Always include -oX - for structured XML output."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Full nmap command (e.g. 'nmap -sV --script=ssh-auth-methods -p 22 192.168.1.1')"
                    },
                    "timeout": {"type": "integer", "default": 300}
                },
                "required": ["command"]
            }
        )
    ]


# ─────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── FULL PORT SCAN ──────────────────────────────────────────────────
    if name == "nmap_full_port_scan":
        target = arguments["target"]
        rate   = arguments.get("rate", 1000)
        timeout = arguments.get("timeout", 300)

        cmd = f"nmap -p- --min-rate={rate} -T4 --open -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {
                "tool": "nmap_full_port_scan",
                "target": target,
                "success": False,
                "error": raw["stderr"],
                "command": cmd
            }
        else:
            parsed = parse_nmap_xml(raw["stdout"])
            open_ports = []
            for host in parsed.get("hosts", []):
                for port in host.get("ports", []):
                    if port["state"] == "open":
                        open_ports.append(port["portid"])

            result = {
                "tool": "nmap_full_port_scan",
                "target": target,
                "success": True,
                "command": cmd,
                "timestamp": datetime.now().isoformat(),
                "open_ports": open_ports,
                "open_ports_string": ",".join(open_ports),
                "host_count": len(parsed.get("hosts", [])),
                "raw_parsed": parsed
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── SERVICE SCAN ────────────────────────────────────────────────────
    elif name == "nmap_service_scan":
        target  = arguments["target"]
        ports   = arguments["ports"]
        timeout = arguments.get("timeout", 300)

        cmd = f"nmap -sV -sC -p{ports} -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {"tool": "nmap_service_scan", "target": target, "success": False,
                      "error": raw["stderr"], "command": cmd}
        else:
            parsed = parse_nmap_xml(raw["stdout"])
            services = []
            for host in parsed.get("hosts", []):
                for port in host.get("ports", []):
                    if port["state"] == "open":
                        svc = port.get("service", {})
                        services.append({
                            "port": port["portid"],
                            "protocol": port["protocol"],
                            "service": svc.get("name", "unknown"),
                            "product": svc.get("product", ""),
                            "version": svc.get("version", ""),
                            "extra": svc.get("extrainfo", ""),
                            "cpe": svc.get("cpe", []),
                            "scripts": port.get("scripts", [])
                        })

            result = {
                "tool": "nmap_service_scan",
                "target": target,
                "success": True,
                "command": cmd,
                "timestamp": datetime.now().isoformat(),
                "services": services,
                "service_count": len(services)
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── VULN SCAN ───────────────────────────────────────────────────────
    elif name == "nmap_vuln_scan":
        target  = arguments["target"]
        ports   = arguments["ports"]
        timeout = arguments.get("timeout", 300)

        cmd = f"nmap --script=vuln -p{ports} -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {"tool": "nmap_vuln_scan", "target": target, "success": False,
                      "error": raw["stderr"], "command": cmd}
        else:
            parsed = parse_nmap_xml(raw["stdout"])
            vuln_findings = []
            for host in parsed.get("hosts", []):
                for port in host.get("ports", []):
                    for script in port.get("scripts", []):
                        if "VULNERABLE" in script.get("output", "").upper() or \
                           "CVE" in script.get("output", "").upper():
                            vuln_findings.append({
                                "port": port["portid"],
                                "script": script["id"],
                                "output": script["output"]
                            })

            result = {
                "tool": "nmap_vuln_scan",
                "target": target,
                "success": True,
                "command": cmd,
                "timestamp": datetime.now().isoformat(),
                "vulnerability_hits": vuln_findings,
                "vuln_count": len(vuln_findings),
                "raw_parsed": parsed
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── OS DETECTION ────────────────────────────────────────────────────
    elif name == "nmap_os_detection":
        target  = arguments["target"]
        ports   = arguments["ports"]
        timeout = arguments.get("timeout", 120)

        cmd = f"nmap -O -p{ports} -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {"tool": "nmap_os_detection", "target": target, "success": False,
                      "error": raw["stderr"], "command": cmd}
        else:
            parsed = parse_nmap_xml(raw["stdout"])
            os_results = []
            for host in parsed.get("hosts", []):
                os_results.extend(host.get("os", []))

            result = {
                "tool": "nmap_os_detection",
                "target": target,
                "success": True,
                "command": cmd,
                "timestamp": datetime.now().isoformat(),
                "os_matches": os_results,
                "best_guess": os_results[0] if os_results else None
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── CUSTOM ──────────────────────────────────────────────────────────
    elif name == "nmap_custom":
        command = arguments["command"]
        timeout = arguments.get("timeout", 300)

        # Safety check — block obviously dangerous flags
        blocked = ["--script=broadcast", "--send-eth", "--unprivileged"]
        for b in blocked:
            if b in command:
                return [types.TextContent(type="text", text=json.dumps({
                    "error": f"Blocked flag detected: {b}",
                    "success": False
                }))]

        # Ensure XML output
        if "-oX" not in command:
            command += " -oX -"

        raw = run_command(command, timeout)
        parsed = parse_nmap_xml(raw["stdout"]) if raw["success"] else {}

        result = {
            "tool": "nmap_custom",
            "command": command,
            "success": raw["success"],
            "timestamp": datetime.now().isoformat(),
            "parsed": parsed,
            "stderr": raw["stderr"] if not raw["success"] else ""
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
