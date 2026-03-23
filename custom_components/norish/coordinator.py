"""Coordinator for the Norish API."""
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

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2
IMAGE_CACHE_DIR = "www/norish_images"


class NorishListCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for the Norish API."""

    def __init__(self, hass: HomeAssistant, api_data: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Norish API",
            update_interval=timedelta(minutes=5),
        )
        self.api_data = api_data
        self.store_map: dict[str, str] = {}
        self._last_successful_update: date | None = None
        self._image_cache_path = os.path.join(hass.config.config_dir, IMAGE_CACHE_DIR)

        # Create image cache directory synchronously – this is a one-time fast filesystem
        # call during coordinator init and safe to do inline.
        os.makedirs(self._image_cache_path, exist_ok=True)

    def _safe_get_trpc_result(
        self,
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
        """Fetch data from a tRPC endpoint with retry logic."""
        trpc_input = {"0": {"json": payload if payload is not None else None}}
        encoded = urllib.parse.quote(json.dumps(trpc_input, separators=(",", ":")))
        url = f"{self.api_data['url']}/api/trpc/{procedure}?batch=1&input={encoded}"
        headers: dict[str, str] = self.api_data.get("headers", {})

        for attempt in range(MAX_RETRIES):
            try:
                async with self.api_data["session"].get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        _LOGGER.error(
                            "Norish: Access denied (401) for %s – check your API key",
                            procedure,
                        )
                        return None

                    if resp.status == 404:
                        _LOGGER.error(
                            "Norish: Endpoint not found (404): %s", procedure
                        )
                        return None

                    if resp.status >= 500:
                        if attempt < MAX_RETRIES - 1:
                            delay = RETRY_DELAY_BASE * (2**attempt)
                            _LOGGER.warning(
                                "Norish: Server error %s for %s, retry %d/%d in %ds",
                                resp.status,
                                procedure,
                                attempt + 1,
                                MAX_RETRIES,
                                delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        _LOGGER.error(
                            "Norish: Server error %s for %s after %d attempts",
                            resp.status,
                            procedure,
                            MAX_RETRIES,
                        )
                        return None

                    if resp.status != 200:
                        text = await resp.text()
                        _LOGGER.error(
                            "Norish: Unexpected status %s for %s: %s",
                            resp.status,
                            procedure,
                            text[:200],
                        )
                        return None

                    return await resp.json()  # type: ignore[no-any-return]

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2**attempt)
                    _LOGGER.warning(
                        "Norish: Timeout for %s, retry %d/%d in %ds",
                        procedure,
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: Timeout for %s after %d attempts", procedure, MAX_RETRIES
                )
                return None

            except aiohttp.ClientError as err:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2**attempt)
                    _LOGGER.warning(
                        "Norish: Network error for %s: %s, retry %d/%d in %ds",
                        procedure,
                        err,
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: Network error for %s: %s", procedure, err
                )
                return None

        return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all Norish data."""
        data: dict[str, Any] = {
            "calendar": [],
            "groceries": [],
            "stores": {},
        }

        # --- Core data: calendar + groceries (must succeed) ---
        try:
            await self._fetch_calendar(data)
            await self._fetch_groceries(data)
            await self._fetch_stores(data)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Norish: failed to fetch core data: %s", err)
            raise UpdateFailed(f"Error fetching Norish data: {err}") from err

        # --- Recipe details + image caching (optional – never blocks core data) ---
        try:
            await self._fetch_recipe_details_for_calendar(data)
            await self._download_and_cache_images(data)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Norish: recipe details / image caching failed: %s", err)

        self._last_successful_update = date.today()
        _LOGGER.info(
            "Norish: loaded %d calendar events, %d grocery items",
            len(data.get("calendar", [])),
            len(data.get("groceries", [])),
        )

        return data

    async def _fetch_calendar(self, data: dict[str, Any]) -> None:
        """Fetch calendar entries from the Norish API (v0.16+)."""
        today = date.today()
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

        _LOGGER.debug("Norish: fetching calendar %s → %s", start_date, end_date)

        c_data = await self._fetch_trpc(
            "calendar.listItems", {"startISO": start_date, "endISO": end_date}
        )

        if c_data:
            calendar_items = self._safe_get_trpc_result(c_data, [])
            if isinstance(calendar_items, list):
                data["calendar"] = calendar_items
                _LOGGER.debug("Norish: loaded %d calendar items", len(calendar_items))
            else:
                _LOGGER.warning(
                    "Norish: unexpected calendar format: %s", type(calendar_items)
                )
        else:
            _LOGGER.warning("Norish: no calendar data received")

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
                        "Norish: loaded recipe '%s'", result.get("name", "unknown")
                    )
                    return result  # type: ignore[no-any-return]
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Norish: failed to load recipe %s: %s", recipe_id, err)
        return None

    async def _fetch_groceries(self, data: dict[str, Any]) -> None:
        """Fetch the grocery/shopping list."""
        g_data = await self._fetch_trpc("groceries.list")

        if not g_data:
            _LOGGER.debug("Norish: no grocery data received")
            return

        items = self._safe_get_trpc_result(g_data, [])
        if not isinstance(items, list):
            _LOGGER.warning("Norish: unexpected grocery format: %s", type(items))
            return

        data["groceries"] = items
        _LOGGER.debug("Norish: loaded %d grocery items", len(items))

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

    async def _download_and_cache_images(self, data: dict[str, Any]) -> None:
        """Download and locally cache recipe images."""
        calendar_items: list[dict[str, Any]] = data.get("calendar", [])
        base_url: str = self.api_data.get("url", "").rstrip("/")

        for event in calendar_items:
            recipe_details: dict[str, Any] = event.get("_recipe") or {}
            if not recipe_details:
                continue

            image_path: str | None = recipe_details.get("image") or recipe_details.get("imageUrl")
            if not image_path:
                continue

            image_url = f"{base_url}{image_path}" if image_path.startswith("/") else image_path

            local_path = await self._cache_image(
                image_url, event.get("recipeId", "unknown")
            )
            if local_path:
                event["_local_image"] = local_path

    async def _cache_image(
        self, image_url: str, recipe_id: str
    ) -> str | None:
        """Download an image and cache it locally. Returns the local URL path."""
        try:
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
            filename = f"{recipe_id}_{url_hash}.jpg"
            local_file_path = os.path.join(self._image_cache_path, filename)

            # Return cached path if already downloaded
            file_exists = await self.hass.async_add_executor_job(
                os.path.exists, local_file_path
            )
            if file_exists:
                return f"/local/norish_images/{filename}"

            headers: dict[str, str] = self.api_data.get("headers", {})
            session = self.api_data.get("session")

            async with session.get(
                image_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.debug(
                        "Norish: could not download image %s (status %s)",
                        image_url,
                        resp.status,
                    )
                    return None

                image_data = await resp.read()

            # Write to disk in executor to avoid blocking the event loop
            await self.hass.async_add_executor_job(
                self._write_image, local_file_path, image_data
            )

            _LOGGER.debug("Norish: cached image %s", filename)
            return f"/local/norish_images/{filename}"

        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Norish: failed to cache image %s: %s", image_url, err)
            return None

    @staticmethod
    def _write_image(path: str, data: bytes) -> None:
        """Write image bytes to disk (runs in executor)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
