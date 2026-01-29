"""Sensor für Norish Mahlzeiten mit Bild- und Video-Unterstützung."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Erstelle mehrere Sensoren für verschiedene Mahlzeiten
    sensors = [
        NorishMealSensor(coordinator, entry, "all"),  # Alle Mahlzeiten
        NorishMealSensor(coordinator, entry, "breakfast"),  # Frühstück
        NorishMealSensor(coordinator, entry, "lunch"),  # Mittagessen
        NorishMealSensor(coordinator, entry, "dinner"),  # Abendessen
        NorishMealSensor(coordinator, entry, "snack"),  # Snack
        NorishWeekPlannerSensor(coordinator, entry),  # Wochenplan
    ]
    
    async_add_entities(sensors)


class NorishMealSensor(CoordinatorEntity, SensorEntity):
    """Sensor für Norish Mahlzeiten mit Bild- und Video-Anzeige."""

    def __init__(self, coordinator, entry, meal_type: str = "all"):
        """Initialize the sensor.
        
        Args:
            coordinator: The data coordinator
            entry: The config entry
            meal_type: Type of meal to show (all, breakfast, lunch, dinner, snack)
        """
        super().__init__(coordinator)
        self._meal_type = meal_type.upper()
        
        # Namen für verschiedene Sensor-Typen
        type_names = {
            "ALL": "Norish Mahlzeiten Heute",
            "BREAKFAST": "Norish Frühstück",
            "LUNCH": "Norish Mittagessen",
            "DINNER": "Norish Abendessen",
            "SNACK": "Norish Snack",
        }
        
        self._attr_name = type_names.get(self._meal_type, "Norish Mahlzeit")
        self._attr_unique_id = f"{entry.entry_id}_meal_{meal_type}"
        self._attr_icon = "mdi:chef-hat"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        meals = self._get_filtered_meals()
        
        if not meals:
            return "Kein Plan"
        
        # Zeige den Namen des ersten/einzigen Gerichts
        if len(meals) == 1:
            return meals[0]['name']
        
        # Bei mehreren Gerichten: Anzahl anzeigen
        return f"{len(meals)} Mahlzeiten"

    @property
    def entity_picture(self) -> Optional[str]:
        """Return the entity picture (Bild-URL des Gerichts)."""
        meals = self._get_filtered_meals()
        
        if not meals:
            return None
        
        # Nimm das Bild der ersten Mahlzeit (falls vorhanden)
        first_meal = meals[0]
        
        # Priorisiere Bilder über Videos für entity_picture
        image_url = first_meal.get('image')
        
        if image_url:
            _LOGGER.debug(f"Bild-URL gefunden für {first_meal['name']}: {image_url}")
            return image_url
        
        # Fallback: Nutze Video-Thumbnail falls verfügbar
        video_thumbnail = first_meal.get('video_thumbnail')
        if video_thumbnail:
            _LOGGER.debug(f"Video-Thumbnail gefunden für {first_meal['name']}: {video_thumbnail}")
            return video_thumbnail
        
        _LOGGER.debug(f"Kein Bild/Video gefunden für {first_meal['name']}")
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        meals = self._get_filtered_meals()
        attributes = {}
        
        # Gruppierung nach Typ für einfache Anzeige
        for meal in meals:
            m_type = meal['type'].lower()
            if m_type not in attributes:
                attributes[m_type] = []
            attributes[m_type].append(meal['name'])
        
        # Liste für Templates
        attributes["liste"] = [f"{m['type']}: {m['name']}" for m in meals]
        
        # Alle Bilder sammeln
        images = []
        videos = []
        for meal in meals:
            # Bilder
            if meal.get('image'):
                images.append({
                    'name': meal['name'],
                    'type': meal['type'],
                    'url': meal['image']
                })
            
            # Videos
            if meal.get('video'):
                video_info = {
                    'name': meal['name'],
                    'type': meal['type'],
                    'url': meal['video'],
                    'video_type': meal.get('video_type', 'unknown'),
                }
                if meal.get('video_thumbnail'):
                    video_info['thumbnail'] = meal['video_thumbnail']
                if meal.get('youtube_id'):
                    video_info['youtube_id'] = meal['youtube_id']
                videos.append(video_info)
        
        if images:
            attributes["images"] = images
        
        if videos:
            attributes["videos"] = videos
            # Für erste Mahlzeit direkt zugänglich machen
            if meals:
                first_meal = meals[0]
                if first_meal.get('video'):
                    attributes["video_url"] = first_meal['video']
                    attributes["video_type"] = first_meal.get('video_type', 'unknown')
                    if first_meal.get('youtube_id'):
                        attributes["youtube_id"] = first_meal['youtube_id']
                        attributes["youtube_embed_url"] = f"https://www.youtube.com/embed/{first_meal['youtube_id']}"
                    if first_meal.get('video_thumbnail'):
                        attributes["video_thumbnail"] = first_meal['video_thumbnail']
            
        # Vollständige Daten
        attributes["raw_data"] = meals
        
        # Zusätzliche Info
        attributes["meal_count"] = len(meals)
        attributes["has_video"] = len(videos) > 0
        attributes["has_image"] = len(images) > 0
        
        return attributes

    def _get_filtered_meals(self) -> List[Dict[str, Any]]:
        """Get today's meals filtered by type."""
        all_meals = self._get_todays_meals()
        
        # Wenn "all", gib alle zurück
        if self._meal_type == "ALL":
            return all_meals
        
        # Filtere nach Mahlzeit-Typ
        filtered = [
            m for m in all_meals 
            if m['type'].upper() == self._meal_type
        ]
        
        return filtered

    def _extract_video_info(self, video_url: str) -> Dict[str, Any]:
        """Extract video information from URL.
        
        Args:
            video_url: The video URL
            
        Returns:
            Dict with video_type, youtube_id, and thumbnail
        """
        info = {
            'video_type': 'direct',
            'youtube_id': None,
            'thumbnail': None,
        }
        
        if not video_url:
            return info
        
        # YouTube URL-Muster
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        ]
        
        # Prüfe auf YouTube
        for pattern in youtube_patterns:
            match = re.search(pattern, video_url)
            if match:
                youtube_id = match.group(1)
                info['video_type'] = 'youtube'
                info['youtube_id'] = youtube_id
                # Standard YouTube Thumbnail
                info['thumbnail'] = f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg"
                break
        
        # Vimeo
        vimeo_pattern = r'(?:https?://)?(?:www\.)?vimeo\.com/([0-9]+)'
        match = re.search(vimeo_pattern, video_url)
        if match:
            info['video_type'] = 'vimeo'
        
        return info

    def _get_todays_meals(self) -> List[Dict[str, Any]]:
        """Filtert die Kalender-Daten nach dem heutigen Tag."""
        filtered = []
        
        if not self.coordinator.data:
            return filtered
        
        events = self.coordinator.data.get("calendar", [])
        now_date = dt_util.now().date()
        
        for event in events:
            # Datums-String holen
            date_raw = event.get("date") or event.get("day")
            if not date_raw:
                continue
            
            try:
                # Datum parsen
                dt_event = datetime.fromisoformat(
                    date_raw.replace("Z", "+00:00")
                ).date()
                
                # Nur heutige Events
                if dt_event != now_date:
                    continue
                
                # Rezept-Daten extrahieren
                recipe = event.get("recipe")
                
                # Name des Gerichts
                name = "Unbekannt"
                if isinstance(recipe, dict):
                    name = recipe.get("name") or "Rezept ohne Namen"
                else:
                    name = (
                        event.get("recipeName") or
                        event.get("title") or
                        "Gericht"
                    )
                
                # Mahlzeit-Typ
                meal_type = str(
                    event.get("type") or
                    event.get("slot") or
                    "Mahlzeit"
                )
                
                # Bild-URL extrahieren
                image_url = None
                if isinstance(recipe, dict):
                    image_url = (
                        recipe.get("image") or
                        recipe.get("imageUrl") or
                        recipe.get("picture") or
                        recipe.get("photo") or
                        recipe.get("thumbnail")
                    )
                
                # Auch im Event selbst nach Bild suchen
                if not image_url:
                    image_url = (
                        event.get("image") or
                        event.get("imageUrl") or
                        event.get("picture") or
                        event.get("photo")
                    )
                
                # Konvertiere relative URLs zu absoluten URLs
                if image_url and image_url.startswith('/'):
                    base_url = self.coordinator.api_data.get('url', '')
                    image_url = f"{base_url}{image_url}"
                    _LOGGER.debug(f"Relative Bild-URL konvertiert: {image_url}")
                
                # Video-URL extrahieren
                video_url = None
                video_thumbnail = None
                if isinstance(recipe, dict):
                    video_url = (
                        recipe.get("video") or
                        recipe.get("videoUrl") or
                        recipe.get("video_url") or
                        recipe.get("youtubeUrl") or
                        recipe.get("youtube_url")
                    )
                    # Separates Video-Thumbnail
                    video_thumbnail = (
                        recipe.get("videoThumbnail") or
                        recipe.get("video_thumbnail")
                    )
                
                # Auch im Event selbst nach Video suchen
                if not video_url:
                    video_url = (
                        event.get("video") or
                        event.get("videoUrl") or
                        event.get("video_url")
                    )
                
                # Konvertiere relative URLs zu absoluten URLs
                if video_url and video_url.startswith('/'):
                    # Hole Base-URL vom Coordinator
                    base_url = self.coordinator.api_data.get('url', '')
                    video_url = f"{base_url}{video_url}"
                    _LOGGER.debug(f"Relative Video-URL konvertiert: {video_url}")
                
                # Video-Informationen extrahieren
                video_info = {}
                if video_url:
                    video_info = self._extract_video_info(video_url)
                    # Nutze extrahiertes Thumbnail falls kein eigenes vorhanden
                    if not video_thumbnail and video_info.get('thumbnail'):
                        video_thumbnail = video_info['thumbnail']
                
                # Konvertiere relatives Video-Thumbnail zu absoluter URL
                if video_thumbnail and video_thumbnail.startswith('/'):
                    base_url = self.coordinator.api_data.get('url', '')
                    video_thumbnail = f"{base_url}{video_thumbnail}"
                    _LOGGER.debug(f"Relative Video-Thumbnail-URL konvertiert: {video_thumbnail}")
                
                meal_data = {
                    "name": name,
                    "type": meal_type.capitalize(),
                    "image": image_url,
                    "video": video_url,
                    "video_thumbnail": video_thumbnail,
                }
                
                # Video-Zusatzinformationen
                if video_info:
                    meal_data["video_type"] = video_info.get('video_type')
                    meal_data["youtube_id"] = video_info.get('youtube_id')
                
                # Optionale zusätzliche Felder
                if isinstance(recipe, dict):
                    meal_data["description"] = recipe.get("description")
                    meal_data["recipe_id"] = recipe.get("id")
                    meal_data["cooking_time"] = recipe.get("cookingTime")
                    meal_data["servings"] = recipe.get("servings")
                    meal_data["prep_time"] = recipe.get("prepTime")
                    meal_data["total_time"] = recipe.get("totalTime")
                
                filtered.append(meal_data)
                
            except Exception as ex:
                _LOGGER.debug(
                    f"Fehler beim Parsen eines Events im Sensor: {ex}"
                )
                continue
        
        return filtered
    def __init__(self, coordinator, entry):
        """Initialize the week planner sensor."""
        super().__init__(coordinator)
        self._attr_name = "Norish Wochenplan"
        self._attr_unique_id = f"{entry.entry_id}_week_planner"
        self._attr_icon = "mdi:calendar-week"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        week_data = self._get_week_data()
        
        # Zähle geplante Tage
        days_with_meals = sum(1 for day in week_data if day['meals'])
        
        if days_with_meals == 0:
            return "Keine Planung"
        elif days_with_meals == 7:
            return "Woche vollständig geplant"
        else:
            return f"{days_with_meals} Tage geplant"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        week_data = self._get_week_data()
        
        attributes = {
            "week_data": week_data,
            "days_planned": sum(1 for day in week_data if day['meals']),
            "total_meals": sum(len(day['meals']) for day in week_data),
        }
        
        # Separate Listen für einfachen Zugriff
        for day_data in week_data:
            day_key = day_data['weekday_short'].lower()
            attributes[day_key] = day_data
        
        return attributes

    def _get_week_data(self) -> List[Dict[str, Any]]:
        """Get meal data for the next 7 days."""
        if not self.coordinator.data:
            return []
        
        events = self.coordinator.data.get("calendar", [])
        today = dt_util.now().date()
        
        # Deutsche Wochentage
        weekday_names_de = [
            "Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"
        ]
        weekday_short_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        
        week_data = []
        
        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            
            # Wochentag ermitteln
            weekday_index = current_date.weekday()
            weekday_name = weekday_names_de[weekday_index]
            weekday_short = weekday_short_de[weekday_index]
            
            # Mahlzeiten für diesen Tag sammeln
            day_meals = []
            
            for event in events:
                date_raw = event.get("date") or event.get("day")
                if not date_raw:
                    continue
                
                try:
                    event_date = datetime.fromisoformat(
                        date_raw.replace("Z", "+00:00")
                    ).date()
                    
                    if event_date != current_date:
                        continue
                    
                    # Rezept-Informationen extrahieren
                    recipe = event.get("recipe")
                    
                    # Name
                    name = "Unbekannt"
                    if isinstance(recipe, dict):
                        name = recipe.get("name") or "Rezept ohne Namen"
                    else:
                        name = (
                            event.get("recipeName") or
                            event.get("title") or
                            "Gericht"
                        )
                    
                    # Mahlzeit-Typ
                    meal_type = str(
                        event.get("type") or event.get("slot") or "Mahlzeit"
                    ).upper()
                    
                    # Bild-URL
                    image_url = None
                    if isinstance(recipe, dict):
                        image_url = (
                            recipe.get("image") or
                            recipe.get("imageUrl") or
                            recipe.get("picture")
                        )
                    if not image_url:
                        image_url = event.get("image")
                    
                    # Relative URL konvertieren
                    if image_url and image_url.startswith('/'):
                        base_url = self.coordinator.api_data.get('url', '')
                        image_url = f"{base_url}{image_url}"
                    
                    # Video-URL
                    video_url = None
                    if isinstance(recipe, dict):
                        video_url = (
                            recipe.get("video") or
                            recipe.get("videoUrl") or
                            recipe.get("video_url")
                        )
                    if not video_url:
                        video_url = event.get("video")
                    
                    # Relative Video-URL konvertieren
                    if video_url and video_url.startswith('/'):
                        base_url = self.coordinator.api_data.get('url', '')
                        video_url = f"{base_url}{video_url}"
                    
                    # Video-Thumbnail
                    video_thumbnail = None
                    if isinstance(recipe, dict):
                        video_thumbnail = (
                            recipe.get("videoThumbnail") or
                            recipe.get("video_thumbnail")
                        )
                    
                    # Relative Thumbnail-URL konvertieren
                    if video_thumbnail and video_thumbnail.startswith('/'):
                        base_url = self.coordinator.api_data.get('url', '')
                        video_thumbnail = f"{base_url}{video_thumbnail}"
                    
                    # Weitere Details
                    cooking_time = None
                    servings = None
                    description = None
                    
                    if isinstance(recipe, dict):
                        cooking_time = recipe.get("cookingTime")
                        servings = recipe.get("servings")
                        description = recipe.get("description")
                    
                    meal_data = {
                        "name": name,
                        "type": meal_type,
                        "image": image_url,
                        "video": video_url,
                        "video_thumbnail": video_thumbnail,
                        "cooking_time": cooking_time,
                        "servings": servings,
                        "description": description,
                        "has_video": video_url is not None,
                        "has_image": image_url is not None,
                    }
                    
                    day_meals.append(meal_data)
                    
                except Exception as e:
                    _LOGGER.debug(f"Fehler beim Parsen eines Events: {e}")
                    continue
            
            # Sortiere Mahlzeiten nach Typ (Frühstück, Lunch, Dinner, Snack)
            type_order = {"BREAKFAST": 0, "LUNCH": 1, "DINNER": 2, "SNACK": 3}
            day_meals.sort(key=lambda x: type_order.get(x["type"], 99))
            
            # Tag-Daten zusammenstellen
            day_info = {
                "date": current_date.isoformat(),
                "date_formatted": current_date.strftime("%d.%m.%Y"),
                "weekday": weekday_name,
                "weekday_short": weekday_short,
                "is_today": day_offset == 0,
                "is_weekend": weekday_index >= 5,
                "meals": day_meals,
                "meal_count": len(day_meals),
                "has_meals": len(day_meals) > 0,
            }
            
            week_data.append(day_info)
        
        return week_data



