"""Norish Integration für Home Assistant."""
import logging
from typing import Dict, Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_URL, UPDATE_INTERVAL_SECONDS
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "todo", "calendar", "camera", "media_player"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Norish component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Norish from a config entry."""
    raw_url = entry.data.get(CONF_URL) or DEFAULT_URL
    base_url = raw_url.rstrip("/")

    api_key = entry.data.get(CONF_API_KEY)

    # Header-Konfiguration
    headers = {
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
        "x-api-key": api_key,
    }

    # Nutze die Standard-Session von Home Assistant
    # Diese Session hat bereits Connection Pooling und ist optimal konfiguriert
    session = async_get_clientsession(hass)

    api_data: Dict[str, Any] = {
        "url": base_url,
        "session": session,
        "headers": headers,  # Headers separat speichern
    }

    coordinator = NorishListCoordinator(hass, api_data)

    # Erster Abruf mit Fehlerbehandlung
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Norish Integration erfolgreich geladen")
    except Exception as e:
        _LOGGER.warning(
            "Norish: Erster Abruf fehlgeschlagen (%s), "
            "Integration wird trotzdem geladen",
            e,
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup aller Plattformen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Session wird von Home Assistant verwaltet, nicht manuell schließen
        return True
    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
