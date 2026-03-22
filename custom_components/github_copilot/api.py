"""GitHub Copilot SDK Client wrapper."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .copilot_sdk import CopilotClient, ExternalServerConfig, PermissionHandler
from .copilot_sdk.session import CopilotSession

from .const import LOGGER

if TYPE_CHECKING:
    from collections.abc import Sequence


class GitHubCopilotApiClientError(Exception):
    """Exception to indicate a general API error."""


class GitHubCopilotApiClientCommunicationError(
    GitHubCopilotApiClientError,
):
    """Exception to indicate a communication error."""


class GitHubCopilotApiClientAuthenticationError(
    GitHubCopilotApiClientError,
):
    """Exception to indicate an authentication error."""


@dataclass
class CopilotSessionContext:
    """In-memory session context for Copilot SDK conversations."""

    session_id: str
    copilot_session: CopilotSession


class GitHubCopilotApiClient:
    """GitHub Copilot SDK client wrapper."""

    def __init__(
        self,
        model: str = "gpt-4o",
        *,
        client_options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize GitHub Copilot SDK client wrapper."""
        self._model = model
        self._client_options = client_options or {}
        self._client: CopilotClient | None = None
        self._sessions: dict[str, CopilotSessionContext] = {}
        self._session_lock = asyncio.Lock()
        self._client_lock = asyncio.Lock()

    async def async_test_connection(self) -> bool:
        """
        Test the API connection.

        Raises:
            GitHubCopilotApiClientAuthenticationError: If authentication fails.
            GitHubCopilotApiClientCommunicationError: If connection fails.
            GitHubCopilotApiClientError: For other API errors.

        Returns:
            True if connection is successful.

        """
        session = await self.async_create_session()
        try:
            await self.async_send_prompt(session.session_id, "Hello")
        finally:
            await self.async_end_session(session.session_id)
        return True

    async def async_create_session(self) -> CopilotSessionContext:
        """Create a Copilot SDK session."""
        client = await self._ensure_client()
        mcp_url = self._client_options.get("mcp_url", "").strip()
        mcp_servers = None
        if mcp_url:
            mcp_servers = {
                "home_assistant": {
                    "type": "sse",
                    "url": mcp_url,
                    "tools": ["*"],
                }
            }
            LOGGER.debug("Creating session with ha-mcp at %s", mcp_url)
        try:
            copilot_session = await client.create_session(
                on_permission_request=PermissionHandler.approve_all,
                model=self._model,
                mcp_servers=mcp_servers,
            )
        except TimeoutError as exception:
            LOGGER.error(
                "Timeout creating Copilot session with model '%s': %s",
                self._model,
                exception,
            )
            msg = (
                f"Timeout creating session with model '{self._model}'. "
                "The Copilot service may be slow or unavailable."
            )
            raise GitHubCopilotApiClientCommunicationError(msg) from exception
        except ValueError as exception:
            LOGGER.error(
                "Invalid configuration for Copilot session: %s",
                exception,
            )
            msg = (
                f"Invalid session configuration for model '{self._model}': "
                f"{exception}"
            )
            raise GitHubCopilotApiClientError(msg) from exception
        except Exception as exception:
            LOGGER.error(
                "Failed to create Copilot session with model '%s': %s - %s",
                self._model,
                type(exception).__name__,
                str(exception),
            )
            msg = (
                f"Unable to start Copilot session with model '{self._model}': "
                f"{type(exception).__name__}. Check the logs for details."
            )
            raise GitHubCopilotApiClientError(msg) from exception

        session_context = CopilotSessionContext(
            session_id=copilot_session.session_id,
            copilot_session=copilot_session,
        )
        async with self._session_lock:
            self._sessions[session_context.session_id] = session_context
        LOGGER.debug(
            "Created Copilot session %s with model '%s'",
            session_context.session_id,
            self._model,
        )
        return session_context

    async def async_end_session(self, session_id: str) -> None:
        """Disconnect a Copilot SDK session."""
        async with self._session_lock:
            session = self._sessions.pop(session_id, None)
        if not session:
            return
        try:
            await session.copilot_session.disconnect()
        except Exception as exception:
            LOGGER.error(
                "Failed to disconnect Copilot session: %s",
                type(exception).__name__,
            )
            msg = "Unable to clean up Copilot session."
            raise GitHubCopilotApiClientError(msg) from exception

    async def async_send_prompt(self, session_id: str, prompt: str) -> str:
        """Send a prompt to an existing Copilot SDK session and wait for the response."""
        if not prompt.strip():
            msg = "Prompt cannot be empty. Please provide a message."
            LOGGER.error(msg)
            raise GitHubCopilotApiClientError(msg)

        async with self._session_lock:
            session = self._sessions.get(session_id)
        if not session:
            msg = f"Session '{session_id}' not found. The session may have expired."
            LOGGER.error(msg)
            raise GitHubCopilotApiClientError(msg)

        done = asyncio.Event()
        response_content: list[str] = []

        def on_event(event: Any) -> None:
            event_type = (
                event.type.value
                if hasattr(event.type, "value")
                else str(event.type)
            )
            if event_type == "assistant.message":
                content = getattr(event.data, "content", None)
                if content:
                    response_content.append(content)
                    LOGGER.debug(
                        "Received assistant.message for session %s (%d chars)",
                        session_id,
                        len(content),
                    )
            elif event_type == "session.idle":
                LOGGER.debug(
                    "session.idle received for session %s — response complete",
                    session_id,
                )
                done.set()
            elif event_type in ("session.error", "error"):
                LOGGER.error(
                    "Copilot session %s reported an error event: %s",
                    session_id,
                    event,
                )
                done.set()

        unsubscribe = session.copilot_session.on(on_event)
        try:
            LOGGER.debug(
                "Sending prompt to session %s: %.80s...",
                session_id,
                prompt,
            )
            await session.copilot_session.send(prompt)
            try:
                await asyncio.wait_for(done.wait(), timeout=120.0)
            except TimeoutError as exception:
                LOGGER.error(
                    "Copilot session %s timed out after 120 s waiting for response",
                    session_id,
                )
                msg = (
                    "Request timed out waiting for Copilot response. "
                    "Please try again or check your connection."
                )
                raise GitHubCopilotApiClientCommunicationError(msg) from exception
        except (
            GitHubCopilotApiClientCommunicationError,
            GitHubCopilotApiClientError,
        ):
            raise
        except ConnectionError as exception:
            LOGGER.error(
                "Connection error in Copilot session %s: %s",
                session_id,
                exception,
            )
            msg = "Lost connection to Copilot. Please check your network and try again."
            raise GitHubCopilotApiClientCommunicationError(msg) from exception
        except Exception as exception:
            LOGGER.error(
                "Copilot session %s error: %s - %s",
                session_id,
                type(exception).__name__,
                str(exception),
            )
            msg = (
                f"Copilot failed to respond: {type(exception).__name__}. "
                "Please check the logs for details."
            )
            raise GitHubCopilotApiClientError(msg) from exception
        finally:
            unsubscribe()

        if not response_content:
            msg = (
                "No response received from Copilot. "
                "The service may be experiencing issues."
            )
            LOGGER.error(msg)
            raise GitHubCopilotApiClientError(msg)

        return response_content[-1]

    async def async_close(self) -> None:
        """Close the Copilot SDK client and all sessions."""
        async with self._session_lock:
            session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            with suppress(GitHubCopilotApiClientError):
                await self.async_end_session(session_id)
        async with self._client_lock:
            if self._client:
                await self._client.stop()
                self._client = None

    async def _ensure_client(self) -> CopilotClient:
        """Ensure the Copilot SDK client is started and connected to the add-on."""
        async with self._client_lock:
            if self._client:
                return self._client

            cli_url = self._client_options.get("cli_url", "").strip()
            if not cli_url:
                msg = (
                    "No Copilot CLI URL configured. "
                    "Please set the add-on URL (e.g. http://local-github_copilot_bridge:7681) "
                    "in the integration settings."
                )
                LOGGER.error(msg)
                raise GitHubCopilotApiClientCommunicationError(msg)

            LOGGER.debug("Initialising Copilot SDK client with cli_url=%s", cli_url)
            try:
                client = CopilotClient(ExternalServerConfig(url=cli_url))
            except (TypeError, ValueError) as exception:
                LOGGER.error(
                    "Invalid Copilot client configuration (cli_url=%s): %s",
                    cli_url,
                    type(exception).__name__,
                )
                msg = "Invalid Copilot client configuration. Please check the add-on URL."
                raise GitHubCopilotApiClientError(msg) from exception
            except Exception as exception:
                LOGGER.error(
                    "Unexpected error initialising Copilot client (cli_url=%s): %s - %s",
                    cli_url,
                    type(exception).__name__,
                    str(exception),
                )
                msg = f"Unable to initialise Copilot client: {type(exception).__name__}"
                raise GitHubCopilotApiClientError(msg) from exception

            LOGGER.debug(
                "Calling client.start() to connect to add-on at %s...",
                cli_url,
            )
            try:
                await client.start()
            except ConnectionRefusedError as exception:
                LOGGER.error(
                    "Connection refused by Copilot add-on at %s. "
                    "Is the add-on running? Check the add-on logs.",
                    cli_url,
                )
                msg = (
                    f"Connection refused by the Copilot add-on at {cli_url}. "
                    "Ensure the GitHub Copilot Bridge add-on is running."
                )
                raise GitHubCopilotApiClientCommunicationError(msg) from exception
            except OSError as exception:
                LOGGER.error(
                    "Network error connecting to Copilot add-on at %s: %s - %s",
                    cli_url,
                    type(exception).__name__,
                    str(exception),
                )
                msg = (
                    f"Network error connecting to Copilot add-on at {cli_url}: "
                    f"{type(exception).__name__}. Check that the URL is correct and "
                    "the add-on is running."
                )
                raise GitHubCopilotApiClientCommunicationError(msg) from exception
            except Exception as exception:
                LOGGER.error(
                    "Failed to connect to Copilot add-on at %s: %s - %s",
                    cli_url,
                    type(exception).__name__,
                    str(exception),
                )
                msg = (
                    f"Unable to connect to Copilot add-on at {cli_url}: "
                    f"{type(exception).__name__}. Check the logs for details."
                )
                raise GitHubCopilotApiClientCommunicationError(msg) from exception

            LOGGER.info(
                "Successfully connected to GitHub Copilot CLI ACP server at %s",
                cli_url,
            )
            self._client = client
            return client

    async def async_available_models(self) -> Sequence[str]:
        """Return available model IDs from the Copilot SDK."""
        client = await self._ensure_client()
        try:
            models = await client.list_models()
        except Exception as exception:
            LOGGER.error(
                "Failed to list Copilot models: %s",
                type(exception).__name__,
            )
            msg = "Unable to fetch Copilot models."
            raise GitHubCopilotApiClientCommunicationError(msg) from exception
        return [model.id for model in models]
