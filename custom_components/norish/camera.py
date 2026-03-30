"""Camera platform for Norish recipe images."""
from __future__ import annotations

import logging
import os

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import NorishCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norish cameras."""
    coordinator: NorishCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    cameras = [
        NorishRecipeCamera(coordinator, entry, "breakfast", "Breakfast"),
        NorishRecipeCamera(coordinator, entry, "lunch", "Lunch"),
        NorishRecipeCamera(coordinator, entry, "dinner", "Dinner"),
        NorishRecipeCamera(coordinator, entry, "snack", "Snack"),
    ]

    async_add_entities(cameras)


class NorishRecipeCamera(CoordinatorEntity, Camera):
    """Camera entity that shows today's recipe image for a given meal type."""

    def __init__(
        self,
        coordinator: NorishCoordinator,
        entry: ConfigEntry,
        meal_type: str,
        name: str,
    ) -> None:
        """Initialize the camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)

        self._entry = entry
        self._meal_type = meal_type.upper()
        self._attr_name = f"Norish {name} Image"
        self._attr_unique_id = f"{entry.entry_id}_camera_{meal_type}"

    def _get_base_url(self) -> str:
        """Return the Norish base URL."""
        return self.coordinator.auth.base_url

    @property
    def is_streaming(self) -> bool:
        """Return whether the camera is streaming."""
        return False

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture URL."""
        return self._get_current_image_url()

    def _get_current_image_url(self) -> str | None:
        """Resolve the best available image URL for today's meal."""
        if not self.coordinator.data:
            return None

        events: list[dict] = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")
        base_url = self._get_base_url()

        for event in events:
            if event.get("date", "") != today_str:
                continue
            if (event.get("slot") or "").upper() != self._meal_type:
                continue

            # Prefer locally cached image
            local_image: str | None = event.get("_local_image")
            if local_image:
                return local_image

            # Fallback: remote image from recipe details
            recipe_details: dict = event.get("_recipe") or {}
            if recipe_details:
                image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                if image_url:
                    return f"{base_url}{image_url}" if image_url.startswith("/") else image_url

            recipe_id: str | None = event.get("recipeId")
            if recipe_id and base_url:
                return f"{base_url}/api/recipes/{recipe_id}/image"

        return None

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Return image bytes for the camera snapshot."""
        if not self.coordinator.data:
            return None

        events: list[dict] = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")

        for event in events:
            if event.get("date", "") != today_str:
                continue
            if (event.get("slot") or "").upper() != self._meal_type:
                continue

            # Try reading from local cache (non-blocking)
            local_image: str | None = event.get("_local_image")
            if local_image:
                try:
                    filename = local_image.replace("/local/norish_images/", "")
                    file_path = self.hass.config.path("www/norish_images", filename)

                    def _read_file(path: str) -> bytes | None:
                        if os.path.exists(path):
                            with open(path, "rb") as f:
                                return f.read()
                        return None

                    data = await self.hass.async_add_executor_job(_read_file, file_path)
                    if data:
                        return data
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Failed to read cached image: %s", err)

            # Fallback: fetch from remote
            image_url = self._get_current_image_url()
            if image_url and not image_url.startswith("/local/"):
                try:
                    from homeassistant.helpers.aiohttp_client import async_get_clientsession
                    await self.coordinator.auth.ensure_valid_session()
                    headers: dict = self.coordinator.auth.get_headers()
                    http_session = async_get_clientsession(self.hass)

                    async with http_session.get(
                        image_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        if response.status == 200:
                            return await response.read()
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Failed to fetch remote image: %s", err)

        return None
