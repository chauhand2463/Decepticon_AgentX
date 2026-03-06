# Installation Guide

This guide provides detailed instructions for setting up **DECEPTICON** in various environments.

## 🐍 Python Environment

We recommend using **Python 3.11+**.

### 1. Using UV (Recommended)
[UV](https://github.com/astral-sh/uv) is an extremely fast Python package manager.

```bash
# Install uv if you haven't
curl -LsSf https://astral-sh.dev/uv/install.sh | sh

# Clone and sync
git clone https://github.com/PurpleAILAB/Decepticon.git
cd Decepticon
uv sync
```

### 2. Standard Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🐋 Docker Setup

For a consistent environment or to run the target lab, use Docker.

### Running Decepticon as a Container
```bash
docker-compose up -d
```

---

## 🛠️ Configuration

Populate your `.env` file with the following keys:

### Essential Keys
- `OPENAI_API_KEY`: For GPT-4o and reasoning models.
- `OPENROUTER_API_KEY`: To access DeepSeek, Llama 3, and more.

### Troubleshooting
- **Import Errors**: Ensure you have synced your environment with `uv sync` or `pip install -r requirements.txt`.
- **API Failures**: Verify your keys and check if you have sufficient credits in your LLM provider account.
