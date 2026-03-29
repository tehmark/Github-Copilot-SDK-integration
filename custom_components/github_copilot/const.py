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

# Default custom instructions pre-populated when ha-mcp is configured.
# Reflects the new scope: a heavy-task agent that performs complex HA tasks and saves
# results to HA helper entities so a lighter model can read them later.
# Optimised for claude-haiku-4.5 with ha-mcp "Enable tool search" ON.
DEFAULT_HA_INSTRUCTIONS = (
    "You are a capable Home Assistant task agent. "
    "You have access to Home Assistant via the ha-mcp MCP server. "
    "Use it to carry out complex tasks: build automations, diagnose issues, "
    "analyse sensor history, manage devices and dashboards.\n\n"
    "When using Home Assistant tools:\n"
    "- Call ha_search_tools first to find the right tool. "
    "Use descriptive search terms — e.g. 'get sensor history', 'create automation', 'set helper value'.\n"
    "- Use the write proxy for create/update/set/control actions. "
    "Use the read proxy for queries and state reads. "
    "Use the delete proxy only for removals.\n"
    "- Be thorough. For complex tasks, gather all needed context before acting.\n\n"
    "When a task is complete:\n"
    "- Save a concise summary of what was done, key findings, and any created entity IDs "
    "to a Home Assistant input_text or note helper entity using ha-mcp. "
    "This lets a lighter model read your work later without repeating it.\n"
    "- Report clearly what you did and what was saved, including the helper entity name."
)


# API constants
API_TIMEOUT = 30  # Timeout in seconds for API requests
