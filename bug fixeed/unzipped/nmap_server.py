"""
DECEPTICON — Nmap MCP Server
Wraps nmap with structured JSON output for the Recon Agent.

Install: pip install mcp
Run:     python mcp_servers/nmap_server.py
"""

import asyncio
import json
import os
import sys
# FIX: xml.etree.ElementTree was used in parse_nmap_xml but never imported
import xml.etree.ElementTree as ET
# FIX: datetime was used in tool implementations but never imported
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from docker_utils import run_in_container

app = Server("decepticon-recon")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def run_command(cmd: str, timeout: int = 300) -> dict:
    """Run a shell command inside the attacker container."""
    return run_in_container(cmd, timeout)


def parse_nmap_xml(xml_output: str) -> dict:
    """Parse nmap XML output into structured dict."""
    try:
        root = ET.fromstring(xml_output)
        results = {"hosts": []}

        for host in root.findall("host"):
            host_data = {
                "status": "",
                "addresses": [],
                "ports": [],
                "os": [],
                "scripts": [],
            }

            status = host.find("status")
            if status is not None:
                host_data["status"] = status.get("state", "unknown")

            for addr in host.findall("address"):
                host_data["addresses"].append(
                    {"addr": addr.get("addr"), "addrtype": addr.get("addrtype")}
                )

            ports_el = host.find("ports")
            if ports_el is not None:
                for port in ports_el.findall("port"):
                    port_data = {
                        "portid": port.get("portid"),
                        "protocol": port.get("protocol"),
                        "state": "",
                        "service": {},
                        "scripts": [],
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
                            "cpe": [c.text for c in svc.findall("cpe")],
                        }

                    for script in port.findall("script"):
                        port_data["scripts"].append(
                            {"id": script.get("id"), "output": script.get("output", "")}
                        )

                    host_data["ports"].append(port_data)

            os_el = host.find("os")
            if os_el is not None:
                for match in os_el.findall("osmatch"):
                    osclass = match.find(".//osclass")
                    host_data["os"].append(
                        {
                            "name": match.get("name"),
                            "accuracy": match.get("accuracy"),
                            "osfamily": osclass.get("osfamily", "") if osclass is not None else "",
                        }
                    )

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
                        "description": "IP address, hostname, or CIDR range (e.g. 192.168.1.1 or 10.0.0.0/24)",
                    },
                    "rate": {
                        "type": "integer",
                        "description": "Packet rate limit (default 1000, reduce for stealth)",
                        "default": 1000,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Scan timeout in seconds (default 300)",
                        "default": 300,
                    },
                },
                "required": ["target"],
            },
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
                        "description": "Comma-separated port list (e.g. '22,80,443,8080')",
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["target", "ports"],
            },
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
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["target", "ports"],
            },
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
                    "timeout": {"type": "integer", "default": 120},
                },
                "required": ["target", "ports"],
            },
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
                        "description": "Full nmap command (e.g. 'nmap -sV --script=ssh-auth-methods -p 22 192.168.1.1')",
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["command"],
            },
        ),
        types.Tool(
            name="subfinder",
            description="Passive subdomain discovery using various OSINT sources.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Target domain (e.g. example.com)"},
                    "timeout": {"type": "integer", "default": 180},
                },
                "required": ["domain"],
            },
        ),
        types.Tool(
            name="httpx",
            description="Fast and multi-purpose HTTP toolkit for probing technologies and status codes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target URL or domain"},
                    "options": {
                        "type": "string",
                        "description": "Additional httpx flags (e.g. -status-code -title)",
                        "default": "-status-code -title -tech-detect",
                    },
                    "timeout": {"type": "integer", "default": 120},
                },
                "required": ["target"],
            },
        ),
        types.Tool(
            name="ffuf",
            description="Fast web fuzzer for directory and file discovery.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL with FUZZ keyword (e.g. http://target.com/FUZZ)",
                    },
                    "wordlist": {
                        "type": "string",
                        "description": "Wordlist path",
                        "default": "/usr/share/wordlists/dirb/common.txt",
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="gobuster",
            description="URI/File/DNS brute forcing tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL (e.g. http://target.com)"},
                    "wordlist": {
                        "type": "string",
                        "description": "Wordlist path",
                        "default": "/usr/share/wordlists/dirb/common.txt",
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["url"],
            },
        ),
    ]


