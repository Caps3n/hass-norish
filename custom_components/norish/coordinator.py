import logging
import json
import urllib.parse
from datetime import timedelta, date
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class NorishListCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_data):
        super().__init__(
            hass, _LOGGER, name="Norish API",
            update_interval=timedelta(seconds=30),
        )
        self.api_data = api_data
        self.store_map = {} 

    async def _fetch_trpc(self, procedure, payload=None):
        """Holt Daten via GET (funktioniert für Kalender/Sensoren)."""
        trpc_input = {"0": {"json": payload}}
        encoded = urllib.parse.quote(json.dumps(trpc_input, separators=(',', ':')))
        url = f"{self.api_data['url']}/api/trpc/{procedure}?batch=1&input={encoded}"
        
        try:
            # Die Session hat die Header bereits aus der __init__.py
            async with self.api_data["session"].get(url) as resp:
                if resp.status == 401:
                    _LOGGER.error(f"Norish Zugriff verweigert (401) bei {procedure}")
                    return None
                if resp.status != 200:
                    return None
                return await resp.json()
        except Exception as e:
            _LOGGER.error(f"Verbindung zu Norish fehlgeschlagen: {e}")
            return None

    async def _async_update_data(self):
        try:
            data = {"calendar": [], "groceries": {"unsorted": []}}
            
            # 1. Läden
            s_data = await self._fetch_trpc("stores.list")
            if s_data:
                res = s_data[0].get("result", {}).get("data", {}).get("json", [])
                for s in res:
                    self.store_map[str(s.get("id"))] = s.get("name")
                    data["groceries"][str(s.get("id"))] = []

            # 2. Kalender
            today = date.today()
            s_iso = (today - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")
            e_iso = (today + timedelta(days=14)).strftime("%Y-%m-%dT23:59:59.000Z")
            c_data = await self._fetch_trpc("calendar.listRecipes", {"startISO": s_iso, "endISO": e_iso})
            if c_data:
                data["calendar"] = c_data[0].get("result", {}).get("data", {}).get("json", [])

            # 3. Einkaufsliste
            g_data = await self._fetch_trpc("groceries.list")
            if g_data:
                res_json = g_data[0].get("result", {}).get("data", {}).get("json", [])
                items = res_json.get("groceries", []) if isinstance(res_json, dict) else res_json
                for item in items:
                    sid = str(item.get("storeId")) if item.get("storeId") else "unsorted"
                    if sid not in data["groceries"]: data["groceries"][sid] = []
                    data["groceries"][sid].append(item)
            return data
        except Exception as e:
            raise UpdateFailed(f"Update Fehler: {e}")

    async def mutate_trpc(self, procedure, payload):
        """POST-Anfrage für Änderungen (To-Do hinzufügen/abhaken)."""
        url = f"{self.api_data['url']}/api/trpc/{procedure}?batch=1"
        
        # WICHTIG: Norish tRPC Mutation Format
        post_data = {"0": {"json": payload}}
        
        try:
            # Wir nutzen die session, die den API-Key in den Headern hat
            async with self.api_data["session"].post(url, json=post_data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error(f"Mutation Error {resp.status}: {text}")
                    return False
                return True
        except Exception as e:
            _LOGGER.error(f"Mutation fehlgeschlagen: {e}")
            return False