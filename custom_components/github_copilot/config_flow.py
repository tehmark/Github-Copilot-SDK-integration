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
    DEFAULT_HA_INSTRUCTIONS,
    DOMAIN,
    LOGGER,
    SUPPORTED_MODELS,
    SUPPORTED_MODEL_IDS,
)


class GitHubCopilotFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for GitHub Copilot."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow handler."""
        super().__init__()
        # Populated after a successful connection test — used to show live models
        # when the initially-selected model isn't available.
        self._live_models: list[dict[str, str]] | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,  # noqa: ARG004
    ) -> GitHubCopilotOptionsFlow:
        """Get the options flow for this handler."""
        return GitHubCopilotOptionsFlow()

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
                    live_model_ids = await self._test_connection(cli_url=cli_url, model=model)
                    if live_model_ids and model not in live_model_ids:
                        # Model isn't available on this account — re-show with live list
                        LOGGER.warning(
                            "Selected model '%s' not in live model list %s",
                            model,
                            live_model_ids,
                        )
                        self._live_models = [{"value": m, "label": m} for m in live_model_ids]
                        _errors[CONF_MODEL] = "model_unavailable"
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
                    if not _errors:
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
            # Use live model list if we fetched one (model was invalid), else static fallback
            model_options = self._live_models or list(SUPPORTED_MODELS)
            default_model = DEFAULT_MODEL
            if user_input:
                prev_model = user_input.get(CONF_MODEL, DEFAULT_MODEL)
                # Keep user's choice if it's valid, otherwise suggest first live model
                if any(o["value"] == prev_model for o in model_options):
                    default_model = prev_model
                elif model_options:
                    default_model = model_options[0]["value"]

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
                            default=default_model,
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=model_options,  # type: ignore[arg-type]
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
                    "documentation_url": "https://github.com/tehmark/Github-Copilot-SDK-integration",
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

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration — allows updating the add-on URL."""
        _errors = {}
        if user_input is not None:
            cli_url = user_input.get(CONF_CLI_URL, DEFAULT_CLI_URL).strip()

            if not cli_url:
                _errors[CONF_CLI_URL] = "required"
            else:
                parsed = urlparse(cli_url)
                if parsed.scheme not in ("http", "https") or not parsed.netloc:
                    _errors[CONF_CLI_URL] = "invalid_url"

            if not _errors:
                try:
                    LOGGER.debug(
                        "Reconfigure: testing connection to Copilot add-on at '%s'",
                        cli_url,
                    )
                    await self._test_connection(
                        cli_url=cli_url,
                        model=self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL),
                    )
                except GitHubCopilotApiClientAuthenticationError as exception:
                    LOGGER.warning("Reconfigure: auth failed: %s", exception)
                    _errors["base"] = "auth"
                except GitHubCopilotApiClientCommunicationError as exception:
                    LOGGER.error("Reconfigure: connection failed: %s", exception)
                    _errors["base"] = "connection"
                except GitHubCopilotApiClientError as exception:
                    LOGGER.exception("Reconfigure: unexpected error: %s", exception)
                    _errors["base"] = "unknown"
                except Exception as exception:  # noqa: BLE001
                    LOGGER.exception("Reconfigure: unexpected error: %s", type(exception).__name__)
                    _errors["base"] = "unknown"
                else:
                    LOGGER.info(
                        "Reconfigure: add-on URL updated to '%s'",
                        cli_url,
                    )
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates={CONF_CLI_URL: cli_url},
                    )

        current_url = self.config_entry.data.get(CONF_CLI_URL, DEFAULT_CLI_URL)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CLI_URL,
                        default=current_url,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.URL,
                        ),
                    ),
                }
            ),
            errors=_errors,
            description_placeholders={
                "default_url": DEFAULT_CLI_URL,
                "current_url": current_url,
            },
        )

    async def _test_connection(
        self,
        cli_url: str,
        model: str,
    ) -> list[str]:
        """Validate connection to the Copilot add-on and return available model IDs."""
        client = GitHubCopilotApiClient(
            model=model,
            client_options={"cli_url": cli_url},
        )
        try:
            await client.async_test_connection()
            try:
                return await client.async_available_models()
            except Exception:  # noqa: BLE001
                return []
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

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            # Store settings in options (not data) so HA detects the change
            # and fires the update listener → triggers integration reload.
            return self.async_create_entry(
                title="",
                data={
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_MCP_URL: user_input.get(CONF_MCP_URL, "").strip(),
                    CONF_INSTRUCTIONS: user_input.get(CONF_INSTRUCTIONS, "").strip(),
                },
            )

        # Read from options first (updated via Configure), fall back to data (initial setup)
        current_model = self.config_entry.options.get(
            CONF_MODEL, self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        )
        current_mcp_url = self.config_entry.options.get(
            CONF_MCP_URL, self.config_entry.data.get(CONF_MCP_URL, "")
        )
        current_instructions = self.config_entry.options.get(
            CONF_INSTRUCTIONS, self.config_entry.data.get(CONF_INSTRUCTIONS, "")
        )

        # If ha-mcp is configured but instructions are blank, suggest the default set.
        if current_mcp_url and not current_instructions:
            current_instructions = DEFAULT_HA_INSTRUCTIONS

        # Try to fetch the live model list from the running client.
        # Falls back to the static list if the client is unavailable.
        model_options = await self._get_model_options(current_model)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODEL,
                        default=current_model,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=model_options,  # type: ignore[arg-type]
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

    async def _get_model_options(self, current_model: str) -> list[dict[str, str]]:
        """Fetch live model list from the Copilot CLI, falling back to the static list."""
        try:
            client = self.config_entry.runtime_data.client
            model_ids = await client.async_available_models()
            if model_ids:
                LOGGER.debug("Fetched %d models from Copilot CLI", len(model_ids))
                options = [{"value": m, "label": m} for m in model_ids]
                # Ensure the currently-configured model is always in the list
                if current_model and not any(o["value"] == current_model for o in options):
                    options.insert(0, {"value": current_model, "label": f"{current_model} (current)"})
                return options
        except Exception as err:  # noqa: BLE001
            LOGGER.debug("Could not fetch live models (%s), using static list", type(err).__name__)
        # Fall back to static list, ensuring current model is present
        options = list(SUPPORTED_MODELS)
        if current_model and not any(o["value"] == current_model for o in options):
            options.insert(0, {"value": current_model, "label": f"{current_model} (current)"})
        return options
