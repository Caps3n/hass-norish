"""Norish Home Assistant Integration.

v1.6.10 – Catch TimeoutError during startup validation so HA retries via ConfigEntryNotReady.
"""
from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_NORISH_EMAIL, CONF_NORISH_PASSWORD, DEFAULT_URL, DOMAIN
from .coordinator import NorishCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor", "todo", "calendar", "camera", "media_player"]


async def _validate_api_key(hass: HomeAssistant, base_url: str, api_key: str) -> None:
    """Quick validation that the API key works (single GET)."""
    session = async_get_clientsession(hass)
    headers = {
        "x-api-key": api_key,
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
    }
    url = (
        f"{base_url}/api/trpc/groceries.list"
        "?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D"
    )
    try:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 401:
                raise ConfigEntryAuthFailed("Norish API key invalid or expired")
            if resp.status >= 500:
                raise ConfigEntryNotReady(
                    f"Norish server error ({resp.status}) during setup"
                )
    except (aiohttp.ClientError, TimeoutError) as err:
        raise ConfigEntryNotReady(f"Cannot connect to Norish: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Norish from a config entry."""
    raw_url: str = entry.data.get(CONF_URL) or DEFAULT_URL
    base_url = raw_url.rstrip("/")
    api_key: str = entry.data.get(CONF_API_KEY, "")
    norish_email: str = entry.data.get(CONF_NORISH_EMAIL, "")
    norish_password: str = entry.data.get(CONF_NORISH_PASSWORD, "")

    # Quick check that the key is still valid
    await _validate_api_key(hass, base_url, api_key)

    coordinator = NorishCoordinator(
        hass, entry, base_url, api_key,
        norish_email=norish_email,
        norish_password=norish_password,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Norish integration loaded successfully")
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "Norish: initial data fetch failed (%s) – loading integration anyway",
            err,
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
