import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishMealSensor(coordinator, entry)])

class NorishMealSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Norish Mahlzeiten Heute"
        self._attr_unique_id = f"{entry.entry_id}_meal_today"
        self._attr_icon = "mdi:chef-hat"

    @property
    def native_value(self):
        meals = self._get_todays_meals()
        if not meals:
            return "Kein Plan"
        
        # Zeige die Anzahl an, oder den Namen des ersten Gerichts, wenn es nur eins ist
        count = len(meals)
        if count == 1:
            return meals[0]['name']
        return f"{count} Mahlzeiten"

    @property
    def extra_state_attributes(self):
        meals = self._get_todays_meals()
        attributes = {}
        
        # Gruppierung nach Typ für einfache Anzeige im Dashboard
        for m in meals:
            m_type = m['type'].lower()
            if m_type not in attributes:
                attributes[m_type] = []
            attributes[m_type].append(m['name'])
        
        # Eine flache Liste für Templates
        attributes["liste"] = [f"{m['type']}: {m['name']}" for m in meals]
        attributes["raw_data"] = meals
        return attributes

    def _get_todays_meals(self):
        """Filtert die Kalender-Daten nach dem heutigen Tag."""
        filtered = []
        if not self.coordinator.data: 
            return filtered
            
        events = self.coordinator.data.get("calendar", [])
        
        # WICHTIG: Wir nutzen die lokale Zeit von Home Assistant
        now_date = dt_util.now().date()
        
        for e in events:
            # Datums-String holen
            date_raw = e.get("date") or e.get("day")
            if not date_raw: 
                continue
            
            try:
                # Parsing analog zum Kalender (ISO Format mit Z-Handling)
                # replace("Z", "+00:00") ist wichtig für Python < 3.11
                dt_event = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).date()
                
                # Exakter Vergleich der Datum-Objekte
                if dt_event == now_date:
                    recipe = e.get("recipe")
                    
                    # Robustes Auslesen des Namens
                    name = "Unbekannt"
                    if isinstance(recipe, dict):
                        name = recipe.get("name") or "Rezept ohne Namen"
                    else:
                        name = e.get("recipeName") or e.get("title") or "Gericht"
                    
                    # Typ (Lunch, Dinner etc.)
                    m_type = str(e.get("type") or e.get("slot") or "Mahlzeit")
                    
                    filtered.append({
                        "name": name, 
                        "type": m_type.capitalize()
                    })
            except Exception as ex:
                # Wir loggen Fehler, damit der Sensor nicht abstürzt
                _LOGGER.debug(f"Fehler beim Parsen eines Events im Sensor: {ex}")
                continue
                
        # Sortieren nach Typ (Frühstück vor Abendessen ist zwar nicht garantiert durch Alphabet,
        # aber besser als zufällig)
        return filtered