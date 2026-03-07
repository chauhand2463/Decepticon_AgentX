# DECEPTICON — Complete Integration Guide

## What's in This Package

```
decepticon/
├── agents/
│   └── prompts.py              ← All 5 agent system prompts
├── mcp_servers/
│   ├── nmap_server.py          ← Nmap MCP server (5 tools)
│   ├── nuclei_server.py        ← Nuclei MCP server (5 tools)
│   ├── sqlmap_server.py        ← SQLMap MCP server (5 tools)
│   └── metasploit_server.py    ← Metasploit MCP server (6 tools)
└── config/
    └── mcp_config.json         ← Drop-in replacement for your mcp_config.json
```

---

## Step 1 — Install Dependencies

```bash
# Python MCP library
pip install mcp pymetasploit3

# Security tools (Debian/Ubuntu)
sudo apt update
sudo apt install -y nmap sqlmap metasploit-framework

# Nuclei (Go required)
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
nuclei -update-templates   # Download all CVE/misconfig templates
```

---

## Step 2 — Copy Files Into Your Project

```bash
# From the decepticon/ folder of this package:
cp agents/prompts.py         /your/decepticon/src/utils/agents/prompts.py
cp mcp_servers/*.py          /your/decepticon/mcp_servers/
cp config/mcp_config.json    /your/decepticon/mcp_config.json
```

---

## Step 3 — Wire Prompts Into Your Agent Definitions

In your agent creation code (wherever you call `create_react_agent` or similar), import and use the prompts:

```python
from src.utils.agents.prompts import (
    PLANNER_SYSTEM_PROMPT,
    RECON_SYSTEM_PROMPT,
    ACCESS_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
)

# Example with LangGraph ReAct agent
from langgraph.prebuilt import create_react_agent

planner = create_react_agent(
    model=llm,
    tools=[],                     # Planner uses no tools
    state_modifier=PLANNER_SYSTEM_PROMPT
)

recon = create_react_agent(
    model=llm,
    tools=nmap_mcp_tools,         # Tools from nmap_server.py
    state_modifier=RECON_SYSTEM_PROMPT
)

researcher = create_react_agent(
    model=llm,
    tools=nuclei_mcp_tools,       # Tools from nuclei_server.py
    state_modifier=RESEARCHER_SYSTEM_PROMPT
)

access = create_react_agent(
    model=llm,
    tools=sqlmap_tools + msf_tools, # Both sqlmap + metasploit
    state_modifier=ACCESS_SYSTEM_PROMPT
)

summary = create_react_agent(
    model=llm,
    tools=[],                     # Summary reads state, writes report
    state_modifier=SUMMARY_SYSTEM_PROMPT
)
```

---

## Step 4 — Start Metasploit RPC Daemon

Metasploit needs its RPC server running before you start DECEPTICON:

```bash
# Start msfrpcd (run once, keep running in background)
msfrpcd -P decepticon_pass -u msf -a 127.0.0.1 -p 55553 -S

# Verify it's running
curl -s -k https://127.0.0.1:55553/api/v1/auth/login \
  -d '{"username":"msf","password":"decepticon_pass"}' \
  -H "Content-Type: application/json"
# Should return: {"data":{"token":"..."}}
```

---

## Step 5 — Test Each MCP Server

```bash
# Test Nmap server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/nmap_server.py

# Test Nuclei server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/nuclei_server.py

# Test SQLMap server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/sqlmap_server.py

# Test Metasploit server (msfrpcd must be running)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/metasploit_server.py
```

Each server should return its tool list as JSON.

---

## Step 6 — Test Full Flow Against a Lab Target

```bash
# Start a vulnerable target (Docker)
docker run -d -p 80:80 -p 3306:3306 webgoat/goat-and-wolf

# Start DECEPTICON
python frontend/cli/cli.py

# Type your first mission:
DECEPTICON > Scan 127.0.0.1 and find all exploitable vulnerabilities
```

Expected agent flow:
```
PHANTOM (Planner)  → mission JSON plan
SHADOW  (Recon)    → nmap_full_port_scan → nmap_service_scan → nmap_vuln_scan
ORACLE  (Researcher) → nuclei_cve_scan → nuclei_misconfig_scan
BREACH  (Access)   → sqlmap_detect → msf_search_module → msf_run_exploit
CIPHER  (Summary)  → full penetration test report
```

---

## Tool Reference

### Nmap Tools (recon_agent)
| Tool | Purpose |
|------|---------|
| `nmap_full_port_scan` | Scan all 65535 ports |
| `nmap_service_scan` | Version detection on open ports |
| `nmap_vuln_scan` | NSE vulnerability scripts |
| `nmap_os_detection` | OS fingerprinting |
| `nmap_custom` | Any custom nmap command |

### Nuclei Tools (researcher_agent)
| Tool | Purpose |
|------|---------|
| `nuclei_cve_scan` | Known CVE detection |
| `nuclei_misconfig_scan` | Misconfiguration detection |
| `nuclei_network_scan` | Network service vulns |
| `nuclei_tech_detect` | Technology fingerprinting |
| `nuclei_full_scan` | All templates combined |

### SQLMap Tools (access_agent)
| Tool | Purpose |
|------|---------|
| `sqlmap_detect` | Detect SQL injection |
| `sqlmap_list_databases` | List accessible databases |
| `sqlmap_list_tables` | List tables in database |
| `sqlmap_dump_table` | Dump table contents |
| `sqlmap_os_shell` | OS command execution via SQLi |

### Metasploit Tools (access_agent)
| Tool | Purpose |
|------|---------|
| `msf_search_module` | Find exploit by CVE/keyword |
| `msf_module_info` | Get module options |
| `msf_run_exploit` | Execute exploit |
| `msf_run_auxiliary` | Run scanner/brute-forcer |
| `msf_session_exec` | Run command in active session |
| `msf_list_sessions` | List all active sessions |

---

## Responsible Use

This tool is for authorized security testing only.
Always obtain written permission before testing any system.
