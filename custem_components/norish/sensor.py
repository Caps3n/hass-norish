import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

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
        if not meals: return "Kein Plan"
        # Zeige die erste wichtige Mahlzeit oder die Anzahl
        return f"{len(meals)} Mahlzeit(en)"

    @property
    def extra_state_attributes(self):
        meals = self._get_todays_meals()
        # Dynamische Gruppierung nach Typ
        attributes = {}
        for m in meals:
            m_type = m['type'].lower() or "andere"
            if m_type not in attributes:
                attributes[m_type] = []
            attributes[m_type].append(m['name'])
        
        # Zusätzlich eine Liste für alles
        attributes["alle_mahlzeiten"] = [f"{m['type']}: {m['name']}" for m in meals]
        return attributes

    def _get_todays_meals(self):
        filtered = []
        if not self.coordinator.data: return filtered
        events = self.coordinator.data.get("calendar", [])
        today = datetime.date.today().isoformat()
        
        for e in events:
            date_raw = e.get("date") or e.get("day") or ""
            if date_raw[:10] == today:
                recipe = e.get("recipe")
                name = recipe.get("name") if isinstance(recipe, dict) else (e.get("recipeName") or "Gericht")
                # Wir nehmen den Typ so wie er kommt (SNACK, LUNCH, etc.)
                m_type = str(e.get("type") or e.get("slot") or "Andere")
                filtered.append({"name": name, "type": m_type})
        return filtered