# ─────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── FULL PORT SCAN ─────────────────────────────────────────────────
    if name == "nmap_full_port_scan":
        target = arguments["target"]
        rate = arguments.get("rate", 1000)
        timeout = arguments.get("timeout", 300)

        cmd = f"nmap -p- --min-rate={rate} -T4 --open -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {
                "tool": "nmap_full_port_scan",
                "target": target,
                "success": False,
                "error": raw["stderr"],
                "command": cmd,
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
                "raw_parsed": parsed,
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── SERVICE SCAN ───────────────────────────────────────────────────
    elif name == "nmap_service_scan":
        target = arguments["target"]
        ports = arguments["ports"]
        timeout = arguments.get("timeout", 300)

        cmd = f"nmap -sV -sC -p{ports} -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {
                "tool": "nmap_service_scan",
                "target": target,
                "success": False,
                "error": raw["stderr"],
                "command": cmd,
            }
        else:
            parsed = parse_nmap_xml(raw["stdout"])
            services = []
            for host in parsed.get("hosts", []):
                for port in host.get("ports", []):
                    if port["state"] == "open":
                        svc = port.get("service", {})
                        services.append(
                            {
                                "port": port["portid"],
                                "protocol": port["protocol"],
                                "service": svc.get("name", "unknown"),
                                "product": svc.get("product", ""),
                                "version": svc.get("version", ""),
                                "extra": svc.get("extrainfo", ""),
                                "cpe": svc.get("cpe", []),
                                "scripts": port.get("scripts", []),
                            }
                        )

            result = {
                "tool": "nmap_service_scan",
                "target": target,
                "success": True,
                "command": cmd,
                "timestamp": datetime.now().isoformat(),
                "services": services,
                "service_count": len(services),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── VULN SCAN ──────────────────────────────────────────────────────
    elif name == "nmap_vuln_scan":
        target = arguments["target"]
        ports = arguments["ports"]
        timeout = arguments.get("timeout", 300)

        cmd = f"nmap --script=vuln -p{ports} -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {
                "tool": "nmap_vuln_scan",
                "target": target,
                "success": False,
                "error": raw["stderr"],
                "command": cmd,
            }
        else:
            parsed = parse_nmap_xml(raw["stdout"])
            vuln_findings = []
            for host in parsed.get("hosts", []):
                for port in host.get("ports", []):
                    for script in port.get("scripts", []):
                        if "VULNERABLE" in script.get("output", "").upper() or "CVE" in script.get(
                            "output", ""
                        ).upper():
                            vuln_findings.append(
                                {
                                    "port": port["portid"],
                                    "script": script["id"],
                                    "output": script["output"],
                                }
                            )

            result = {
                "tool": "nmap_vuln_scan",
                "target": target,
                "success": True,
                "command": cmd,
                "timestamp": datetime.now().isoformat(),
                "vulnerability_hits": vuln_findings,
                "vuln_count": len(vuln_findings),
                "raw_parsed": parsed,
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── OS DETECTION ───────────────────────────────────────────────────
    elif name == "nmap_os_detection":
        target = arguments["target"]
        ports = arguments["ports"]
        timeout = arguments.get("timeout", 120)

        cmd = f"nmap -O -p{ports} -oX - {target}"
        raw = run_command(cmd, timeout)

        if not raw["success"]:
            result = {
                "tool": "nmap_os_detection",
                "target": target,
                "success": False,
                "error": raw["stderr"],
                "command": cmd,
            }
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
                "best_guess": os_results[0] if os_results else None,
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── SUBFINDER ──────────────────────────────────────────────────────
    elif name == "subfinder":
        domain = arguments["domain"]
        timeout = arguments.get("timeout", 180)
        cmd = f"subfinder -d {domain} -silent"
        raw = run_command(cmd, timeout)
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "tool": "subfinder",
                        "domain": domain,
                        "success": raw["success"],
                        "subdomains": raw["stdout"].strip().split("\n") if raw["stdout"] else [],
                        "stderr": raw["stderr"],
                    },
                    indent=2,
                ),
            )
        ]

    # ── HTTPX ──────────────────────────────────────────────────────────
    elif name == "httpx":
        target = arguments["target"]
        options = arguments.get("options", "-status-code -title -tech-detect")
        timeout = arguments.get("timeout", 120)
        cmd = f"echo {target} | httpx {options} -silent"
        raw = run_command(cmd, timeout)
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "tool": "httpx",
                        "target": target,
                        "success": raw["success"],
                        "output": raw["stdout"].strip(),
                        "stderr": raw["stderr"],
                    },
                    indent=2,
                ),
            )
        ]

    # ── FFUF ───────────────────────────────────────────────────────────
    elif name == "ffuf":
        url = arguments["url"]
        wordlist = arguments.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        timeout = arguments.get("timeout", 300)
        cmd = f"ffuf -u {url} -w {wordlist} -mc 200,301,302,403 -s"
        raw = run_command(cmd, timeout)
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "tool": "ffuf",
                        "url": url,
                        "success": raw["success"],
                        "output": raw["stdout"].strip(),
                        "stderr": raw["stderr"],
                    },
                    indent=2,
                ),
            )
        ]

    # ── GOBUSTER ───────────────────────────────────────────────────────
    elif name == "gobuster":
        url = arguments["url"]
        wordlist = arguments.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        timeout = arguments.get("timeout", 300)
        cmd = f"gobuster dir -u {url} -w {wordlist} -q -n"
        raw = run_command(cmd, timeout)
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "tool": "gobuster",
                        "url": url,
                        "success": raw["success"],
                        "output": raw["stdout"].strip(),
                        "stderr": raw["stderr"],
                    },
                    indent=2,
                ),
            )
        ]

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
