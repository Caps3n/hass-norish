"""Media Player Entity für Norish Rezept-Videos."""
import logging
from typing import Optional
from datetime import datetime

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaType,
    MediaPlayerState,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup media player entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Erstelle Media Player für verschiedene Mahlzeiten
    players = [
        NorishVideoPlayer(coordinator, entry, "breakfast"),
        NorishVideoPlayer(coordinator, entry, "lunch"),
        NorishVideoPlayer(coordinator, entry, "dinner"),
        NorishVideoPlayer(coordinator, entry, "snack"),
    ]
    
    async_add_entities(players)


class NorishVideoPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Media Player Entity für Norish Rezept-Videos.
    
    Spielt Videos in Endlosschleife, stumm und automatisch ab.
    """

    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY |
        MediaPlayerEntityFeature.PAUSE |
        MediaPlayerEntityFeature.STOP |
        MediaPlayerEntityFeature.VOLUME_MUTE
    )

    def __init__(self, coordinator, entry, meal_type: str):
        """Initialize the media player.
        
        Args:
            coordinator: The data coordinator
            entry: The config entry
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
        """
        CoordinatorEntity.__init__(self, coordinator)
        MediaPlayerEntity.__init__(self)
        
        self._meal_type = meal_type.upper()
        
        # Namen
        type_names = {
            "BREAKFAST": "Frühstück",
            "LUNCH": "Mittagessen",
            "DINNER": "Abendessen",
            "SNACK": "Snack",
        }
        
        display_name = type_names.get(self._meal_type, meal_type)
        self._attr_name = f"Norish {display_name} Video"
        self._attr_unique_id = f"{entry.entry_id}_video_{meal_type}"
        self._attr_icon = "mdi:play-circle"
        
        # Immer stumm und in Schleife
        self._attr_is_volume_muted = True
        self._attr_repeat = "all"

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        video_url = self._get_video_url()
        
        if not video_url:
            return MediaPlayerState.OFF
        
        # Video ist verfügbar = automatisch spielend
        return MediaPlayerState.PLAYING

    @property
    def media_content_type(self) -> str:
        """Return the media type."""
        return MediaType.VIDEO

    @property
    def media_content_id(self) -> Optional[str]:
        """Return the content ID (Video-URL)."""
        return self._get_video_url()

    @property
    def media_title(self) -> Optional[str]:
        """Return the title of current playing media."""
        if not self.coordinator.data:
            return None
        
        events = self.coordinator.data.get("calendar", [])
        now_date = dt_util.now().date()
        
        for event in events:
            date_raw = event.get("date") or event.get("day")
            if not date_raw:
                continue
            
            try:
                dt_event = datetime.fromisoformat(
                    date_raw.replace("Z", "+00:00")
                ).date()
                
                if dt_event != now_date:
                    continue
                
                event_type = str(
                    event.get("type") or event.get("slot") or ""
                ).upper()
                
                if event_type != self._meal_type:
                    continue
                
                recipe = event.get("recipe")
                if isinstance(recipe, dict):
                    return recipe.get("name")
                return event.get("recipeName") or event.get("title")
                
            except Exception:
                continue
        
        return None

    @property
    def media_image_url(self) -> Optional[str]:
        """Return the thumbnail URL."""
        if not self.coordinator.data:
            return None
        
        events = self.coordinator.data.get("calendar", [])
        now_date = dt_util.now().date()
        
        for event in events:
            date_raw = event.get("date") or event.get("day")
            if not date_raw:
                continue
            
            try:
                dt_event = datetime.fromisoformat(
                    date_raw.replace("Z", "+00:00")
                ).date()
                
                if dt_event != now_date:
                    continue
                
                event_type = str(
                    event.get("type") or event.get("slot") or ""
                ).upper()
                
                if event_type != self._meal_type:
                    continue
                
                recipe = event.get("recipe")
                
                # Priorisiere Video-Thumbnail
                if isinstance(recipe, dict):
                    thumbnail = (
                        recipe.get("videoThumbnail") or
                        recipe.get("video_thumbnail") or
                        recipe.get("image") or
                        recipe.get("imageUrl")
                    )
                    if thumbnail:
                        return thumbnail
                
                # Fallback: Event-Bild
                return event.get("image") or event.get("imageUrl")
                
            except Exception:
                continue
        
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        attrs = {
            "loop": True,
            "muted": True,
            "autoplay": True,
            "controls": True,
        }
        
        video_url = self._get_video_url()
        if video_url:
            attrs["video_url"] = video_url
            attrs["video_source"] = self._get_base_url() + video_url if video_url.startswith('/') else video_url
        
        return attrs

    def _get_video_url(self) -> Optional[str]:
        """Get the video URL for today's meal."""
        if not self.coordinator.data:
            return None
        
        events = self.coordinator.data.get("calendar", [])
        now_date = dt_util.now().date()
        
        for event in events:
            date_raw = event.get("date") or event.get("day")
            if not date_raw:
                continue
            
            try:
                dt_event = datetime.fromisoformat(
                    date_raw.replace("Z", "+00:00")
                ).date()
                
                if dt_event != now_date:
                    continue
                
                event_type = str(
                    event.get("type") or event.get("slot") or ""
                ).upper()
                
                if event_type != self._meal_type:
                    continue
                
                recipe = event.get("recipe")
                
                # Video-URL finden
                if isinstance(recipe, dict):
                    video_url = (
                        recipe.get("video") or
                        recipe.get("videoUrl") or
                        recipe.get("video_url") or
                        recipe.get("youtubeUrl") or
                        recipe.get("youtube_url")
                    )
                    if video_url:
                        return video_url
                
                # Fallback: Event-Video
                video_url = (
                    event.get("video") or
                    event.get("videoUrl") or
                    event.get("video_url")
                )
                if video_url:
                    return video_url
                
            except Exception as e:
                _LOGGER.debug(f"Fehler beim Extrahieren der Video-URL: {e}")
                continue
        
        return None

    def _get_base_url(self) -> str:
        """Get the base URL from coordinator."""
        return self.coordinator.api_data.get("url", "")

    # Media Player Actions (für Kompatibilität)
    
    async def async_play(self):
        """Play media - Videos spielen automatisch."""
        pass

    async def async_pause(self):
        """Pause media - wird nicht unterstützt (auto-loop)."""
        pass

    async def async_stop(self):
        """Stop media - wird nicht unterstützt (auto-loop)."""
        pass

    async def async_mute_volume(self, mute):
        """Mute volume - immer stumm."""
        self._attr_is_volume_muted = True
