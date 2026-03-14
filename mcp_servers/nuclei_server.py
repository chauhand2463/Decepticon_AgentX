"""
DECEPTICON — Nuclei MCP Server
Wraps Nuclei template-based CVE/misconfiguration scanner for the Researcher Agent.

Install: pip install mcp && go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
Run:     python mcp_servers/nuclei_server.py
"""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from docker_utils import run_in_container

app = Server("decepticon-nuclei")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def run_command(cmd: str, timeout: int = 600) -> dict:
    """Run a shell command inside the attacker container."""
    return run_in_container(cmd, timeout)


def parse_nuclei_jsonl(raw_output: str) -> list:
    """Parse nuclei JSONL output into structured list."""
    findings = []
    for line in raw_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            findings.append({
                "template_id":   entry.get("template-id", ""),
                "name":          entry.get("info", {}).get("name", ""),
                "severity":      entry.get("info", {}).get("severity", "unknown").upper(),
                "cvss_score":    entry.get("info", {}).get("classification", {}).get("cvss-score", None),
                "cve":           entry.get("info", {}).get("classification", {}).get("cve-id", []),
                "description":   entry.get("info", {}).get("description", ""),
                "remediation":   entry.get("info", {}).get("remediation", ""),
                "matched_at":    entry.get("matched-at", ""),
                "host":          entry.get("host", ""),
                "ip":            entry.get("ip", ""),
                "tags":          entry.get("info", {}).get("tags", []),
                "reference":     entry.get("info", {}).get("reference", []),
                "extracted_results": entry.get("extracted-results", []),
                "matcher_name":  entry.get("matcher-name", ""),
                "timestamp":     entry.get("timestamp", "")
            })
        except json.JSONDecodeError:
            # Non-JSON line (progress output etc.), skip
            continue
    return findings


def severity_to_priority(severity: str) -> int:
    return {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(severity.upper(), 5)


# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="nuclei_cve_scan",
            description=(
                "Scan a target for known CVEs using Nuclei's CVE template library. "
                "Runs only CVE templates at critical and high severity. "
                "Returns confirmed CVE matches with CVSS scores and PoC details. "
                "Run against web targets AND network services."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target URL or IP (e.g. http://192.168.1.1 or 192.168.1.1)"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Severity filter: critical,high,medium,low (default: critical,high)",
                        "default": "critical,high"
                    },
                    "timeout": {"type": "integer", "default": 600}
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="nuclei_misconfig_scan",
            description=(
                "Scan for security misconfigurations: exposed admin panels, default credentials, "
                "open redirects, CORS issues, missing headers, exposed files and directories. "
                "Essential for web application audits."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target URL (e.g. http://target.com)"},
                    "timeout": {"type": "integer", "default": 600}
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="nuclei_network_scan",
            description=(
                "Scan network services (SSH, FTP, SMB, Redis, MongoDB, etc.) "
                "for default credentials, exposed services, and network-level vulnerabilities. "
                "Pass IP:port format for non-HTTP services."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target IP or IP:port"},
                    "timeout": {"type": "integer", "default": 300}
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="nuclei_tech_detect",
            description=(
                "Detect web technologies, frameworks, CMS versions, and server software. "
                "Use BEFORE CVE scan to know exactly what templates to run. "
                "Returns detected technologies for targeted vulnerability research."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target URL"},
                    "timeout": {"type": "integer", "default": 120}
                },
                "required": ["target"]
            }
        ),
        types.Tool(
            name="nuclei_full_scan",
            description=(
                "Run ALL Nuclei templates: CVEs, misconfigurations, exposures, "
                "default-logins, and tech detection in one pass. "
                "Slower but most comprehensive. Recommended for full pentest engagements."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "description": "Minimum severity (default: medium)",
                        "default": "medium"
                    },
                    "timeout": {"type": "integer", "default": 900}
                },
                "required": ["target"]
            }
        )
    ]


