"""Sensor für Norish Mahlzeiten - Norish v0.16+ API."""
import logging
from datetime import timedelta
from typing import Optional, List, Dict, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        NorishMealSensor(coordinator, entry, "all"),
        NorishMealSensor(coordinator, entry, "breakfast"),
        NorishMealSensor(coordinator, entry, "lunch"),
        NorishMealSensor(coordinator, entry, "dinner"),
        NorishMealSensor(coordinator, entry, "snack"),
        NorishWeekPlannerSensor(coordinator, entry),
    ]
    
    async_add_entities(sensors)


class NorishMealSensor(CoordinatorEntity, SensorEntity):
    """Sensor für Norish Mahlzeiten."""

    def __init__(self, coordinator, entry, meal_type: str = "all"):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._meal_type = meal_type.upper()
        
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

    def _get_base_url(self) -> str:
        """Hole Base-URL von Norish."""
        return self.coordinator.api_data.get('url', '').rstrip('/')

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        meals = self._get_filtered_meals()
        if not meals:
            return "Kein Plan"
        if len(meals) == 1:
            return meals[0]['name']
        return f"{len(meals)} Mahlzeiten"

    @property
    def entity_picture(self) -> Optional[str]:
        """Return the entity picture."""
        meals = self._get_filtered_meals()
        if not meals:
            return None
        return meals[0].get('image')

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        meals = self._get_filtered_meals()
        
        attributes = {
            "meal_count": len(meals),
            "liste": [f"{m['type']}: {m['name']}" for m in meals],
            "raw_data": meals,
        }
        
        if meals:
            first = meals[0]
            if first.get('image'):
                attributes["image_url"] = first['image']
            if first.get('recipe_id'):
                attributes["recipe_id"] = first['recipe_id']
        
        return attributes

    def _get_filtered_meals(self) -> List[Dict[str, Any]]:
        """Get today's meals filtered by type."""
        all_meals = self._get_todays_meals()
        if self._meal_type == "ALL":
            return all_meals
        return [m for m in all_meals if m['type'].upper() == self._meal_type]

    def _get_todays_meals(self) -> List[Dict[str, Any]]:
        """Hole heutige Mahlzeiten."""
        filtered = []
        
        if not self.coordinator.data:
            return filtered
        
        events = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")
        base_url = self._get_base_url()
        
        for event in events:
            # Datum prüfen (Format: "2026-02-02")
            event_date = event.get("date", "")
            if event_date != today_str:
                continue
            
            # Name aus recipeName oder _recipe
            name = event.get("recipeName") or "Unbekannt"
            recipe_details = event.get("_recipe", {})
            if recipe_details and recipe_details.get("name"):
                name = recipe_details.get("name")
            
            # Typ aus slot
            slot = event.get("slot") or "Mahlzeit"
            meal_type = slot.upper() if slot else "MEAL"
            
            # Recipe ID
            recipe_id = event.get("recipeId")
            
            # Bild-URL - bevorzuge lokales gecachtes Bild
            image_url = event.get("_local_image")  # Lokales gecachtes Bild
            
            if not image_url:
                # Fallback: Versuche aus _recipe
                if recipe_details:
                    image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                
                # Wenn image_url relativ ist, base_url voranstellen
                if image_url and image_url.startswith("/") and base_url:
                    image_url = f"{base_url}{image_url}"
                elif not image_url and recipe_id and base_url:
                    image_url = f"{base_url}/api/recipes/{recipe_id}/image"
            
            meal_data = {
                "name": name,
                "type": meal_type.capitalize(),
                "recipe_id": recipe_id,
                "image": image_url,
            }
            
            filtered.append(meal_data)
        
        return filtered


class NorishWeekPlannerSensor(CoordinatorEntity, SensorEntity):
    """Sensor für 7-Tage Wochenplan."""

    def __init__(self, coordinator, entry):
        """Initialize the week planner sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Norish Wochenplan"
        self._attr_unique_id = f"{entry.entry_id}_week_planner"
        self._attr_icon = "mdi:calendar-week"

    def _get_base_url(self) -> str:
        """Hole Base-URL von Norish."""
        return self.coordinator.api_data.get('url', '').rstrip('/')

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        week_data = self._get_week_data()
        days_with_meals = sum(1 for day in week_data if day.get('meals'))
        
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
            "days_planned": sum(1 for day in week_data if day.get('meals')),
            "total_meals": sum(len(day.get('meals', [])) for day in week_data),
        }
        
        for day_data in week_data:
            day_key = day_data.get('weekday_short', 'xx').lower()
            attributes[day_key] = day_data
        
        return attributes

    def _get_week_data(self) -> List[Dict[str, Any]]:
        """Hole Mahlzeiten für die nächsten 7 Tage."""
        if not self.coordinator.data:
            return self._generate_empty_week()
        
        events = self.coordinator.data.get("calendar", [])
        if not events:
            return self._generate_empty_week()
        
        today = dt_util.now().date()
        base_url = self._get_base_url()
        
        weekday_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        weekday_short = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        
        week_data = []
        
        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            current_date_str = current_date.strftime("%Y-%m-%d")
            weekday_index = current_date.weekday()
            
            day_meals = []
            
            for event in events:
                event_date = event.get("date", "")
                if event_date != current_date_str:
                    continue
                
                name = event.get("recipeName") or "Unbekannt"
                recipe_details = event.get("_recipe", {})
                if recipe_details and recipe_details.get("name"):
                    name = recipe_details.get("name")
                
                slot = event.get("slot") or "Mahlzeit"
                meal_type = slot.upper() if slot else "MEAL"
                
                recipe_id = event.get("recipeId")
                
                # Bild-URL - bevorzuge lokales gecachtes Bild
                image_url = event.get("_local_image")  # Lokales gecachtes Bild
                
                if not image_url:
                    # Fallback: Versuche aus _recipe
                    if recipe_details:
                        image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                    
                    # Wenn image_url relativ ist, base_url voranstellen
                    if image_url and image_url.startswith("/") and base_url:
                        image_url = f"{base_url}{image_url}"
                    elif not image_url and recipe_id and base_url:
                        image_url = f"{base_url}/api/recipes/{recipe_id}/image"
                
                meal_data = {
                    "name": name,
                    "type": meal_type,
                    "recipe_id": recipe_id,
                    "image": image_url,
                }
                
                day_meals.append(meal_data)
            
            type_order = {"BREAKFAST": 0, "LUNCH": 1, "DINNER": 2, "SNACK": 3}
            day_meals.sort(key=lambda x: type_order.get(x.get("type", ""), 99))
            
            day_info = {
                "date": current_date_str,
                "date_formatted": current_date.strftime("%d.%m."),
                "weekday": weekday_names[weekday_index],
                "weekday_short": weekday_short[weekday_index],
                "is_today": day_offset == 0,
                "is_weekend": weekday_index >= 5,
                "meals": day_meals,
                "meal_count": len(day_meals),
                "has_meals": len(day_meals) > 0,
            }
            
            week_data.append(day_info)
        
        return week_data

    def _generate_empty_week(self) -> List[Dict[str, Any]]:
        """Generiere leere Wochenstruktur."""
        today = dt_util.now().date()
        weekday_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        weekday_short = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        
        week_data = []
        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            weekday_index = current_date.weekday()
            
            week_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "date_formatted": current_date.strftime("%d.%m."),
                "weekday": weekday_names[weekday_index],
                "weekday_short": weekday_short[weekday_index],
                "is_today": day_offset == 0,
                "is_weekend": weekday_index >= 5,
                "meals": [],
                "meal_count": 0,
                "has_meals": False,
            })
        
        return week_data
