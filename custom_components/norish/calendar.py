"""Calendar platform for Norish."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
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
    """Set up Norish calendar."""
    coordinator: NorishListCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishCalendar(coordinator, entry)])


class NorishCalendar(CoordinatorEntity, CalendarEntity):
    """Norish Calendar Entity."""

    def __init__(self, coordinator, entry):
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Norish Mahlzeiten"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        events = self._get_events_for_range(dt_util.now(), dt_util.now() + timedelta(days=1))
        return events[0] if events else None

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events_for_range(start_date, end_date)

    def _get_events_for_range(self, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Get events for a date range."""
        events = []
        
        if not self.coordinator.data:
            return events

        calendar_data = self.coordinator.data.get("calendar", [])
        start_date_only = start_date.date() if hasattr(start_date, 'date') else start_date
        end_date_only = end_date.date() if hasattr(end_date, 'date') else end_date

        for item in calendar_data:
            try:
                event_date_str = item.get("date", "")
                if not event_date_str:
                    continue
                    
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()

                if not (start_date_only <= event_date <= end_date_only):
                    continue

                name = item.get("recipeName") or "Mahlzeit"
                recipe_details = item.get("_recipe", {})
                if recipe_details and recipe_details.get("name"):
                    name = recipe_details.get("name")
                    
                slot = item.get("slot") or "Mahlzeit"

                slot_times = {"Breakfast": (7, 0), "Lunch": (12, 0), "Dinner": (18, 0), "Snack": (15, 0)}
                hour, minute = slot_times.get(slot, (12, 0))

                start_dt = datetime.combine(event_date, datetime.min.time().replace(hour=hour, minute=minute))
                end_dt = start_dt + timedelta(hours=1)

                event = CalendarEvent(
                    start=start_dt,
                    end=end_dt,
                    summary=f"{slot}: {name}",
                    description=f"Norish {slot}",
                )
                events.append(event)

            except Exception as e:
                _LOGGER.debug(f"Fehler beim Parsen des Events: {e}")
                continue

        return sorted(events, key=lambda x: x.start)