# ─────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    target  = arguments.get("target", "")
    timeout = arguments.get("timeout", 600)

    # ── CVE SCAN ────────────────────────────────────────────────────────
    if name == "nuclei_cve_scan":
        severity = arguments.get("severity", "critical,high")
        cmd = f"nuclei -u {target} -t cves/ -severity {severity} -json -silent -no-color"
        raw = run_command(cmd, timeout)

        findings = parse_nuclei_jsonl(raw["stdout"]) if raw["stdout"] else []
        findings.sort(key=lambda x: severity_to_priority(x["severity"]))

        result = {
            "tool": "nuclei_cve_scan",
            "target": target,
            "command": cmd,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "findings": findings,
            "summary": {
                "total": len(findings),
                "critical": sum(1 for f in findings if f["severity"] == "CRITICAL"),
                "high":     sum(1 for f in findings if f["severity"] == "HIGH"),
                "medium":   sum(1 for f in findings if f["severity"] == "MEDIUM"),
            },
            "stderr": raw["stderr"] if not raw["success"] else ""
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── MISCONFIG SCAN ──────────────────────────────────────────────────
    elif name == "nuclei_misconfig_scan":
        cmd = (
            f"nuclei -u {target} "
            f"-t misconfigurations/ -t exposures/ -t default-logins/ "
            f"-json -silent -no-color"
        )
        raw = run_command(cmd, timeout)
        findings = parse_nuclei_jsonl(raw["stdout"]) if raw["stdout"] else []
        findings.sort(key=lambda x: severity_to_priority(x["severity"]))

        result = {
            "tool": "nuclei_misconfig_scan",
            "target": target,
            "command": cmd,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "findings": findings,
            "summary": {
                "total": len(findings),
                "critical": sum(1 for f in findings if f["severity"] == "CRITICAL"),
                "high":     sum(1 for f in findings if f["severity"] == "HIGH"),
                "default_logins": [f for f in findings if "default-logins" in f.get("tags", [])]
            },
            "stderr": raw["stderr"] if not raw["success"] else ""
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── NETWORK SCAN ────────────────────────────────────────────────────
    elif name == "nuclei_network_scan":
        cmd = f"nuclei -u {target} -t network/ -t default-logins/ -json -silent -no-color"
        raw = run_command(cmd, timeout)
        findings = parse_nuclei_jsonl(raw["stdout"]) if raw["stdout"] else []

        result = {
            "tool": "nuclei_network_scan",
            "target": target,
            "command": cmd,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "findings": findings,
            "total": len(findings),
            "default_credential_hits": [f for f in findings if "default-login" in f.get("template_id", "")],
            "stderr": raw["stderr"] if not raw["success"] else ""
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── TECH DETECT ─────────────────────────────────────────────────────
    elif name == "nuclei_tech_detect":
        cmd = f"nuclei -u {target} -t technologies/ -json -silent -no-color"
        raw = run_command(cmd, timeout)
        findings = parse_nuclei_jsonl(raw["stdout"]) if raw["stdout"] else []

        technologies = [f["name"] for f in findings]

        result = {
            "tool": "nuclei_tech_detect",
            "target": target,
            "command": cmd,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "technologies_detected": technologies,
            "raw_findings": findings,
            "recommendation": f"Run nuclei_cve_scan with templates matching: {', '.join(technologies[:5])}" if technologies else "No technologies detected"
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── FULL SCAN ───────────────────────────────────────────────────────
    elif name == "nuclei_full_scan":
        severity = arguments.get("severity", "medium")
        cmd = (
            f"nuclei -u {target} "
            f"-t cves/ -t misconfigurations/ -t exposures/ "
            f"-t technologies/ -t default-logins/ -t network/ "
            f"-severity {severity},high,critical "
            f"-json -silent -no-color"
        )
        raw = run_command(cmd, timeout)
        findings = parse_nuclei_jsonl(raw["stdout"]) if raw["stdout"] else []
        findings.sort(key=lambda x: severity_to_priority(x["severity"]))

        result = {
            "tool": "nuclei_full_scan",
            "target": target,
            "command": cmd,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "findings": findings,
            "summary": {
                "total": len(findings),
                "critical": sum(1 for f in findings if f["severity"] == "CRITICAL"),
                "high":     sum(1 for f in findings if f["severity"] == "HIGH"),
                "medium":   sum(1 for f in findings if f["severity"] == "MEDIUM"),
                "low":      sum(1 for f in findings if f["severity"] == "LOW"),
                "info":     sum(1 for f in findings if f["severity"] == "INFO"),
            },
            "top_findings": findings[:10],
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
