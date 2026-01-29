"""Camera Entity für Norish Rezeptbilder (Alternative Implementierung)."""
import logging
from datetime import datetime
from typing import Optional

import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup camera entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Erstelle Kameras für verschiedene Mahlzeiten
    cameras = [
        NorishMealCamera(coordinator, entry, "breakfast"),
        NorishMealCamera(coordinator, entry, "lunch"),
        NorishMealCamera(coordinator, entry, "dinner"),
        NorishMealCamera(coordinator, entry, "snack"),
    ]
    
    async_add_entities(cameras)


class NorishMealCamera(CoordinatorEntity, Camera):
    """Camera Entity die das Rezeptbild anzeigt."""

    def __init__(self, coordinator, entry, meal_type: str):
        """Initialize the camera.
        
        Args:
            coordinator: The data coordinator
            entry: The config entry
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
        """
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        
        self._meal_type = meal_type.upper()
        
        # Namen
        type_names = {
            "BREAKFAST": "Frühstück",
            "LUNCH": "Mittagessen",
            "DINNER": "Abendessen",
            "SNACK": "Snack",
        }
        
        display_name = type_names.get(self._meal_type, meal_type)
        self._attr_name = f"Norish {display_name} Bild"
        self._attr_unique_id = f"{entry.entry_id}_camera_{meal_type}"
        self._attr_brand = "Norish"
        
        self._cached_image: Optional[bytes] = None
        self._last_image_url: Optional[str] = None

    @property
    def is_on(self) -> bool:
        """Return true if the camera is on (has an image to show)."""
        return self._get_image_url() is not None

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return image response."""
        image_url = self._get_image_url()
        
        if not image_url:
            _LOGGER.debug(f"Keine Bild-URL für {self._meal_type}")
            return None
        
        # Cache-Check: Wenn URL gleich ist, nutze gecachtes Bild
        if image_url == self._last_image_url and self._cached_image:
            _LOGGER.debug(f"Nutze gecachtes Bild für {self._meal_type}")
            return self._cached_image
        
        # Neues Bild laden
        try:
            _LOGGER.debug(f"Lade Bild von: {image_url}")
            
            # Headers aus coordinator api_data holen (falls vorhanden)
            headers = self.coordinator.api_data.get("headers", {})
            
            async with self.coordinator.api_data["session"].get(
                image_url,
                headers=headers,  # Headers explizit übergeben
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(
                        f"Fehler beim Laden des Bildes: Status {resp.status}"
                    )
                    return None
                
                image_data = await resp.read()
                
                # Cache aktualisieren
                self._cached_image = image_data
                self._last_image_url = image_url
                
                _LOGGER.debug(
                    f"Bild erfolgreich geladen: {len(image_data)} bytes"
                )
                return image_data
                
        except Exception as e:
            _LOGGER.error(f"Fehler beim Laden des Rezeptbildes: {e}")
            return None

    def _get_image_url(self) -> Optional[str]:
        """Get the image URL for today's meal of this type."""
        if not self.coordinator.data:
            return None
        
        events = self.coordinator.data.get("calendar", [])
        now_date = dt_util.now().date()
        
        for event in events:
            # Datum prüfen
            date_raw = event.get("date") or event.get("day")
            if not date_raw:
                continue
            
            try:
                dt_event = datetime.fromisoformat(
                    date_raw.replace("Z", "+00:00")
                ).date()
                
                if dt_event != now_date:
                    continue
                
                # Typ prüfen
                event_type = str(
                    event.get("type") or event.get("slot") or ""
                ).upper()
                
                if event_type != self._meal_type:
                    continue
                
                # Bild-URL finden
                recipe = event.get("recipe")
                
                image_url = None
                if isinstance(recipe, dict):
                    image_url = (
                        recipe.get("image") or
                        recipe.get("imageUrl") or
                        recipe.get("picture") or
                        recipe.get("photo") or
                        recipe.get("thumbnail")
                    )
                
                if not image_url:
                    image_url = (
                        event.get("image") or
                        event.get("imageUrl") or
                        event.get("picture")
                    )
                
                if image_url:
                    return image_url
                    
            except Exception as e:
                _LOGGER.debug(f"Fehler beim Extrahieren der Bild-URL: {e}")
                continue
        
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        attrs = {}
        
        if not self.coordinator.data:
            return attrs
        
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
                
                # Rezept-Informationen hinzufügen
                recipe = event.get("recipe")
                if isinstance(recipe, dict):
                    attrs["recipe_name"] = recipe.get("name")
                    attrs["description"] = recipe.get("description")
                    attrs["cooking_time"] = recipe.get("cookingTime")
                    attrs["servings"] = recipe.get("servings")
                    attrs["recipe_id"] = recipe.get("id")
                else:
                    attrs["recipe_name"] = (
                        event.get("recipeName") or event.get("title")
                    )
                
                attrs["meal_type"] = event_type
                
                break
                
            except Exception:
                continue
        
        return attrs
