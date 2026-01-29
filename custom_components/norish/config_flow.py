"""Config Flow für Norish Integration mit Validierung."""
import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_URL, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    DOMAIN,
    DEFAULT_URL,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_AUTH,
    ERROR_UNKNOWN,
    DEFAULT_SHOW_BREAKFAST,
    DEFAULT_SHOW_LUNCH,
    DEFAULT_SHOW_DINNER,
    DEFAULT_SHOW_SNACK,
)

_LOGGER = logging.getLogger(__name__)


class NorishConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norish."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validiere die Eingaben
            try:
                await self._validate_credentials(
                    user_input[CONF_URL], user_input[CONF_API_KEY]
                )

                # Erstelle eindeutige ID basierend auf URL
                await self.async_set_unique_id(user_input[CONF_URL].rstrip("/"))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Norish", data=user_input
                )

            except CannotConnect:
                errors["base"] = ERROR_CANNOT_CONNECT
            except InvalidAuth:
                errors["base"] = ERROR_INVALID_AUTH
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unerwarteter Fehler bei der Validierung")
                errors["base"] = ERROR_UNKNOWN

        # Schema für das Eingabeformular
        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=DEFAULT_URL): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _validate_credentials(self, url: str, api_key: str) -> bool:
        """
        Validiert die API-Zugangsdaten durch einen Test-Request.

        Args:
            url: Die Norish Server URL
            api_key: Der API-Schlüssel

        Raises:
            CannotConnect: Wenn Verbindung nicht hergestellt werden kann
            InvalidAuth: Wenn API-Schlüssel ungültig ist

        Returns:
            True wenn Validierung erfolgreich
        """
        base_url = url.rstrip("/")
        headers = {
            "User-Agent": "HomeAssistant/Norish",
            "Accept": "application/json",
            "x-api-key": api_key,
        }

        session = async_create_clientsession(self.hass)

        try:
            # Einfacher Test-Request zu stores.list
            test_url = f"{base_url}/api/trpc/stores.list?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D"

            async with session.get(
                test_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 401 or resp.status == 403:
                    _LOGGER.error(
                        "Norish API-Schlüssel ungültig (Status %d)", resp.status
                    )
                    raise InvalidAuth

                if resp.status == 404:
                    _LOGGER.error(
                        "Norish API-Endpoint nicht gefunden. Prüfe die URL."
                    )
                    raise CannotConnect

                if resp.status >= 500:
                    _LOGGER.error("Norish Server-Fehler (Status %d)", resp.status)
                    raise CannotConnect

                if resp.status != 200:
                    _LOGGER.error(
                        "Unerwarteter Status-Code von Norish: %d", resp.status
                    )
                    raise CannotConnect

                # Prüfe ob Response valides JSON ist
                try:
                    await resp.json()
                except Exception as e:
                    _LOGGER.error("Ungültige JSON-Antwort von Norish: %s", e)
                    raise CannotConnect

                _LOGGER.info("Norish API-Validierung erfolgreich")
                return True

        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Verbindung zu Norish fehlgeschlagen: %s", err)
            raise CannotConnect from err
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP-Fehler bei Norish-Verbindung: %s", err)
            raise CannotConnect from err
        except InvalidAuth:
            raise
        except Exception as err:
            _LOGGER.exception("Unerwarteter Fehler bei Validierung: %s", err)
            raise CannotConnect from err

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "NorishOptionsFlowHandler":
        """Get the options flow for this handler."""
        return NorishOptionsFlowHandler(config_entry)


class NorishOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Norish options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.entry.options or {}
        schema = vol.Schema(
            {
                vol.Optional(
                    "show_breakfast",
                    default=opts.get("show_breakfast", DEFAULT_SHOW_BREAKFAST),
                ): bool,
                vol.Optional(
                    "show_lunch",
                    default=opts.get("show_lunch", DEFAULT_SHOW_LUNCH),
                ): bool,
                vol.Optional(
                    "show_dinner",
                    default=opts.get("show_dinner", DEFAULT_SHOW_DINNER),
                ): bool,
                vol.Optional(
                    "show_snack",
                    default=opts.get("show_snack", DEFAULT_SHOW_SNACK),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
