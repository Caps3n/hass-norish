"""Coordinator für Norish API."""
import logging
import json
import asyncio
import urllib.parse
import os
import hashlib
from datetime import timedelta, date
from typing import Optional, Dict, Any, List
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import aiohttp

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2
IMAGE_CACHE_DIR = "www/norish_images"


class NorishListCoordinator(DataUpdateCoordinator):
    """Coordinator für Norish API."""

    def __init__(self, hass, api_data: Dict[str, Any]):
        super().__init__(
            hass,
            _LOGGER,
            name="Norish API",
            update_interval=timedelta(minutes=5),
        )
        self.hass = hass
        self.api_data = api_data
        self.store_map: Dict[str, str] = {}
        self._last_successful_update: Optional[date] = None
        self._image_cache_path = os.path.join(hass.config.config_dir, IMAGE_CACHE_DIR)
        
        # Erstelle Cache-Verzeichnis falls nicht vorhanden
        os.makedirs(self._image_cache_path, exist_ok=True)

    def _safe_get_trpc_result(
        self, data: Optional[List], default: Any = None
    ) -> Any:
        """Extrahiert tRPC Ergebnis sicher."""
        if not data or not isinstance(data, list) or len(data) == 0:
            return default

        try:
            result = data[0].get("result", {})
            if "error" in result:
                error_msg = result["error"].get("message", "Unbekannter Fehler")
                _LOGGER.error(f"tRPC Fehler: {error_msg}")
                return default

            return result.get("data", {}).get("json", default)
        except (KeyError, AttributeError, IndexError) as e:
            _LOGGER.warning(f"Fehler beim Extrahieren des tRPC Ergebnisses: {e}")
            return default

    async def _fetch_trpc(
        self, procedure: str, payload: Optional[Dict] = None
    ) -> Optional[List]:
        """Holt Daten via GET mit Retry-Logik."""
        trpc_input = {"0": {"json": payload}} if payload else {"0": {"json": None}}
        encoded = urllib.parse.quote(
            json.dumps(trpc_input, separators=(",", ":"))
        )
        url = f"{self.api_data['url']}/api/trpc/{procedure}?batch=1&input={encoded}"

        headers = self.api_data.get("headers", {})

        for attempt in range(MAX_RETRIES):
            try:
                async with self.api_data["session"].get(
                    url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 401:
                        _LOGGER.error(
                            f"Norish: Zugriff verweigert (401) bei {procedure}. "
                            "Prüfe den API Key in der Konfiguration."
                        )
                        return None

                    if resp.status == 404:
                        _LOGGER.error(
                            f"Norish: Endpoint nicht gefunden (404): {procedure}"
                        )
                        return None

                    if resp.status >= 500:
                        if attempt < MAX_RETRIES - 1:
                            delay = RETRY_DELAY_BASE * (2**attempt)
                            _LOGGER.warning(
                                f"Server-Fehler {resp.status} bei {procedure}, "
                                f"Retry {attempt + 1}/{MAX_RETRIES} in {delay}s"
                            )
                            await asyncio.sleep(delay)
                            continue
                        _LOGGER.error(
                            f"Norish: Server-Fehler {resp.status} bei {procedure} "
                            f"nach {MAX_RETRIES} Versuchen"
                        )
                        return None

                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.error(
                            f"Norish: Unerwarteter Status {resp.status} "
                            f"bei {procedure}: {text[:200]}"
                        )
                        return None

                    return await resp.json()

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2**attempt)
                    _LOGGER.warning(
                        f"Timeout bei {procedure}, "
                        f"Retry {attempt + 1}/{MAX_RETRIES} in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    f"Norish: Timeout bei {procedure} nach {MAX_RETRIES} Versuchen"
                )
                return None

            except aiohttp.ClientError as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2**attempt)
                    _LOGGER.warning(
                        f"Netzwerkfehler bei {procedure}: {e}, "
                        f"Retry {attempt + 1}/{MAX_RETRIES} in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    f"Norish: Netzwerkfehler bei {procedure}: {e}"
                )
                return None

        return None

    async def _async_update_data(self) -> Dict[str, Any]:
        """Holt alle Norish-Daten."""
        data: Dict[str, Any] = {
            "calendar": [],
            "groceries": [],
            "stores": {},
        }

        try:
            # Kalender-Daten laden
            await self._fetch_calendar(data)
            
            # Rezept-Details für jeden Kalender-Eintrag laden
            await self._fetch_recipe_details_for_calendar(data)
            
            # Bilder lokal cachen
            await self._download_and_cache_images(data)
            
            # Einkaufsliste laden
            await self._fetch_groceries(data)
            
            # Stores laden
            await self._fetch_stores(data)

            self._last_successful_update = date.today()
            
            calendar_count = len(data.get("calendar", []))
            _LOGGER.info(f"Norish: {calendar_count} Kalender-Events geladen")

        except Exception as e:
            _LOGGER.error(f"Fehler beim Abrufen der Norish-Daten: {e}")
            raise UpdateFailed(f"Fehler beim Abrufen: {e}")

        return data

    async def _fetch_calendar(self, data: Dict[str, Any]) -> None:
        """Lädt Kalender-Einträge - Norish v0.16+ API."""
        today = date.today()
        # Norish v0.16+ verwendet NUR Datum ohne Zeit!
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

        _LOGGER.debug(f"Norish: Lade Kalender von {start_date} bis {end_date}")

        # Norish v0.16+ verwendet calendar.listItems (NICHT calendar.listRecipes!)
        c_data = await self._fetch_trpc(
            "calendar.listItems", {"startISO": start_date, "endISO": end_date}
        )

        if c_data:
            calendar_items = self._safe_get_trpc_result(c_data, [])
            if isinstance(calendar_items, list):
                data["calendar"] = calendar_items
                _LOGGER.info(f"Norish: {len(calendar_items)} Kalender-Einträge geladen")
            else:
                _LOGGER.warning(f"Unerwartetes Kalender-Format: {type(calendar_items)}")
        else:
            _LOGGER.warning("Norish: Keine Kalender-Daten erhalten")

    async def _fetch_recipe_details_for_calendar(self, data: Dict[str, Any]) -> None:
        """Lädt Rezept-Details für alle Kalender-Einträge."""
        calendar_items = data.get("calendar", [])
        
        # Sammle unique Recipe IDs
        recipe_ids = set()
        for event in calendar_items:
            recipe_id = event.get("recipeId")
            if recipe_id:
                recipe_ids.add(recipe_id)
        
        if not recipe_ids:
            return
            
        _LOGGER.debug(f"Norish: Lade Details für {len(recipe_ids)} Rezepte")
        
        # Lade Details für jedes Rezept
        recipe_details = {}
        for recipe_id in recipe_ids:
            details = await self._fetch_recipe_details(recipe_id)
            if details:
                recipe_details[recipe_id] = details
        
        # Füge Details zu Kalender-Einträgen hinzu
        for event in calendar_items:
            recipe_id = event.get("recipeId")
            if recipe_id and recipe_id in recipe_details:
                event["_recipe"] = recipe_details[recipe_id]

    async def _fetch_recipe_details(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Lädt Details für ein einzelnes Rezept."""
        try:
            r_data = await self._fetch_trpc("recipes.get", {"id": recipe_id})
            if r_data:
                result = self._safe_get_trpc_result(r_data, None)
                if result:
                    _LOGGER.debug(f"Rezept geladen: {result.get('name', 'unknown')}")
                    return result
        except Exception as e:
            _LOGGER.debug(f"Fehler beim Laden von Rezept {recipe_id}: {e}")
        return None

    async def _fetch_groceries(self, data: Dict[str, Any]) -> None:
        """Lädt die Einkaufsliste."""
        g_data = await self._fetch_trpc("groceries.list")
        
        if not g_data:
            _LOGGER.debug("Norish: Keine Grocery-Daten erhalten")
            return

        items = self._safe_get_trpc_result(g_data, [])
        if not isinstance(items, list):
            _LOGGER.warning(f"Unerwartetes Grocery-Format: {type(items)}")
            return

        data["groceries"] = items
        _LOGGER.debug(f"Norish: {len(items)} Einkaufslisten-Items geladen")

    async def _fetch_stores(self, data: Dict[str, Any]) -> None:
        """Lädt die Store-Liste."""
        s_data = await self._fetch_trpc("stores.list")
        
        if not s_data:
            return

        stores = self._safe_get_trpc_result(s_data, [])
        if isinstance(stores, list):
            # Erstelle Map von Store-ID zu Store-Name
            for store in stores:
                store_id = store.get("id")
                store_name = store.get("name")
                if store_id and store_name:
                    data["stores"][store_id] = store_name

    async def _download_and_cache_images(self, data: Dict[str, Any]) -> None:
        """Lädt Bilder herunter und cached sie lokal."""
        calendar_items = data.get("calendar", [])
        base_url = self.api_data.get("url", "").rstrip("/")
        
        for event in calendar_items:
            recipe_details = event.get("_recipe", {})
            if not recipe_details:
                continue
            
            # Hole Bild-URL aus Rezept-Details
            image_path = recipe_details.get("image") or recipe_details.get("imageUrl")
            if not image_path:
                continue
            
            # Erstelle vollständige URL falls relativ
            if image_path.startswith("/"):
                image_url = f"{base_url}{image_path}"
            else:
                image_url = image_path
            
            # Cache das Bild lokal
            local_path = await self._cache_image(image_url, event.get("recipeId", "unknown"))
            if local_path:
                # Speichere den lokalen Pfad im Event
                event["_local_image"] = local_path

    async def _cache_image(self, image_url: str, recipe_id: str) -> Optional[str]:
        """Lädt ein Bild herunter und cached es lokal. Gibt den lokalen URL-Pfad zurück."""
        try:
            # Erstelle einen eindeutigen Dateinamen basierend auf der URL
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
            filename = f"{recipe_id}_{url_hash}.jpg"
            local_file_path = os.path.join(self._image_cache_path, filename)
            
            # Prüfe ob Bild bereits gecached ist
            if os.path.exists(local_file_path):
                return f"/local/norish_images/{filename}"
            
            # Lade Bild herunter
            headers = self.api_data.get("headers", {})
            session = self.api_data.get("session")
            
            async with session.get(image_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    _LOGGER.debug(f"Konnte Bild nicht laden: {image_url} (Status {resp.status})")
                    return None
                
                image_data = await resp.read()
                
                # Speichere Bild lokal
                with open(local_file_path, 'wb') as f:
                    f.write(image_data)
                
                _LOGGER.debug(f"Bild gecached: {filename}")
                return f"/local/norish_images/{filename}"
                
        except Exception as e:
            _LOGGER.debug(f"Fehler beim Cachen des Bildes {image_url}: {e}")
            return None
