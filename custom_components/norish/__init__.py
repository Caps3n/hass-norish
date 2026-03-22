"""Norish Integration für Home Assistant."""
import logging
from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_URL
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

    headers = {
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
        "x-api-key": api_key,
    }

    session = async_get_clientsession(hass)

    api_data: Dict[str, Any] = {
        "url": base_url,
        "session": session,
        "headers": headers,
    }

    coordinator = NorishListCoordinator(hass, api_data)

    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Norish Integration erfolgreich geladen")
    except Exception as e:
        _LOGGER.warning(f"Norish: Erster Abruf fehlgeschlagen ({e}), Integration wird trotzdem geladen")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
