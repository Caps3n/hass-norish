"""Norish Home Assistant Integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_URL, DOMAIN
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor", "todo", "calendar", "camera", "media_player"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Norish from a config entry."""
    raw_url: str = entry.data.get(CONF_URL) or DEFAULT_URL
    base_url = raw_url.rstrip("/")
    api_key: str = entry.data.get(CONF_API_KEY, "")

    headers: dict[str, Any] = {
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
        "x-api-key": api_key,
    }

    session = async_get_clientsession(hass)

    api_data: dict[str, Any] = {
        "url": base_url,
        "session": session,
        "headers": headers,
    }

    coordinator = NorishListCoordinator(hass, api_data, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Norish integration loaded successfully")
    except ConfigEntryAuthFailed:
        raise  # API key definitively expired (3+ failures) – user must reconfigure
    except Exception as err:  # noqa: BLE001
        # This intentionally catches ConfigEntryNotReady too.
        # When _async_update_data raises UpdateFailed (auth count < threshold),
        # async_config_entry_first_refresh converts it to ConfigEntryNotReady.
        # If we re-raised that, HA would retry async_setup_entry with a NEW
        # coordinator – resetting the sliding-window counter to zero every time,
        # so the threshold is never reached (counter stuck at 1/3 forever).
        # Instead, we load the integration with empty/stale data. The coordinator
        # persists and retries on the next poll, letting the sliding-window
        # counter accumulate across polls until it reaches the threshold.
        _LOGGER.warning(
            "Norish: initial data fetch failed (%s) – loading integration anyway", err
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
