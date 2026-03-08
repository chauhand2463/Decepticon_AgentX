

ICON = "assets/logo.png"
ICON_TEXT = "assets/logo_text1.png"

DEFAULT_CHAT_HEIGHT = 700
DEFAULT_THEME = "dark"
DEFAULT_DOCKER_CONTAINER = "decepticon-kali"

MESSAGE_TYPE_USER = "user"
MESSAGE_TYPE_AI = "ai"
MESSAGE_TYPE_TOOL = "tool"

AGENT_PLANNER = "planner"
AGENT_RECONNAISSANCE = "reconnaissance"
AGENT_INITIAL_ACCESS = "initial_access"
AGENT_EXECUTION = "execution"
AGENT_PERSISTENCE = "persistence"
AGENT_PRIVILEGE_ESCALATION = "privilege_escalation"
AGENT_DEFENSE_EVASION = "defense_evasion"
AGENT_SUMMARY = "summary"

AGENTS_INFO = [
    {"id": AGENT_PLANNER, "name": "Planner", "icon": "🧠"},
    {"id": AGENT_RECONNAISSANCE, "name": "Reconnaissance", "icon": "🔍"},
    {"id": AGENT_INITIAL_ACCESS, "name": "Initial Access", "icon": "🔑"},
    {"id": AGENT_EXECUTION, "name": "Execution", "icon": "💻"},
    {"id": AGENT_PERSISTENCE, "name": "Persistence", "icon": "🔐"},
    {"id": AGENT_PRIVILEGE_ESCALATION, "name": "Privilege Escalation", "icon": "🔒"},
    {"id": AGENT_DEFENSE_EVASION, "name": "Defense Evasion", "icon": "🕵️"},
    {"id": AGENT_SUMMARY, "name": "Summary", "icon": "📋"},
]

CSS_CLASS_AGENT_STATUS = "agent-status"
CSS_CLASS_STATUS_ACTIVE = "status-active"
CSS_CLASS_STATUS_COMPLETED = "status-completed"
CSS_CLASS_TERMINAL_CONTAINER = "terminal-container"
CSS_CLASS_MAC_TERMINAL_HEADER = "mac-terminal-header"

SESSION_KEY_EXECUTOR_READY = "executor_ready"
SESSION_KEY_CURRENT_MODEL = "current_model"
SESSION_KEY_WORKFLOW_RUNNING = "workflow_running"
SESSION_KEY_STRUCTURED_MESSAGES = "structured_messages"
SESSION_KEY_TERMINAL_MESSAGES = "terminal_messages"
SESSION_KEY_ACTIVE_AGENT = "active_agent"
SESSION_KEY_COMPLETED_AGENTS = "completed_agents"
SESSION_KEY_TERMINAL_HISTORY = "terminal_history"
SESSION_KEY_DEBUG_MODE = "debug_mode"
SESSION_KEY_THEME_MANAGER = "theme_manager"
SESSION_KEY_REPLAY_MODE = "replay_mode"

API_KEYS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "GOOGLE_API_KEY"
]

PROVIDERS = [
    "Anthropic",
    "OpenAI",
    "DeepSeek",
    "Gemini",
    "Groq",
    "Ollama",
    "OpenRouter"
]

TERMINAL_PREFIXES_TO_REMOVE = [
    'Running command:',
    'Executing:',
    'Command:',
    'Execute:',
    '$'
]

TERMINAL_TOOL_KEYWORDS = [
    "terminal",
    "command",
    "exec",
    "shell"
]

COMPANY_LINK = "https://decepticon.cyber"

CSS_PATH_TERMINAL = "frontend/static/css/terminal.css"
CSS_PATH_CHAT_UI = "frontend/static/css/chat_ui.css"
CSS_PATH_AGENT_STATUS = "frontend/static/css/agent_status.css"
CSS_PATH_LAYOUT = "frontend/static/css/layout.css"
CSS_PATH_INPUT_FIX = "frontend/static/css/input_fix.css"
CSS_PATH_MODEL_INFO = "frontend/static/css/model_info.css"