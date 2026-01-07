import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_EMAIL, CONF_PASSWORD
from .const import DOMAIN, DEFAULT_URL
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "todo", "calendar"]

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    raw_url = entry.data.get(CONF_URL) or DEFAULT_URL
    base_url = raw_url.rstrip('/')
    
    email = entry.data.get(CONF_EMAIL)
    password = entry.data.get(CONF_PASSWORD)

    cookie_jar = aiohttp.CookieJar(unsafe=True)
    headers = {
        "User-Agent": "HomeAssistant/Norish",
        "Accept": "application/json",
        "Origin": base_url,
        "Referer": f"{base_url}/login"
    }
    
    session = aiohttp.ClientSession(cookie_jar=cookie_jar, headers=headers)
    
    try:
        _LOGGER.info(f"Norish: Login-Versuch bei {base_url}")
        
        # 1. CSRF holen (Ignorieren wir bei Fehler, BetterAuth braucht es manchmal nicht)
        csrf_token = ""
        try:
            async with session.get(f"{base_url}/api/auth/csrf", timeout=10) as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    csrf_token = json_data.get("csrfToken", "")
        except: pass

        # 2. Login mit Redirect-Verbot!
        login_url = f"{base_url}/api/auth/callback/credentials"
        payload = {
            "email": email,
            "password": password,
            "csrfToken": csrf_token,
            "json": "true"
        }
        
        # WICHTIG: allow_redirects=False verhindert den 0.0.0.0 Crash!
        async with session.post(login_url, json=payload, allow_redirects=False) as resp:
            # Wir akzeptieren 200 (OK) oder 302/303 (Redirect) als Erfolg,
            # solange wir Cookies bekommen haben.
            if len(session.cookie_jar) > 0:
                _LOGGER.info(f"Norish: Login erfolgreich! (Status {resp.status})")
            else:
                _LOGGER.error(f"Norish: Login fehlgeschlagen. Status: {resp.status}")

    except Exception as e:
        _LOGGER.error(f"Norish Setup Fehler: {e}")

    api_data = {"url": base_url, "session": session}
    coordinator = NorishListCoordinator(hass, api_data)
    await coordinator.async_config_entry_first_refresh()

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