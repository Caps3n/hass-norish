"""Media player platform for Norish recipe videos."""
from __future__ import annotations

import logging

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
from .coordinator import NorishCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norish media players."""
    coordinator: NorishCoordinator = hass.data[DOMAIN][entry.entry_id]

    players = [
        NorishVideoPlayer(coordinator, entry, "breakfast", "Breakfast"),
        NorishVideoPlayer(coordinator, entry, "lunch", "Lunch"),
        NorishVideoPlayer(coordinator, entry, "dinner", "Dinner"),
        NorishVideoPlayer(coordinator, entry, "snack", "Snack"),
    ]

    async_add_entities(players)


class NorishVideoPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Media player entity showing today's recipe video for a given meal type."""

    def __init__(
        self,
        coordinator: NorishCoordinator,
        entry: ConfigEntry,
        meal_type: str,
        name: str,
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._entry = entry
        self._meal_type = meal_type.upper()
        self._attr_name = f"Norish {name} Video"
        self._attr_unique_id = f"{entry.entry_id}_video_{meal_type}"
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.STOP
        )

    def _get_base_url(self) -> str:
        """Return the Norish base URL."""
        return self.coordinator.base_url

    def _get_today_event(self) -> dict | None:
        """Return today's calendar event for this meal type, or None."""
        if not self.coordinator.data:
            return None
        today_str = dt_util.now().strftime("%Y-%m-%d")
        for event in self.coordinator.data.get("calendar", []):
            if event.get("date", "") == today_str and (
                event.get("slot") or ""
            ).upper() == self._meal_type:
                return event
        return None

    @property
    def state(self) -> MediaPlayerState:
        """Return the player state."""
        return MediaPlayerState.IDLE if self._get_video_url() else MediaPlayerState.OFF

    @property
    def media_content_type(self) -> str:
        """Return the media content type."""
        return MediaType.VIDEO

    @property
    def media_title(self) -> str | None:
        """Return the title of the current media."""
        event = self._get_today_event()
        if event:
            return event.get("recipeName") or event.get("name")
        return None

    @property
    def media_image_url(self) -> str | None:
        """Return the image URL for the current media."""
        event = self._get_today_event()
        if not event:
            return None
        base_url = self._get_base_url()
        recipe_details: dict = event.get("_recipe") or {}
        if recipe_details:
            image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
            if image_url:
                return f"{base_url}{image_url}" if image_url.startswith("/") else image_url
        recipe_id: str | None = event.get("recipeId")
        if recipe_id and base_url:
            return f"{base_url}/api/recipes/{recipe_id}/image"
        return None

    def _get_video_url(self) -> str | None:
        """Return the video URL for today's recipe, or None."""
        event = self._get_today_event()
        if not event:
            return None
        recipe_details: dict = event.get("_recipe") or {}
        if recipe_details:
            video = recipe_details.get("video") or recipe_details.get("videoUrl")
            if video:
                base_url = self._get_base_url()
                return f"{base_url}{video}" if video.startswith("/") else video
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "video_url": self._get_video_url(),
            "meal_type": self._meal_type,
        }
