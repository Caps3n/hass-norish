"""Norish Home Assistant Integration.

v1.6.0 – Session-based auth via email/password with auto-refresh.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .auth import NorishAuthError, NorishAuthManager, NorishConnectionError
from .const import DEFAULT_URL, DOMAIN
from .coordinator import NorishCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor", "todo", "calendar", "camera", "media_player"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Norish from a config entry."""
    raw_url: str = entry.data.get(CONF_URL) or DEFAULT_URL
    base_url = raw_url.rstrip("/")
    email: str = entry.data.get(CONF_EMAIL, "")
    password: str = entry.data.get(CONF_PASSWORD, "")

    # Create auth manager and log in
    auth = NorishAuthManager(hass, base_url)

    try:
        await auth.login(email, password)
    except NorishAuthError as err:
        raise ConfigEntryAuthFailed(
            f"Norish login failed: {err}"
        ) from err
    except NorishConnectionError as err:
        _LOGGER.error("Norish: cannot connect during setup: %s", err)
        # Load anyway – coordinator will retry on next poll
        _LOGGER.warning(
            "Norish: loading integration without active session, "
            "will retry login on first poll"
        )

    coordinator = NorishCoordinator(hass, entry, auth)

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

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "auth": auth,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        auth: NorishAuthManager = entry_data.get("auth")
        if auth:
            auth.logout()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
