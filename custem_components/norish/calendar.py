from datetime import datetime, timedelta, time
import logging
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishCalendar(coordinator, entry)], True)

class NorishCalendar(CoordinatorEntity, CalendarEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Norish Speiseplan"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self):
        now = dt_util.now()
        events = self._get_events_for_range(now, now + timedelta(days=7))
        return events[0] if events else None

    async def async_get_events(self, hass, start_date, end_date):
        return self._get_events_for_range(start_date, end_date)

    def _get_events_for_range(self, start_date, end_date):
        raw_events = self.coordinator.data.get("calendar", [])
        events = []
        
        # Mapping der Slots auf Uhrzeiten (damit sie nicht alle um 12:00 Uhr stehen)
        slot_times = {
            "BREAKFAST": time(8, 0),
            "LUNCH": time(12, 0),
            "SNACK": time(15, 0),
            "DINNER": time(18, 0)
        }

        for item in raw_events:
            try:
                date_raw = item.get("date") or item.get("day")
                if not date_raw: continue
                
                # Datum parsen (ISO Format)
                dt_day = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).date()
                
                # Typ/Slot ermitteln (Großschreibung erzwingen für Mapping)
                raw_slot = str(item.get("type") or item.get("slot") or "LUNCH").upper()
                
                # Uhrzeit aus Mapping holen, sonst 12:00 Uhr
                st_time = slot_times.get(raw_slot, time(12, 0))
                
                # Start- und Endzeit berechnen
                start_dt = dt_util.as_local(datetime.combine(dt_day, st_time))
                
                if start_date <= start_dt <= end_date:
                    recipe = item.get("recipe")
                    # Name des Gerichts finden
                    summary = "Unbekanntes Gericht"
                    if isinstance(recipe, dict) and recipe.get("name"):
                        summary = recipe.get("name")
                    elif item.get("recipeName"):
                        summary = item.get("recipeName")
                    elif item.get("title"):
                        summary = item.get("title")

                    events.append(CalendarEvent(
                        summary=f"{raw_slot.capitalize()}: {summary}",
                        start=start_dt,
                        end=start_dt + timedelta(minutes=45),
                        description=f"Norish Typ: {raw_slot}"
                    ))
            except Exception as e:
                _LOGGER.debug("Fehler bei Kalender-Event: %s", e)
                continue
                
        # Nach Zeit sortieren, damit die Liste im Dashboard Sinn ergibt
        return sorted(events, key=lambda x: x.start)