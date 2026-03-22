"""Config flow for Norish integration."""
import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, ERROR_CANNOT_CONNECT, ERROR_INVALID_AUTH, ERROR_UNKNOWN

_LOGGER = logging.getLogger(__name__)


class NorishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norish."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}

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
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema({
            vol.Required(CONF_URL, default="https://norish.example.com"): str,
            vol.Required(CONF_API_KEY): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def _validate_credentials(self, url: str, api_key: str) -> bool:
        """Validate the credentials."""
        session = async_get_clientsession(self.hass)
        headers = {"x-api-key": api_key, "Accept": "application/json"}
        base_url = url.rstrip("/")

        try:
            async with session.get(
                f"{base_url}/api/trpc/groceries.list?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    raise InvalidAuth()
                if response.status >= 400:
                    raise CannotConnect()
                return True
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Verbindungsfehler: {err}")
            raise CannotConnect() from err


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
