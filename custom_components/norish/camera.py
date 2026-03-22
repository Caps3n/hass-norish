"""Camera platform for Norish recipe images."""
import logging
import os
from typing import Optional

from homeassistant.components.camera import Camera
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Norish cameras."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    cameras = [
        NorishRecipeCamera(coordinator, entry, "breakfast", "Frühstück"),
        NorishRecipeCamera(coordinator, entry, "lunch", "Mittagessen"),
        NorishRecipeCamera(coordinator, entry, "dinner", "Abendessen"),
        NorishRecipeCamera(coordinator, entry, "snack", "Snack"),
    ]
    
    async_add_entities(cameras)


class NorishRecipeCamera(CoordinatorEntity, Camera):
    """Camera entity for Norish recipe images."""

    def __init__(self, coordinator, entry, meal_type: str, name: str):
        """Initialize the camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        
        self._entry = entry
        self._meal_type = meal_type.upper()
        self._attr_name = f"Norish {name} Bild"
        self._attr_unique_id = f"{entry.entry_id}_camera_{meal_type}"
        self.hass = coordinator.hass

    def _get_base_url(self) -> str:
        return self.coordinator.api_data.get('url', '').rstrip('/')

    @property
    def is_streaming(self) -> bool:
        return False

    @property
    def entity_picture(self) -> Optional[str]:
        return self._get_current_image_url()

    def _get_current_image_url(self) -> Optional[str]:
        if not self.coordinator.data:
            return None

        events = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")
        base_url = self._get_base_url()

        for event in events:
            if event.get("date", "") != today_str:
                continue
            slot = event.get("slot") or ""
            if slot.upper() != self._meal_type:
                continue

            # Bevorzuge lokales gecachtes Bild
            local_image = event.get("_local_image")
            if local_image:
                return local_image

            # Fallback: Remote-Bild
            recipe_details = event.get("_recipe", {})
            if recipe_details:
                image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                if image_url:
                    if image_url.startswith("/"):
                        return f"{base_url}{image_url}"
                    return image_url

            recipe_id = event.get("recipeId")
            if recipe_id and base_url:
                return f"{base_url}/api/recipes/{recipe_id}/image"

        return None

    async def async_camera_image(self, width: Optional[int] = None, height: Optional[int] = None) -> Optional[bytes]:
        if not self.coordinator.data:
            return None

        events = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")

        for event in events:
            if event.get("date", "") != today_str:
                continue
            slot = event.get("slot") or ""
            if slot.upper() != self._meal_type:
                continue

            # Versuche lokales Bild zu laden
            local_image = event.get("_local_image")
            if local_image:
                try:
                    # Konvertiere /local/norish_images/xxx.jpg zu Dateipfad
                    filename = local_image.replace("/local/norish_images/", "")
                    file_path = self.hass.config.path("www/norish_images", filename)
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            return f.read()
                except Exception as e:
                    _LOGGER.debug(f"Fehler beim Laden des lokalen Bildes: {e}")

            # Fallback: Remote-Bild laden
            image_url = self._get_current_image_url()
            if image_url and not image_url.startswith("/local/"):
                try:
                    session = self.coordinator.api_data.get("session")
                    headers = self.coordinator.api_data.get("headers", {})
                    
                    async with session.get(image_url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            return await response.read()
                except Exception as e:
                    _LOGGER.debug(f"Fehler beim Laden des Remote-Bildes: {e}")

        return None
