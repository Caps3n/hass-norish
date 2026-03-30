"""Config flow for Norish integration.

v1.6.0 – Uses email/password login via better-auth instead of API keys.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_URL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import NorishAuthError, NorishAuthManager, NorishConnectionError
from .const import DOMAIN, ERROR_CANNOT_CONNECT, ERROR_INVALID_AUTH, ERROR_UNKNOWN

_LOGGER = logging.getLogger(__name__)


class NorishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norish."""

    VERSION = 2  # Bumped for email/password schema change

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                auth = NorishAuthManager(
                    self.hass, user_input[CONF_URL]
                )
                await auth.validate_credentials(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
                return self.async_create_entry(title="Norish", data=user_input)

            except NorishAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except NorishConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during Norish setup")
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="https://norish.example.com"): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration – update URL, email, or password."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        current_url = (
            entry.data.get(CONF_URL, "https://norish.example.com")
            if entry else "https://norish.example.com"
        )
        current_email = entry.data.get(CONF_EMAIL, "") if entry else ""

        if user_input is not None:
            try:
                auth = NorishAuthManager(
                    self.hass, user_input[CONF_URL]
                )
                await auth.validate_credentials(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
                return self.async_update_reload_and_abort(
                    entry,
                    data=user_input,
                    reason="reconfigure_successful",
                )
            except NorishAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except NorishConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "Unexpected exception during Norish reconfiguration"
                )
                errors["base"] = ERROR_UNKNOWN

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): str,
                vol.Required(CONF_EMAIL, default=current_email): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure", data_schema=data_schema, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle re-authentication when session has expired."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication with new credentials."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(
            self.context.get("entry_id", "")
        )

        if user_input is not None:
            try:
                url = entry.data.get(CONF_URL, "") if entry else ""
                auth = NorishAuthManager(self.hass, url)
                await auth.validate_credentials(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
                new_data = {**entry.data, **user_input} if entry else user_input
                return self.async_update_reload_and_abort(
                    entry,
                    data=new_data,
                    reason="reauth_successful",
                )
            except NorishAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except NorishConnectionError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during re-auth")
                errors["base"] = ERROR_UNKNOWN

        current_email = entry.data.get(CONF_EMAIL, "") if entry else ""

        data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL, default=current_email): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=data_schema,
            errors=errors,
        )
