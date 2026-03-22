"""Adds config flow for GitHub Copilot."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .api import (
    GitHubCopilotApiClient,
    GitHubCopilotApiClientAuthenticationError,
    GitHubCopilotApiClientCommunicationError,
    GitHubCopilotApiClientError,
)
from .const import (
    CONF_CLI_URL,
    CONF_MODEL,
    CONF_MCP_URL,
    CONF_INSTRUCTIONS,
    DEFAULT_CLI_URL,
    DEFAULT_MODEL,
    DOMAIN,
    LOGGER,
    SUPPORTED_MODELS,
    SUPPORTED_MODEL_IDS,
)


class GitHubCopilotFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for GitHub Copilot."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GitHubCopilotOptionsFlow:
        """Get the options flow for this handler."""
        return GitHubCopilotOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            model = user_input.get(CONF_MODEL, DEFAULT_MODEL)
            cli_url = user_input.get(CONF_CLI_URL, DEFAULT_CLI_URL).strip()
            mcp_url = user_input.get(CONF_MCP_URL, "").strip()

            if not cli_url:
                _errors[CONF_CLI_URL] = "required"
            else:
                parsed = urlparse(cli_url)
                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    _errors[CONF_CLI_URL] = "invalid_url"

            if not _errors:
                try:
                    LOGGER.debug(
                        "Testing connection to Copilot add-on at '%s' with model '%s'",
                        cli_url,
                        model,
                    )
                    await self._test_connection(cli_url=cli_url, model=model)
                except GitHubCopilotApiClientAuthenticationError as exception:
                    LOGGER.warning(
                        "GitHub Copilot authentication failed: %s",
                        exception,
                    )
                    _errors["base"] = "auth"
                except GitHubCopilotApiClientCommunicationError as exception:
                    LOGGER.error(
                        "Failed to connect to GitHub Copilot add-on: %s",
                        exception,
                    )
                    _errors["base"] = "connection"
                except GitHubCopilotApiClientError as exception:
                    LOGGER.exception(
                        "Unexpected error during GitHub Copilot setup: %s",
                        exception,
                    )
                    _errors["base"] = "unknown"
                except Exception as exception:  # noqa: BLE001
                    LOGGER.exception(
                        "Unexpected error in config flow: %s",
                        type(exception).__name__,
                    )
                    _errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id("github_copilot")
                    self._abort_if_unique_id_configured()
                    LOGGER.info(
                        "GitHub Copilot integration configured (add-on: '%s', model: '%s')",
                        cli_url,
                        model,
                    )
                    return self.async_create_entry(
                        title="GitHub Copilot Bridge Integration",
                        data=user_input,
                    )

        try:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_CLI_URL,
                            default=DEFAULT_CLI_URL,
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.URL,
                            ),
                        ),
                        vol.Optional(
                            CONF_MODEL,
                            default=DEFAULT_MODEL,
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=SUPPORTED_MODELS,  # type: ignore[arg-type]
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            ),
                        ),
                        vol.Optional(
                            CONF_MCP_URL,
                            default="",
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.URL,
                            ),
                        ),
                    },
                ),
                errors=_errors,
                description_placeholders={
                    "documentation_url": "https://github.com/tserra30/Github-Copilot-SDK-integration",
                    "default_url": DEFAULT_CLI_URL,
                },
            )
        except Exception as exception:  # noqa: BLE001
            LOGGER.exception(
                "Failed to render config flow form: %s",
                type(exception).__name__,
            )
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_CLI_URL, default=DEFAULT_CLI_URL): str,
                    }
                ),
                errors={"base": "unknown"},
            )

    async def _test_connection(
        self,
        cli_url: str,
        model: str,
    ) -> None:
        """Validate connection to the Copilot add-on."""
        client = GitHubCopilotApiClient(
            model=model,
            client_options={"cli_url": cli_url},
        )
        try:
            await client.async_test_connection()
        except (
            GitHubCopilotApiClientAuthenticationError,
            GitHubCopilotApiClientCommunicationError,
            GitHubCopilotApiClientError,
        ):
            raise
        except Exception as exception:
            LOGGER.exception(
                "Unexpected exception during connection test: %s",
                type(exception).__name__,
            )
            msg = (
                f"Unexpected error during connection test: "
                f"{type(exception).__name__}"
            )
            raise GitHubCopilotApiClientError(msg) from exception
        finally:
            await client.async_close()


class GitHubCopilotOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for GitHub Copilot integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_MCP_URL: user_input.get(CONF_MCP_URL, "").strip(),
                    CONF_INSTRUCTIONS: user_input.get(CONF_INSTRUCTIONS, "").strip(),
                },
            )
            return self.async_create_entry(title="", data={})

        current_model = self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        current_mcp_url = self.config_entry.data.get(CONF_MCP_URL, "")
        current_instructions = self.config_entry.data.get(CONF_INSTRUCTIONS, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODEL,
                        default=current_model,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=SUPPORTED_MODELS,  # type: ignore[arg-type]
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Optional(
                        CONF_MCP_URL,
                        default=current_mcp_url,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.URL,
                        ),
                    ),
                    vol.Optional(
                        CONF_INSTRUCTIONS,
                        default=current_instructions,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=True,
                        ),
                    ),
                }
            ),
        )
