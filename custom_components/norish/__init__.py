import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_API_KEY
from .const import DOMAIN, DEFAULT_URL
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "todo", "calendar"]

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    raw_url = entry.data.get(CONF_URL) or DEFAULT_URL
    base_url = raw_url.rstrip('/')
    
    api_key = entry.data.get(CONF_API_KEY)

    # ÄNDERUNG: Header auf 'x-api-key' geändert. 
    # Falls das auch nicht geht, prüfen Sie bitte, welchen Header Ihr Server erwartet.
    headers = {
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
        "x-api-key": api_key,
        # "Authorization": f"Bearer {api_key}" # Deaktiviert, da 401 Fehler
    }
    
    session = aiohttp.ClientSession(headers=headers)
    
    api_data = {"url": base_url, "session": session}
    coordinator = NorishListCoordinator(hass, api_data)
    
    # Wir fangen den Fehler hier ab, damit die Integration lädt und man die Logs sieht,
    # auch wenn der erste Abruf fehlschlägt.
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        _LOGGER.warning(f"Norish: Erster Abruf fehlgeschlagen ({e}), Integration wird trotzdem geladen.")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api_data["session"].close()
        return True
    return False