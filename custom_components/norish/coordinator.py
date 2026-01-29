import logging
import json
import asyncio
import urllib.parse
from datetime import timedelta, date
from typing import Optional, Dict, Any, List
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import aiohttp

_LOGGER = logging.getLogger(__name__)

# Konstanten
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1  # Sekunden für exponentielles Backoff


class NorishListCoordinator(DataUpdateCoordinator):
    """Coordinator für Norish API mit verbesserter Fehlerbehandlung."""

    def __init__(self, hass, api_data: Dict[str, Any]):
        super().__init__(
            hass,
            _LOGGER,
            name="Norish API",
            update_interval=timedelta(minutes=5),  # Weniger aggressiv
        )
        self.api_data = api_data
        self.store_map: Dict[str, str] = {}
        self._last_successful_update: Optional[date] = None

    def _safe_get_trpc_result(
        self, data: Optional[List], default: Any = None
    ) -> Any:
        """Extrahiert tRPC Ergebnis sicher mit Validierung."""
        if not data or not isinstance(data, list) or len(data) == 0:
            _LOGGER.debug("Leere oder ungültige tRPC Antwort")
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
        """
        Holt Daten via GET mit Retry-Logik.

        Args:
            procedure: tRPC Prozedurname
            payload: Optional payload für die Anfrage

        Returns:
            JSON Antwort oder None bei Fehler
        """
        trpc_input = {"0": {"json": payload}} if payload else {"0": {"json": None}}
        encoded = urllib.parse.quote(
            json.dumps(trpc_input, separators=(",", ":"))
        )
        url = f"{self.api_data['url']}/api/trpc/{procedure}?batch=1&input={encoded}"

        # Headers aus api_data holen
        headers = self.api_data.get("headers", {})

        for attempt in range(MAX_RETRIES):
            try:
                async with self.api_data["session"].get(
                    url, 
                    headers=headers,  # Headers explizit übergeben
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    # Status-Code Handling
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
                _LOGGER.error(f"Timeout bei {procedure} nach {MAX_RETRIES} Versuchen")
                return None

            except aiohttp.ClientError as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2**attempt)
                    _LOGGER.warning(
                        f"Verbindungsfehler bei {procedure}: {e}, "
                        f"Retry {attempt + 1}/{MAX_RETRIES} in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    f"Verbindung zu Norish fehlgeschlagen bei {procedure}: {e}"
                )
                return None

            except Exception as e:
                _LOGGER.exception(
                    f"Unerwarteter Fehler bei tRPC Aufruf {procedure}: {e}"
                )
                return None

        return None

    async def _async_update_data(self) -> Dict[str, Any]:
        """Aktualisiert alle Daten von der Norish API."""
        try:
            data = {
                "calendar": [],
                "groceries": {"unsorted": []},
                "last_update": None,
            }

            # 1. Läden abrufen (nur wenn noch nicht geladen oder täglich)
            if not self.store_map or self._should_refresh_stores():
                await self._fetch_stores(data)

            # 2. Kalender abrufen
            await self._fetch_calendar(data)

            # 3. Einkaufsliste abrufen
            await self._fetch_groceries(data)

            # Update-Zeit speichern
            data["last_update"] = date.today()
            self._last_successful_update = date.today()

            return data

        except Exception as e:
            _LOGGER.exception(f"Fehler beim Aktualisieren der Norish Daten: {e}")
            raise UpdateFailed(f"Update Fehler: {e}")

    def _should_refresh_stores(self) -> bool:
        """Prüft, ob Store-Liste neu geladen werden sollte."""
        if not self._last_successful_update:
            return True
        # Stores nur einmal täglich neu laden
        return self._last_successful_update < date.today()

    async def _fetch_stores(self, data: Dict[str, Any]) -> None:
        """Lädt die Liste der Geschäfte."""
        s_data = await self._fetch_trpc("stores.list")
        if not s_data:
            _LOGGER.warning("Keine Store-Daten erhalten")
            return

        stores = self._safe_get_trpc_result(s_data, [])
        if not isinstance(stores, list):
            _LOGGER.error(f"Unerwartetes Store-Format: {type(stores)}")
            return

        for store in stores:
            if not isinstance(store, dict):
                continue
            store_id = str(store.get("id", ""))
            store_name = store.get("name", f"Store {store_id}")
            if store_id:
                self.store_map[store_id] = store_name
                data["groceries"][store_id] = []

        _LOGGER.debug(f"Stores geladen: {len(self.store_map)} Geschäfte")

    async def _fetch_calendar(self, data: Dict[str, Any]) -> None:
        """Lädt Kalender-Einträge."""
        today = date.today()
        start_iso = (today - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")
        end_iso = (today + timedelta(days=14)).strftime("%Y-%m-%dT23:59:59.000Z")

        c_data = await self._fetch_trpc(
            "calendar.listRecipes", {"startISO": start_iso, "endISO": end_iso}
        )

        if c_data:
            calendar_items = self._safe_get_trpc_result(c_data, [])
            if isinstance(calendar_items, list):
                data["calendar"] = calendar_items
                _LOGGER.debug(f"Kalender geladen: {len(calendar_items)} Einträge")
            else:
                _LOGGER.warning(
                    f"Unerwartetes Kalender-Format: {type(calendar_items)}"
                )

    async def _fetch_groceries(self, data: Dict[str, Any]) -> None:
        """Lädt die Einkaufsliste."""
        g_data = await self._fetch_trpc("groceries.list")
        if not g_data:
            _LOGGER.warning("Keine Grocery-Daten erhalten")
            return

        res_json = self._safe_get_trpc_result(g_data, [])

        # Flexibles Handling: manchmal Dict mit 'groceries', manchmal direkt Liste
        items = []
        if isinstance(res_json, dict):
            items = res_json.get("groceries", [])
        elif isinstance(res_json, list):
            items = res_json
        else:
            _LOGGER.warning(f"Unerwartetes Grocery-Format: {type(res_json)}")
            return

        if not isinstance(items, list):
            _LOGGER.error(f"Groceries sind keine Liste: {type(items)}")
            return

        # Items zu Stores zuordnen
        for item in items:
            if not isinstance(item, dict):
                continue

            store_id = item.get("storeId")
            store_key = str(store_id) if store_id else "unsorted"

            # Erstelle Store-Liste falls nicht vorhanden
            if store_key not in data["groceries"]:
                data["groceries"][store_key] = []

            data["groceries"][store_key].append(item)

        _LOGGER.debug(f"Groceries geladen: {len(items)} Artikel")

    async def mutate_trpc(self, procedure: str, payload: Dict) -> bool:
        """
        POST-Anfrage für Änderungen mit Fehlerbehandlung.

        Args:
            procedure: tRPC Prozedurname
            payload: Payload für die Mutation

        Returns:
            True bei Erfolg, False bei Fehler
        """
        url = f"{self.api_data['url']}/api/trpc/{procedure}?batch=1"
        post_data = {"0": {"json": payload}}
        
        # Headers aus api_data holen
        headers = self.api_data.get("headers", {})

        for attempt in range(MAX_RETRIES):
            try:
                async with self.api_data["session"].post(
                    url, 
                    json=post_data,
                    headers=headers,  # Headers explizit übergeben
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 401:
                        _LOGGER.error(
                            f"Zugriff verweigert bei Mutation {procedure}. "
                            "Prüfe API Key."
                        )
                        return False

                    if resp.status >= 500 and attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAY_BASE * (2**attempt)
                        _LOGGER.warning(
                            f"Server-Fehler bei Mutation, Retry in {delay}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.error(
                            f"Mutation Error {resp.status} bei {procedure}: "
                            f"{text[:200]}"
                        )
                        return False

                    _LOGGER.debug(f"Mutation erfolgreich: {procedure}")
                    return True

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_BASE * (2**attempt))
                    continue
                _LOGGER.error(f"Timeout bei Mutation {procedure}")
                return False

            except aiohttp.ClientError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_BASE * (2**attempt))
                    continue
                _LOGGER.error(f"Mutation fehlgeschlagen: {e}")
                return False

            except Exception as e:
                _LOGGER.exception(f"Unerwarteter Fehler bei Mutation: {e}")
                return False

        return False
