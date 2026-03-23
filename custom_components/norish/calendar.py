"""Calendar platform for Norish."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)

SLOT_TIMES: dict[str, tuple[int, int]] = {
    "Breakfast": (7, 0),
    "Lunch": (12, 0),
    "Dinner": (18, 0),
    "Snack": (15, 0),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norish calendar."""
    coordinator: NorishListCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishCalendar(coordinator, entry)])


class NorishCalendar(CoordinatorEntity, CalendarEntity):
    """Norish Meal Calendar entity."""

    def __init__(
        self,
        coordinator: NorishListCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Norish Meal Calendar"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        events = self._get_events_for_range(
            dt_util.now(), dt_util.now() + timedelta(days=1)
        )
        return events[0] if events else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events_for_range(start_date, end_date)

    def _get_events_for_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get events for a date range."""
        events: list[CalendarEvent] = []

        if not self.coordinator.data:
            return events

        calendar_data: list[dict] = self.coordinator.data.get("calendar", [])
        start_date_only = start_date.date() if hasattr(start_date, "date") else start_date
        end_date_only = end_date.date() if hasattr(end_date, "date") else end_date

        for item in calendar_data:
            try:
                event_date_str: str = item.get("date", "")
                if not event_date_str:
                    continue

                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()

                if not (start_date_only <= event_date <= end_date_only):
                    continue

                name: str = item.get("recipeName") or "Meal"
                recipe_details: dict = item.get("_recipe") or {}
                if recipe_details.get("name"):
                    name = recipe_details["name"]

                slot: str = item.get("slot") or "Meal"
                hour, minute = SLOT_TIMES.get(slot, (12, 0))

                start_dt = datetime.combine(
                    event_date,
                    datetime.min.time().replace(hour=hour, minute=minute),
                )
                end_dt = start_dt + timedelta(hours=1)

                events.append(
                    CalendarEvent(
                        start=start_dt,
                        end=end_dt,
                        summary=f"{slot}: {name}",
                        description=f"Norish – {slot}",
                    )
                )

            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Failed to parse calendar event: %s", err)
                continue

        return sorted(events, key=lambda x: x.start)
