"""Media player platform for Norish recipe videos."""
from __future__ import annotations

import logging
from typing import Optional

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norish media players."""
    coordinator: NorishListCoordinator = hass.data[DOMAIN][entry.entry_id]

    players = [
        NorishVideoPlayer(coordinator, entry, "breakfast", "Frühstück"),
        NorishVideoPlayer(coordinator, entry, "lunch", "Mittagessen"),
        NorishVideoPlayer(coordinator, entry, "dinner", "Abendessen"),
        NorishVideoPlayer(coordinator, entry, "snack", "Snack"),
    ]
    
    async_add_entities(players)


class NorishVideoPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Media player for Norish recipe videos."""

    def __init__(self, coordinator, entry, meal_type: str, name: str):
        super().__init__(coordinator)
        self._entry = entry
        self._meal_type = meal_type.upper()
        self._attr_name = f"Norish {name} Video"
        self._attr_unique_id = f"{entry.entry_id}_video_{meal_type}"
        self._attr_supported_features = MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.STOP

    def _get_base_url(self) -> str:
        return self.coordinator.api_data.get('url', '').rstrip('/')

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.IDLE if self._get_video_url() else MediaPlayerState.OFF

    @property
    def media_content_type(self) -> Optional[str]:
        return MediaType.VIDEO

    @property
    def media_title(self) -> Optional[str]:
        return self._get_recipe_name()

    @property
    def media_image_url(self) -> Optional[str]:
        return self._get_image_url()

    def _get_video_url(self) -> Optional[str]:
        if not self.coordinator.data:
            return None
        events = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")

        for event in events:
            if event.get("date", "") != today_str:
                continue
            if (event.get("slot") or "").upper() != self._meal_type:
                continue
            recipe_details = event.get("_recipe", {})
            if recipe_details:
                return recipe_details.get("video") or recipe_details.get("videoUrl")
        return None

    def _get_image_url(self) -> Optional[str]:
        if not self.coordinator.data:
            return None
        events = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")
        base_url = self._get_base_url()

        for event in events:
            if event.get("date", "") != today_str:
                continue
            if (event.get("slot") or "").upper() != self._meal_type:
                continue
            recipe_details = event.get("_recipe", {})
            if recipe_details:
                image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                if image_url:
                    return image_url
            recipe_id = event.get("recipeId")
            if recipe_id and base_url:
                return f"{base_url}/api/recipes/{recipe_id}/image"
        return None

    def _get_recipe_name(self) -> Optional[str]:
        if not self.coordinator.data:
            return None
        events = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")

        for event in events:
            if event.get("date", "") != today_str:
                continue
            if (event.get("slot") or "").upper() != self._meal_type:
                continue
            return event.get("recipeName") or event.get("name")
        return None

    @property
    def extra_state_attributes(self):
        return {"video_url": self._get_video_url(), "meal_type": self._meal_type}
