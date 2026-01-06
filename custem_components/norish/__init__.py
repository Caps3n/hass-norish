import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_PASSWORD
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "todo", "calendar"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    base_url = entry.data.get(CONF_URL).rstrip('/')
    api_key = entry.data.get(CONF_PASSWORD)

    # Wir senden den Key doppelt (als Header und als Bearer Token)
    headers = {
        "x-api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    session = aiohttp.ClientSession(headers=headers)
    api_data = {"url": base_url, "session": session}
    
    from .coordinator import NorishListCoordinator
    coordinator = NorishListCoordinator(hass, api_data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True