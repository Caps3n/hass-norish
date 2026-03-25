"""Config flow for Norish integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, ERROR_CANNOT_CONNECT, ERROR_INVALID_AUTH, ERROR_UNKNOWN

_LOGGER = logging.getLogger(__name__)


class NorishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norish."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_credentials(
                    user_input[CONF_URL], user_input[CONF_API_KEY]
                )
                return self.async_create_entry(title="Norish", data=user_input)

            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except InvalidAuth:
                errors["base"] = ERROR_INVALID_AUTH
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during Norish setup")
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="https://norish.example.com"): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration – allows updating URL and API key."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        current_url = entry.data.get(CONF_URL, "https://norish.example.com") if entry else "https://norish.example.com"

        if user_input is not None:
            try:
                await self._validate_credentials(
                    user_input[CONF_URL], user_input[CONF_API_KEY]
                )
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                    reason="reconfigure_successful",
                )
            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except InvalidAuth:
                errors["base"] = ERROR_INVALID_AUTH
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during Norish reconfiguration")
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure", data_schema=data_schema, errors=errors
        )

    async def _validate_credentials(self, url: str, api_key: str) -> None:
        """Validate the credentials by testing both groceries and calendar endpoints."""
        session = async_get_clientsession(self.hass)
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json",
            "User-Agent": "HomeAssistant/Norish",
        }
        base_url = url.rstrip("/")

        try:
            # Test groceries endpoint
            async with session.get(
                f"{base_url}/api/trpc/groceries.list"
                "?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status >= 400:
                    raise CannotConnect

            # Also test calendar endpoint (requires same auth)
            async with session.get(
                f"{base_url}/api/trpc/calendar.listItems"
                "?batch=1&input=%7B%220%22%3A%7B%22json%22%3A%7B%22startISO%22%3A%222000-01-01%22%2C%22endISO%22%3A%222000-01-02%22%7D%7D%7D",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status >= 400:
                    raise CannotConnect

        except (CannotConnect, InvalidAuth):
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error("Norish: connection error while validating credentials: %s", err)
            raise CannotConnect from err


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