class NorishWeekPlannerSensor(CoordinatorEntity, SensorEntity):
    """Sensor für 7-Tage Wochenplan mit Bildern und Videos."""

    def __init__(self, coordinator, entry):
        """Initialize the week planner sensor."""
        super().__init__(coordinator)
        self._attr_name = "Norish Wochenplan"
        self._attr_unique_id = f"{entry.entry_id}_week_planner"
        self._attr_icon = "mdi:calendar-week"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        week_data = self._get_week_data()
        
        # Zähle geplante Tage
        days_with_meals = sum(1 for day in week_data if day['meals'])
        
        if days_with_meals == 0:
            return "Keine Planung"
        elif days_with_meals == 7:
            return "Woche vollständig geplant"
        else:
            return f"{days_with_meals} Tage geplant"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        week_data = self._get_week_data()
        
        attributes = {
            "week_data": week_data,
            "days_planned": sum(1 for day in week_data if day['meals']),
            "total_meals": sum(len(day['meals']) for day in week_data),
        }
        
        # Separate Listen für einfachen Zugriff
        for day_data in week_data:
            day_key = day_data['weekday_short'].lower()
            attributes[day_key] = day_data
        
        return attributes

    def _get_week_data(self) -> List[Dict[str, Any]]:
        """Get meal data for the next 7 days."""
        if not self.coordinator.data:
            return []
        
        events = self.coordinator.data.get("calendar", [])
        today = dt_util.now().date()
        
        # Deutsche Wochentage
        weekday_names_de = [
            "Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"
        ]
        weekday_short_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        
        week_data = []
        
        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            
            # Wochentag ermitteln
            weekday_index = current_date.weekday()
            weekday_name = weekday_names_de[weekday_index]
            weekday_short = weekday_short_de[weekday_index]
            
            # Mahlzeiten für diesen Tag sammeln
            day_meals = []
            
            for event in events:
                date_raw = event.get("date") or event.get("day")
                if not date_raw:
                    continue
                
                try:
                    event_date = datetime.fromisoformat(
                        date_raw.replace("Z", "+00:00")
                    ).date()
                    
                    if event_date != current_date:
                        continue
                    
                    # Rezept-Informationen extrahieren
                    recipe = event.get("recipe")
                    
                    # Name
                    name = "Unbekannt"
                    if isinstance(recipe, dict):
                        name = recipe.get("name") or "Rezept ohne Namen"
                    else:
                        name = (
                            event.get("recipeName") or
                            event.get("title") or
                            "Gericht"
                        )
                    
                    # Mahlzeit-Typ
                    meal_type = str(
                        event.get("type") or event.get("slot") or "Mahlzeit"
                    ).upper()
                    
                    # Bild-URL
                    image_url = None
                    if isinstance(recipe, dict):
                        image_url = (
                            recipe.get("image") or
                            recipe.get("imageUrl") or
                            recipe.get("picture")
                        )
                    if not image_url:
                        image_url = event.get("image")
                    
                    # Relative URL konvertieren
                    if image_url and image_url.startswith('/'):
                        base_url = self.coordinator.api_data.get('url', '')
                        image_url = f"{base_url}{image_url}"
                    
                    # Video-URL
                    video_url = None
                    if isinstance(recipe, dict):
                        video_url = (
                            recipe.get("video") or
                            recipe.get("videoUrl") or
                            recipe.get("video_url")
                        )
                    if not video_url:
                        video_url = event.get("video")
                    
                    # Relative Video-URL konvertieren
                    if video_url and video_url.startswith('/'):
                        base_url = self.coordinator.api_data.get('url', '')
                        video_url = f"{base_url}{video_url}"
                    
                    # Video-Thumbnail
                    video_thumbnail = None
                    if isinstance(recipe, dict):
                        video_thumbnail = (
                            recipe.get("videoThumbnail") or
                            recipe.get("video_thumbnail")
                        )
                    
                    # Relative Thumbnail-URL konvertieren
                    if video_thumbnail and video_thumbnail.startswith('/'):
                        base_url = self.coordinator.api_data.get('url', '')
                        video_thumbnail = f"{base_url}{video_thumbnail}"
                    
                    # Weitere Details
                    cooking_time = None
                    servings = None
                    description = None
                    
                    if isinstance(recipe, dict):
                        cooking_time = recipe.get("cookingTime")
                        servings = recipe.get("servings")
                        description = recipe.get("description")
                    
                    meal_data = {
                        "name": name,
                        "type": meal_type,
                        "image": image_url,
                        "video": video_url,
                        "video_thumbnail": video_thumbnail,
                        "cooking_time": cooking_time,
                        "servings": servings,
                        "description": description,
                        "has_video": video_url is not None,
                        "has_image": image_url is not None,
                    }
                    
                    day_meals.append(meal_data)
                    
                except Exception as e:
                    _LOGGER.debug(f"Fehler beim Parsen eines Events: {e}")
                    continue
            
            # Sortiere Mahlzeiten nach Typ (Frühstück, Lunch, Dinner, Snack)
            type_order = {"BREAKFAST": 0, "LUNCH": 1, "DINNER": 2, "SNACK": 3}
            day_meals.sort(key=lambda x: type_order.get(x["type"], 99))
            
            # Tag-Daten zusammenstellen
            day_info = {
                "date": current_date.isoformat(),
                "date_formatted": current_date.strftime("%d.%m.%Y"),
                "weekday": weekday_name,
                "weekday_short": weekday_short,
                "is_today": day_offset == 0,
                "is_weekend": weekday_index >= 5,
                "meals": day_meals,
                "meal_count": len(day_meals),
                "has_meals": len(day_meals) > 0,
            }
            
            week_data.append(day_info)
        
        return week_data
