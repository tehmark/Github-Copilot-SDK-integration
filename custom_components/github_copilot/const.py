"""Constants for github_copilot."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "github_copilot"
ATTRIBUTION = "Powered by GitHub Copilot SDK"

# Configuration constants
CONF_MODEL = "model"
CONF_CLI_URL = "cli_url"

# Default values
DEFAULT_MODEL = "gpt-4o"
DEFAULT_CLI_URL = "http://github-copilot-bridge:7681"

# Model list with display labels showing approximate cost category.
# "Included" models do not consume premium requests on paid Copilot plans.
# "Premium" models draw from your monthly premium-request allowance.
# Check https://docs.github.com/en/copilot/about-github-copilot/plans-for-github-copilot
# for the current multiplier table, as GitHub updates it frequently.
SUPPORTED_MODELS = [
    {"value": "gpt-4o",          "label": "GPT-4o — included, no premium cost ✓"},
    {"value": "gpt-4o-mini",     "label": "GPT-4o mini — included, faster & lighter ✓"},
    {"value": "gpt-3.5-turbo",   "label": "GPT-3.5 Turbo — included, fastest response ✓"},
    {"value": "o3-mini",         "label": "o3-mini — reasoning model, uses premium requests"},
    {"value": "o1-mini",         "label": "o1-mini — reasoning model, uses premium requests"},
    {"value": "o1",              "label": "o1 — deep reasoning, high premium cost"},
    {"value": "gpt-4-turbo",     "label": "GPT-4 Turbo — uses premium requests"},
    {"value": "gpt-4",           "label": "GPT-4 — uses premium requests"},
    {"value": "claude-3.5-sonnet", "label": "Claude 3.5 Sonnet — uses premium requests"},
    {"value": "claude-3.7-sonnet", "label": "Claude 3.7 Sonnet — uses premium requests"},
]

# Plain list of model IDs for validation logic
SUPPORTED_MODEL_IDS = [m["value"] for m in SUPPORTED_MODELS]


# API constants
API_TIMEOUT = 30  # Timeout in seconds for API requests
