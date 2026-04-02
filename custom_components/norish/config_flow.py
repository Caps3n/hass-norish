"""Config flow for Norish integration.

v1.6.5 – Options flow fixed for HA 2024.11+ API (self.config_entry, @callback).
"""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
)

from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_URL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    POLL_INTERVAL_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


async def _test_api_key(hass, base_url: str, api_key: str) -> str | None:
    """Test the API key against the Norish API.

    Returns None on success, or an error key on failure.
    """
    session = async_get_clientsession(hass)
    headers = {
        "x-api-key": api_key,
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
    }
    url = (
        f"{base_url.rstrip('/')}/api/trpc/groceries.list"
        "?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D"
    )
    try:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 401:
                return ERROR_INVALID_AUTH
            if resp.status >= 400:
                return ERROR_CANNOT_CONNECT
    except aiohttp.ClientError:
        return ERROR_CANNOT_CONNECT
    except Exception:  # noqa: BLE001
        return ERROR_UNKNOWN
    return None


def _poll_interval_selector() -> SelectSelector:
    """Return a dropdown selector for the poll interval."""
    options = [
        SelectOptionDict(value=str(seconds), label=label)
        for seconds, label in POLL_INTERVAL_OPTIONS.items()
    ]
    return SelectSelector(
        SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
    )


class NorishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norish."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return NorishOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await _test_api_key(
                self.hass,
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
            )
            if error is None:
                return self.async_create_entry(title="Norish", data=user_input)
            errors["base"] = error

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=DEFAULT_URL): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration – update URL or API key."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        current_url = (
            entry.data.get(CONF_URL, DEFAULT_URL)
            if entry else DEFAULT_URL
        )

        if user_input is not None:
            error = await _test_api_key(
                self.hass,
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
            )
            if error is None:
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                    reason="reconfigure_successful",
                )
            errors["base"] = error

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure", data_schema=data_schema, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle re-authentication when API key has expired."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication with a new API key."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(
            self.context.get("entry_id", "")
        )

        if user_input is not None:
            url = entry.data.get(CONF_URL, DEFAULT_URL) if entry else DEFAULT_URL
            error = await _test_api_key(
                self.hass,
                url,
                user_input[CONF_API_KEY],
            )
            if error is None:
                new_data = {**entry.data, **user_input} if entry else user_input
                return self.async_update_reload_and_abort(
                    entry,
                    data=new_data,
                    reason="reauth_successful",
                )
            errors["base"] = error

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=data_schema,
            errors=errors,
        )


class NorishOptionsFlow(config_entries.OptionsFlow):
    """Handle Norish options (poll interval).

    Uses self.config_entry (HA 2024.11+ API) — no __init__ needed.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the options form."""
        if user_input is not None:
            # Convert the string value from the selector back to int
            poll_interval = int(user_input[CONF_POLL_INTERVAL])
            return self.async_create_entry(
                title="",
                data={CONF_POLL_INTERVAL: poll_interval},
            )

        # Current value (default 15 min) — self.config_entry provided by HA
        current_interval = str(
            self.config_entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLL_INTERVAL,
                    default=current_interval,
                ): _poll_interval_selector(),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
