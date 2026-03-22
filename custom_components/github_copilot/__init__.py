"""
Custom integration to integrate GitHub Copilot with Home Assistant.

For more details about this integration, please refer to
https://github.com/tserra30/Github-Copilot-SDK-integration
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from .api import GitHubCopilotApiClient
from .const import (
    CONF_CLI_URL,
    CONF_MODEL,
    CONF_MCP_URL,
    CONF_INSTRUCTIONS,
    DEFAULT_CLI_URL,
    DEFAULT_MODEL,
    DOMAIN,
    LOGGER,
)
from .coordinator import GitHubCopilotDataUpdateCoordinator
from .data import GitHubCopilotData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import GitHubCopilotConfigEntry

PLATFORMS: list[Platform] = [
    Platform.CONVERSATION,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: GitHubCopilotConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    try:
        coordinator = GitHubCopilotDataUpdateCoordinator(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )
        cli_url = entry.data.get(CONF_CLI_URL, DEFAULT_CLI_URL).strip()
        mcp_url = entry.data.get(CONF_MCP_URL, "").strip()
        instructions = entry.data.get(CONF_INSTRUCTIONS, "").strip()
        if not cli_url:
            LOGGER.error(
                "No Copilot CLI URL in config entry — cannot set up integration. "
                "Please re-add the integration and provide the add-on URL."
            )
            return False
        if mcp_url:
            LOGGER.debug(
                "MCP server configured: %s",
                mcp_url,
            )
        if instructions:
            LOGGER.debug("Custom instructions configured (%d chars)", len(instructions))
        LOGGER.debug("Setting up GitHub Copilot integration with add-on URL: %s", cli_url)
        entry.runtime_data = GitHubCopilotData(
            client=GitHubCopilotApiClient(
                model=entry.data.get(CONF_MODEL, DEFAULT_MODEL),
                client_options={"cli_url": cli_url, "mcp_url": mcp_url, "instructions": instructions},
            ),
            integration=async_get_loaded_integration(hass, entry.domain),
            coordinator=coordinator,
        )

        # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
        await coordinator.async_config_entry_first_refresh()

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        LOGGER.info("GitHub Copilot integration setup completed successfully")
        return True  # noqa: TRY300
    except Exception as err:
        # Don't log exception details to avoid exposing tokens
        # or sensitive config data
        LOGGER.error(
            "Failed to set up GitHub Copilot integration: %s",
            type(err).__name__,
        )
        raise


async def async_unload_entry(
    hass: HomeAssistant,
    entry: GitHubCopilotConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.client.async_close()
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: GitHubCopilotConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
