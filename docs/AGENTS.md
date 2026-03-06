# Agent Specialists

DECEPTICON employs a "Swarm" of specialized agents, each with a unique persona and toolset designed for specific phases of a security operation.

## 🕵️‍♂️ Reconnaissance Agent (The Scout)
The Recon agent is responsible for the "Information Gathering" phase.
- **Tools**: Nmap, Dig, Whois, specialized web scrapers.
- **Goal**: Map the attack surface and identify potential entry points.

## 🏗️ Planner Agent (The Architect)
The brain of the operation. It doesn't execute tools directly but manages the mission lifecycle.
- **Logic**: Decomposes complex goals into atomic tasks for other agents.
- **Monitoring**: Re-evaluates the mission plan based on incoming intelligence.

## 🔓 Initial Access Agent (The Breacher)
Focuses on exploitation and validation.
- **Capabilities**: Credential testing, exploit execution (non-destructive), and payload delivery simulation.
- **Safety**: Guided by strict prompts to avoid accidental system damage.

## 🔍 Researcher Agent (The Analyst)
The deep-diver. When a service is found, the Researcher looks up its history.
- **Intelligence**: CVE database cross-referencing, zero-day research (via web search), and patch analysis.

## 📝 Summary Agent (The Reporter)
The final stage of the pipeline.
- **Function**: Compiles all findings, tool outputs, and agent observations into a professional, human-readable report.
- **Output**: Markdown summaries, CVSS scoring suggestions, and remediation advice.
