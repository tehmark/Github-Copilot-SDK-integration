"""Constants for github_copilot."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "github_copilot"
ATTRIBUTION = "Powered by GitHub Copilot SDK"

# Configuration constants
CONF_MODEL = "model"
CONF_CLI_URL = "cli_url"
CONF_MCP_URL = "mcp_url"
CONF_INSTRUCTIONS = "instructions"

# Default values
DEFAULT_MODEL = "claude-haiku-4.5"
DEFAULT_CLI_URL = "http://github-copilot-bridge:7681"

# Fallback model list used when the live Copilot CLI is unreachable.
# The Configure dialog fetches the real list dynamically — this is only a safety net.
# GitHub updates available models frequently; check https://github.com/features/copilot/plans.
# ⚡ = fast/low-latency  ✓ = included (no premium cost)  $ = uses premium request budget
SUPPORTED_MODELS = [
    # --- Fast / Included (recommended for voice & HA control) ---
    {"value": "claude-haiku-4.5",    "label": "claude-haiku-4.5 ⚡✓ — best for voice & HA control, included (use with tool search ON in ha-mcp)"},
    {"value": "gpt-5.4-mini",        "label": "gpt-5.4-mini ⚡✓ — fastest GPT, included (use with tool search ON in ha-mcp)"},
    {"value": "gpt-5-mini",          "label": "gpt-5-mini ⚡✓ — fast, included (use with tool search ON in ha-mcp)"},
    {"value": "gpt-5.1-codex-mini",  "label": "gpt-5.1-codex-mini ⚡✓ — fast, code-optimised, included"},
    {"value": "gpt-4.1",             "label": "gpt-4.1 ⚡✓ — fast, included"},
    # --- Balanced quality / premium (use with tool search OFF in ha-mcp) ---
    {"value": "gpt-5.1",             "label": "gpt-5.1 $ — balanced quality, premium requests (tool search OFF)"},
    {"value": "gpt-5.2",             "label": "gpt-5.2 $ — balanced quality, premium requests (tool search OFF)"},
    {"value": "gpt-5.1-codex",       "label": "gpt-5.1-codex $ — code-focused, premium requests"},
    {"value": "gpt-5.2-codex",       "label": "gpt-5.2-codex $ — code-focused, premium requests"},
    {"value": "gpt-5.3-codex",       "label": "gpt-5.3-codex $ — code-focused, premium requests"},
    {"value": "claude-sonnet-4",     "label": "claude-sonnet-4 $ — Anthropic, premium requests (tool search OFF)"},
    {"value": "claude-sonnet-4.5",   "label": "claude-sonnet-4.5 $ — Anthropic, premium requests (tool search OFF)"},
    {"value": "claude-sonnet-4.6",   "label": "claude-sonnet-4.6 $ — latest Anthropic Sonnet, premium requests (tool search OFF)"},
    {"value": "gemini-3-pro-preview", "label": "gemini-3-pro-preview $ — Google, premium requests"},
    # --- Heavy / high-cost ---
    {"value": "gpt-5.4",             "label": "gpt-5.4 $$ — most capable GPT, premium requests"},
    {"value": "gpt-5.1-codex-max",   "label": "gpt-5.1-codex-max $$ — max code model, premium requests"},
    {"value": "claude-opus-4.5",     "label": "claude-opus-4.5 $$ — Anthropic flagship, premium requests"},
    {"value": "claude-opus-4.6",     "label": "claude-opus-4.6 $$ — latest Anthropic Opus, premium requests"},
]

# Plain list of model IDs for validation logic
SUPPORTED_MODEL_IDS = [m["value"] for m in SUPPORTED_MODELS]

# Default system message appended when ha-mcp is configured.
# Tells Copilot it's acting as a Home Assistant agent and should use MCP tools proactively.
DEFAULT_HA_SYSTEM_PROMPT = (
    "You are a smart home assistant integrated into Home Assistant. "
    "You have access to a set of Home Assistant MCP tools that let you read and control "
    "devices, entities, automations, scripts, scenes, and dashboards in the user's home. "
    "When the user asks about their home, devices, lights, climate, sensors, or wants to "
    "control anything in their house, use these tools proactively — do not just describe "
    "what you could do, actually do it. "
    "Always confirm what you did after completing an action. "
    "If a request is ambiguous (e.g. 'the lights' could mean multiple rooms), ask a "
    "short clarifying question before acting."
)

# Default custom instructions pre-populated when ha-mcp is configured.
# Optimised for claude-haiku-4.5 with ha-mcp "Enable tool search" mode ON.
# Haiku lacks deferred tool loading — tool search reduces idle context from ~46K to ~5K tokens.
# In tool search mode: ha_search_tools discovers available tools; proxies execute them.
DEFAULT_HA_INSTRUCTIONS = (
    "When controlling or querying Home Assistant:\n"
    "- Always call ha_search_tools first to find the right tool for the task. "
    "Use descriptive search terms — e.g. 'turn on light', 'get sensor state', 'run script'.\n"
    "- Be fuzzy with device names. A ceiling fan may be a switch entity with 'fan' in the name, "
    "not a fan entity. Try 'fan', 'ceiling', 'switch' if the first search finds nothing.\n"
    "- Use the write proxy for on/off/toggle/set actions. Use the read proxy for state queries. "
    "Use the delete proxy only for removing things.\n"
    "- For 'all X' requests (e.g. 'all lights', 'all fans'), search broadly and call the write proxy "
    "for each matching entity, or find a bulk tool if available.\n"
    "- For simple on/off/toggle commands, act immediately without asking for confirmation. "
    "After acting, briefly report what you did in one sentence (e.g. 'Turned on 3 fans in the house.').\n"
    "- If a search returns no results, retry with alternate terms "
    "(e.g. 'ceiling', 'lamp', 'overhead', 'switch').\n"
    "- Keep all responses short and conversational — responses are read aloud via voice assistant. "
    "One or two sentences maximum. Do not use emoji, bullet points, or markdown formatting."
)


# API constants
API_TIMEOUT = 30  # Timeout in seconds for API requests
