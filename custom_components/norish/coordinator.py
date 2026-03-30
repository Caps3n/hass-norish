"""Coordinator for the Norish API.

v1.6.0 – Complete rewrite with session-based auth via NorishAuthManager.
No more sliding-window counters or API key workarounds.  On 401 the
coordinator attempts a transparent re-login; only if that fails too is
ConfigEntryAuthFailed raised so HA shows "Reconfigure".
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import urllib.parse
from datetime import date, timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .auth import NorishAuthError, NorishAuthManager

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2
IMAGE_CACHE_DIR = "www/norish_images"
POLL_INTERVAL_SECONDS = 30


class NorishCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for the Norish API with session-based authentication."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        auth: NorishAuthManager,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Norish API",
            update_interval=timedelta(seconds=POLL_INTERVAL_SECONDS),
            config_entry=entry,
        )
        self.auth = auth
        self.store_map: dict[str, str] = {}
        self._last_successful_update: date | None = None
        self._image_cache_path = os.path.join(
            hass.config.config_dir, IMAGE_CACHE_DIR
        )
        os.makedirs(self._image_cache_path, exist_ok=True)

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
        """Fetch data from a tRPC endpoint with retry + auto re-auth."""
        trpc_input = {"0": {"json": payload if payload is not None else None}}
        encoded = urllib.parse.quote(
            json.dumps(trpc_input, separators=(",", ":"))
        )
        url = f"{self.auth.base_url}/api/trpc/{procedure}?batch=1&input={encoded}"
        session = async_get_clientsession(self.hass)

        for attempt in range(MAX_RETRIES):
            # Ensure session is valid before every attempt
            await self.auth.ensure_valid_session()
            headers = self.auth.get_headers()

            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        _LOGGER.warning(
                            "Norish: 401 for %s – attempting re-login",
                            procedure,
                        )
                        try:
                            await self.auth.ensure_valid_session()
                        except NorishAuthError:
                            raise ConfigEntryAuthFailed(
                                "Norish session expired and re-login failed"
                            ) from None
                        # Retry with fresh session
                        if attempt < MAX_RETRIES - 1:
                            continue
                        raise ConfigEntryAuthFailed(
                            "Norish: persistent 401 after re-login"
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

            except ConfigEntryAuthFailed:
                raise  # Don't catch auth failures in the retry loop

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
        await self.auth.ensure_valid_session()

        url = f"{self.auth.base_url}/api/trpc/{procedure}?batch=1"
        headers = {
            **self.auth.get_headers(),
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
                        "Norish: POST %s – 401, session may have expired",
                        procedure,
                    )
                    raise ConfigEntryAuthFailed(
                        "Norish session expired on POST"
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

        On 401: attempts transparent re-login.  If re-login also fails,
        raises ConfigEntryAuthFailed so HA shows 'Reconfigure'.
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
            await self._fetch_stores(data)
        except ConfigEntryAuthFailed:
            # Session is dead and re-login failed → user must reconfigure
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Norish: failed to fetch core data: %s", err)
            raise UpdateFailed(f"Error fetching Norish data: {err}") from err

        # --- Optional: recipe details + image caching ---
        try:
            await self._fetch_recipe_details_for_calendar(data)
            await self._download_and_cache_images(data)
        except ConfigEntryAuthFailed:
            _LOGGER.warning(
                "Norish: recipe endpoint returned 401 – core data loaded OK"
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

    async def _fetch_stores(self, data: dict[str, Any]) -> None:
        """Fetch the store list."""
        s_data = await self._fetch_trpc("stores.list")
        if not s_data:
            return
        stores = self._safe_get_trpc_result(s_data, [])
        if isinstance(stores, list):
            for store in stores:
                store_id = store.get("id")
                store_name = store.get("name")
                if store_id and store_name:
                    data["stores"][store_id] = store_name

    async def _fetch_recipe_details_for_calendar(
        self, data: dict[str, Any]
    ) -> None:
        """Fetch recipe details for all calendar entries."""
        calendar_items: list[dict[str, Any]] = data.get("calendar", [])
        recipe_ids: set[str] = {
            event["recipeId"]
            for event in calendar_items
            if event.get("recipeId")
        }
        if not recipe_ids:
            return

        _LOGGER.debug("Norish: fetching details for %d recipes", len(recipe_ids))

        recipe_details: dict[str, Any] = {}
        for recipe_id in recipe_ids:
            details = await self._fetch_recipe_details(recipe_id)
            if details:
                recipe_details[recipe_id] = details

        for event in calendar_items:
            recipe_id = event.get("recipeId")
            if recipe_id and recipe_id in recipe_details:
                event["_recipe"] = recipe_details[recipe_id]

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
        base_url = self.auth.base_url

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
                f"{base_url}{image_path}"
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

            await self.auth.ensure_valid_session()
            headers = self.auth.get_headers()
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
