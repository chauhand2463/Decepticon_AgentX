# Architecture & Orchestration

**DECEPTICON** is built on a modular, multi-agent architecture powered by **LangGraph**. This allows for complex, stateful workflows that are both autonomous and human-steerable.

## 🧠 The Orchestration Engine

The core of DECEPTICON is the **Supervisory Mesh**. Unlike simple linear chains, our agents operate in a graph-based state machine.

### State Management
- **Shared State**: All agents share a common background, mission objective, and discovery log.
- **Persistent Memory**: Findings are stored in a vector database (optional integration) to allow agents to recall previous scan results across different mission phases.

## 🧱 Key Components

### 1. LangGraph Cycles
The workflow is not a straight line. If a **Recon Agent** finds a new port, it updates the state, and the **Planner** may decide to loop back and send an **Access Agent** to investigate immediately.

### 2. MCP (Model Context Protocol) Integration
DECEPTICON uses MCP to bridge the gap between AI reasoning and real-world tools.
- **Terminal Server**: Allows agents to run safe shell commands (e.g., `nmap`, `curl`).
- **Filesystem Server**: Enables agents to read/write mission reports and configuration.

## 📡 Communication Flow

1.  **User Input** → Tactical CLI / Web UI.
2.  **Planner** → Analyzes goal and delegates to specialists.
3.  **Specialists** → Execute tools via MCP, return observations.
4.  **State Update** → The shared mission log is updated.
5.  **Termination/Reporting** → Summary agent compiles results when the goal is met.
