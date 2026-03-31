"""Coordinator for the Norish API.

v1.6.3 – Safer poll interval.
- Poll interval increased from 300 s → 900 s (15 min, 4 polls/hour)
- Store list is cached in memory; only re-fetched every 24 hours
- Recipe details are cached; only re-fetched when the set of recipe IDs changes
- HTTP 429 (rate-limited) now raises UpdateFailed instead of silently returning
  None, so Home Assistant retries on the next poll interval instead of marking
  all entities unavailable permanently.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import urllib.parse
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2
IMAGE_CACHE_DIR = "www/norish_images"

# Poll every 15 minutes — very safe margin under the Norish rate limit of 500 req/hour.
# At 4 polls/hour × 3 requests each = ~12 req/hour (was 120 × 10 = 1 200/hour).
POLL_INTERVAL_SECONDS = 900

# How often to re-fetch the store list (it basically never changes).
STORE_REFRESH_HOURS = 24


class NorishCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for the Norish API with API key authentication."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        base_url: str,
        api_key: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Norish API",
            update_interval=timedelta(seconds=POLL_INTERVAL_SECONDS),
            config_entry=entry,
        )
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.store_map: dict[str, str] = {}
        self._last_successful_update: date | None = None
        self._image_cache_path = os.path.join(
            hass.config.config_dir, IMAGE_CACHE_DIR
        )
        os.makedirs(self._image_cache_path, exist_ok=True)

        # --- Caches to avoid redundant API calls ---
        # Store cache: fetch once, refresh every STORE_REFRESH_HOURS
        self._cached_stores: dict[str, str] = {}
        self._stores_last_fetched: datetime | None = None

        # Recipe cache: { recipe_id: recipe_dict }
        # Only invalidated when the set of recipe IDs in the calendar changes.
        self._cached_recipes: dict[str, Any] = {}
        self._cached_recipe_ids: frozenset[str] = frozenset()

    def _get_headers(self) -> dict[str, str]:
        """Return headers for authenticated API requests."""
        return {
            "x-api-key": self._api_key,
            "User-Agent": "HomeAssistant/Norish",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # tRPC helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_get_trpc_result(
        data: list[Any] | None,
        default: Any = None,
    ) -> Any:
        """Safely extract a tRPC result from the batch response."""
        if not data or not isinstance(data, list):
            return default
        try:
            result = data[0].get("result", {})
            if "error" in result:
                _LOGGER.error(
                    "tRPC error in response: %s",
                    result["error"].get("message", "unknown error"),
                )
                return default
            return result.get("data", {}).get("json", default)
        except (KeyError, AttributeError, IndexError) as err:
            _LOGGER.warning("Failed to extract tRPC result: %s", err)
            return default

    async def _fetch_trpc(
        self,
        procedure: str,
        payload: dict[str, Any] | None = None,
    ) -> list[Any] | None:
        """Fetch data from a tRPC endpoint with retry."""
        trpc_input = {"0": {"json": payload if payload is not None else None}}
        encoded = urllib.parse.quote(
            json.dumps(trpc_input, separators=(",", ":"))
        )
        url = f"{self.base_url}/api/trpc/{procedure}?batch=1&input={encoded}"
        session = async_get_clientsession(self.hass)
        headers = self._get_headers()

        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        _LOGGER.error(
                            "Norish: 401 for %s – API key invalid or expired",
                            procedure,
                        )
                        raise ConfigEntryAuthFailed(
                            "Norish API key invalid or expired"
                        )

                    if resp.status == 429:
                        # Rate-limited: tell HA to wait until next poll interval.
                        # Do NOT raise ConfigEntryAuthFailed — that would stop all
                        # polling and require manual re-auth.
                        retry_after = resp.headers.get("Retry-After", "unknown")
                        _LOGGER.warning(
                            "Norish: rate-limited (429) for %s – retry-after: %s. "
                            "Will retry on next poll interval.",
                            procedure, retry_after,
                        )
                        raise UpdateFailed(
                            f"Norish API rate limit reached for {procedure} "
                            f"(Retry-After: {retry_after})"
                        )

                    if resp.status == 404:
                        _LOGGER.error(
                            "Norish: endpoint not found (404): %s", procedure
                        )
                        return None

                    if resp.status >= 500:
                        if attempt < MAX_RETRIES - 1:
                            delay = RETRY_DELAY_BASE * (2 ** attempt)
                            _LOGGER.warning(
                                "Norish: server error %s for %s, retry %d/%d in %ds",
                                resp.status, procedure,
                                attempt + 1, MAX_RETRIES, delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        _LOGGER.error(
                            "Norish: server error %s for %s after %d attempts",
                            resp.status, procedure, MAX_RETRIES,
                        )
                        return None

                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.error(
                            "Norish: unexpected status %s for %s: %s",
                            resp.status, procedure, text[:200],
                        )
                        return None

                    return await resp.json()  # type: ignore[no-any-return]

            except (ConfigEntryAuthFailed, UpdateFailed):
                raise  # Never swallow auth failures or explicit rate-limit errors

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    _LOGGER.warning(
                        "Norish: timeout for %s, retry %d/%d in %ds",
                        procedure, attempt + 1, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: timeout for %s after %d attempts",
                    procedure, MAX_RETRIES,
                )
                return None

            except (
                aiohttp.ServerDisconnectedError,
                aiohttp.ClientConnectorError,
            ) as err:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    _LOGGER.warning(
                        "Norish: connection dropped for %s (%s), retry %d/%d in %ds",
                        procedure, type(err).__name__,
                        attempt + 1, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: connection failed for %s after %d attempts: %s",
                    procedure, MAX_RETRIES, err,
                )
                return None

            except aiohttp.ClientError as err:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    _LOGGER.warning(
                        "Norish: network error for %s: %s, retry %d/%d in %ds",
                        procedure, err, attempt + 1, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: network error for %s: %s", procedure, err
                )
                return None

        return None

    async def _post_trpc(
        self,
        procedure: str,
        payload: dict[str, Any],
    ) -> list[Any] | None:
        """POST a mutation to a tRPC endpoint."""
        url = f"{self.base_url}/api/trpc/{procedure}?batch=1"
        headers = {
            **self._get_headers(),
            "Content-Type": "application/json",
        }
        body = json.dumps({"0": {"json": payload}})
        session = async_get_clientsession(self.hass)

        try:
            async with session.post(
                url, headers=headers, data=body,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    _LOGGER.error(
                        "Norish: POST %s – 401, API key invalid or expired",
                        procedure,
                    )
                    raise ConfigEntryAuthFailed(
                        "Norish API key invalid or expired on POST"
                    )
                if resp.status == 429:
                    _LOGGER.warning(
                        "Norish: POST %s rate-limited (429)", procedure
                    )
                    raise UpdateFailed(
                        f"Norish API rate limit reached for POST {procedure}"
                    )
                if resp.status not in (200, 201):
                    text = await resp.text()
                    _LOGGER.error(
                        "Norish: POST %s failed with status %s: %s",
                        procedure, resp.status, text[:200],
                    )
                    return None
                return await resp.json()  # type: ignore[no-any-return]
        except aiohttp.ClientError as err:
            _LOGGER.error("Norish: POST %s network error: %s", procedure, err)
            return None
        except asyncio.TimeoutError:
            _LOGGER.error("Norish: POST %s timed out", procedure)
            return None

    # ------------------------------------------------------------------
    # Public mutation helpers (used by todo.py)
    # ------------------------------------------------------------------

    async def async_delete_groceries(self, grocery_ids: list[str]) -> bool:
        """Delete grocery items from Norish."""
        payload: dict[str, Any] = {"groceryIds": grocery_ids}
        result = await self._post_trpc("groceries.delete", payload)
        if result is None:
            _LOGGER.error("Norish: failed to delete groceries %s", grocery_ids)
            return False
        _LOGGER.debug("Norish: deleted groceries %s", grocery_ids)
        await self.async_request_refresh()
        return True

    async def async_toggle_grocery(
        self, grocery_id: str, is_done: bool
    ) -> bool:
        """Toggle a grocery item's done state."""
        payload: dict[str, Any] = {"groceryIds": [grocery_id], "isDone": is_done}
        result = await self._post_trpc("groceries.toggle", payload)
        if result is None:
            _LOGGER.error(
                "Norish: failed to toggle grocery %s (isDone=%s)",
                grocery_id, is_done,
            )
            return False
        _LOGGER.debug("Norish: toggled grocery %s → isDone=%s", grocery_id, is_done)
        await self.async_request_refresh()
        return True

    # ------------------------------------------------------------------
    # Core data update
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all Norish data.

        On 401: raises ConfigEntryAuthFailed so HA shows 'Reconfigure'.
        On 429: raises UpdateFailed so HA retries on the next poll interval.
        On network errors: raises UpdateFailed so HA retries on next poll.
        """
        data: dict[str, Any] = {
            "calendar": [],
            "groceries": [],
            "stores": {},
        }

        try:
            await self._fetch_calendar(data)
            await self._fetch_groceries(data)
            await self._fetch_stores_cached(data)
        except ConfigEntryAuthFailed:
            # API key is invalid → user must reconfigure
            raise
        except UpdateFailed:
            # Rate-limit or explicit failure → HA will retry on next interval
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Norish: failed to fetch core data: %s", err)
            raise UpdateFailed(f"Error fetching Norish data: {err}") from err

        # --- Optional: recipe details + image caching ---
        try:
            await self._fetch_recipe_details_cached(data)
            await self._download_and_cache_images(data)
        except ConfigEntryAuthFailed:
            _LOGGER.warning(
                "Norish: recipe endpoint returned 401 – core data loaded OK"
            )
        except UpdateFailed as err:
            _LOGGER.warning(
                "Norish: recipe fetch rate-limited, using cached recipes: %s", err
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Norish: recipe details / image caching failed: %s", err
            )

        self._last_successful_update = date.today()
        _LOGGER.info(
            "Norish: loaded %d calendar events, %d grocery items",
            len(data.get("calendar", [])),
            len(data.get("groceries", [])),
        )
        return data

    # ------------------------------------------------------------------
    # Data fetch methods
    # ------------------------------------------------------------------

    async def _fetch_calendar(self, data: dict[str, Any]) -> None:
        """Fetch calendar entries."""
        today = date.today()
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

        _LOGGER.debug("Norish: fetching calendar %s → %s", start_date, end_date)

        c_data = await self._fetch_trpc(
            "calendar.listItems",
            {"startISO": start_date, "endISO": end_date},
        )
        if c_data:
            items = self._safe_get_trpc_result(c_data, [])
            if isinstance(items, list):
                data["calendar"] = items
                _LOGGER.debug("Norish: loaded %d calendar items", len(items))
            else:
                _LOGGER.warning(
                    "Norish: unexpected calendar format: %s", type(items)
                )
        else:
            _LOGGER.warning("Norish: no calendar data received")

    async def _fetch_groceries(self, data: dict[str, Any]) -> None:
        """Fetch the grocery / shopping list."""
        g_data = await self._fetch_trpc("groceries.list")
        if not g_data:
            _LOGGER.debug("Norish: no grocery data received")
            return

        result = self._safe_get_trpc_result(g_data, {})

        if isinstance(result, list):
            items: list[Any] = result
        elif isinstance(result, dict):
            items = result.get("groceries", [])
        else:
            _LOGGER.warning("Norish: unexpected grocery format: %s", type(result))
            return

        if not isinstance(items, list):
            _LOGGER.warning(
                "Norish: unexpected groceries list format: %s", type(items)
            )
            return

        data["groceries"] = items

        recurring = (
            result.get("recurringGroceries", [])
            if isinstance(result, dict) else []
        )
        data["recurring_groceries"] = (
            recurring if isinstance(recurring, list) else []
        )

        _LOGGER.debug(
            "Norish: loaded %d grocery items, %d recurring",
            len(items), len(data["recurring_groceries"]),
        )

    async def _fetch_stores_cached(self, data: dict[str, Any]) -> None:
        """Fetch the store list, using the in-memory cache when possible.

        Stores almost never change, so we only call the API once every
        STORE_REFRESH_HOURS hours instead of on every poll.
        """
        now = datetime.now()
        cache_expired = (
            self._stores_last_fetched is None
            or (now - self._stores_last_fetched).total_seconds()
            > STORE_REFRESH_HOURS * 3600
        )

        if not cache_expired and self._cached_stores:
            _LOGGER.debug("Norish: using cached store list (%d stores)", len(self._cached_stores))
            data["stores"] = dict(self._cached_stores)
            self.store_map = dict(self._cached_stores)
            return

        _LOGGER.debug("Norish: fetching store list from API")
        s_data = await self._fetch_trpc("stores.list")
        if not s_data:
            # Fall back to cache if we have one
            if self._cached_stores:
                _LOGGER.warning("Norish: stores.list returned no data, using cached store list")
                data["stores"] = dict(self._cached_stores)
                self.store_map = dict(self._cached_stores)
            return

        stores = self._safe_get_trpc_result(s_data, [])
        new_store_map: dict[str, str] = {}
        if isinstance(stores, list):
            for store in stores:
                store_id = store.get("id")
                store_name = store.get("name")
                if store_id and store_name:
                    new_store_map[store_id] = store_name

        self._cached_stores = new_store_map
        self._stores_last_fetched = now
        data["stores"] = dict(new_store_map)
        self.store_map = dict(new_store_map)
        _LOGGER.debug("Norish: fetched and cached %d stores", len(new_store_map))

    async def _fetch_recipe_details_cached(self, data: dict[str, Any]) -> None:
        """Fetch recipe details, only re-fetching when the recipe ID set changes.

        If the set of recipe IDs in the current calendar is identical to the
        last fetch, the cached recipe details are reused — zero extra API calls.
        """
        calendar_items: list[dict[str, Any]] = data.get("calendar", [])
        current_recipe_ids: frozenset[str] = frozenset(
            event["recipeId"]
            for event in calendar_items
            if event.get("recipeId")
        )

        if not current_recipe_ids:
            return

        if current_recipe_ids == self._cached_recipe_ids and self._cached_recipes:
            _LOGGER.debug(
                "Norish: recipe IDs unchanged, reusing cache (%d recipes)",
                len(self._cached_recipes),
            )
        else:
            # Fetch only the IDs we don't already have cached
            new_ids = current_recipe_ids - set(self._cached_recipes.keys())
            if new_ids:
                _LOGGER.debug(
                    "Norish: fetching %d new recipe(s) (cache has %d)",
                    len(new_ids), len(self._cached_recipes),
                )
                for recipe_id in new_ids:
                    details = await self._fetch_recipe_details(recipe_id)
                    if details:
                        self._cached_recipes[recipe_id] = details
            else:
                _LOGGER.debug("Norish: all recipes already cached")

            # Remove recipes no longer referenced in the calendar
            stale_ids = set(self._cached_recipes.keys()) - current_recipe_ids
            for stale_id in stale_ids:
                del self._cached_recipes[stale_id]

            self._cached_recipe_ids = current_recipe_ids

        # Attach cached recipe data to calendar events
        for event in calendar_items:
            recipe_id = event.get("recipeId")
            if recipe_id and recipe_id in self._cached_recipes:
                event["_recipe"] = self._cached_recipes[recipe_id]

    async def _fetch_recipe_details(
        self, recipe_id: str
    ) -> dict[str, Any] | None:
        """Fetch details for a single recipe."""
        try:
            r_data = await self._fetch_trpc("recipes.get", {"id": recipe_id})
            if r_data:
                result = self._safe_get_trpc_result(r_data, None)
                if result:
                    _LOGGER.debug(
                        "Norish: loaded recipe '%s'",
                        result.get("name", "unknown"),
                    )
                    return result  # type: ignore[no-any-return]
        except ConfigEntryAuthFailed:
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Norish: failed to load recipe %s: %s", recipe_id, err
            )
        return None

    # ------------------------------------------------------------------
    # Image caching
    # ------------------------------------------------------------------

    async def _download_and_cache_images(self, data: dict[str, Any]) -> None:
        """Download and locally cache recipe images."""
        calendar_items: list[dict[str, Any]] = data.get("calendar", [])

        for event in calendar_items:
            recipe = event.get("_recipe") or {}
            if not recipe:
                continue
            image_path: str | None = (
                recipe.get("image") or recipe.get("imageUrl")
            )
            if not image_path:
                continue

            image_url = (
                f"{self.base_url}{image_path}"
                if image_path.startswith("/")
                else image_path
            )
            local_path = await self._cache_image(
                image_url, event.get("recipeId", "unknown")
            )
            if local_path:
                event["_local_image"] = local_path

    async def _cache_image(
        self, image_url: str, recipe_id: str
    ) -> str | None:
        """Download an image and cache it locally."""
        try:
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]  # noqa: S324
            filename = f"{recipe_id}_{url_hash}.jpg"
            local_file_path = os.path.join(self._image_cache_path, filename)

            file_exists = await self.hass.async_add_executor_job(
                os.path.exists, local_file_path
            )
            if file_exists:
                return f"/local/norish_images/{filename}"

            headers = self._get_headers()
            session = async_get_clientsession(self.hass)

            async with session.get(
                image_url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.debug(
                        "Norish: could not download image %s (status %s)",
                        image_url, resp.status,
                    )
                    return None
                image_data = await resp.read()

            await self.hass.async_add_executor_job(
                self._write_image, local_file_path, image_data
            )
            _LOGGER.debug("Norish: cached image %s", filename)
            return f"/local/norish_images/{filename}"

        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Norish: failed to cache image %s: %s", image_url, err
            )
            return None

    @staticmethod
    def _write_image(path: str, data: bytes) -> None:
        """Write image bytes to disk (runs in executor)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
