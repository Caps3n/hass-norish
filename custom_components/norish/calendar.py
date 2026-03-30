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
from .coordinator import NorishCoordinator

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
    coordinator: NorishCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishCalendar(coordinator, entry)])


class NorishCalendar(CoordinatorEntity, CalendarEntity):
    """Norish Meal Calendar entity."""

    def __init__(
        self,
        coordinator: NorishCoordinator,
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
        now = dt_util.now()
        events = self._get_events_for_range(now, now + timedelta(days=1))
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
        """Get events for a date range, returning timezone-aware CalendarEvents."""
        events: list[CalendarEvent] = []

        if not self.coordinator.data:
            return events

        # Use HA's local timezone for all datetime operations
        local_tz = dt_util.get_time_zone(self.hass.config.time_zone)

        calendar_data: list[dict] = self.coordinator.data.get("calendar", [])

        # Normalise boundaries to dates for comparison
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

                # Resolve display name
                name: str = item.get("recipeName") or "Meal"
                recipe_details: dict = item.get("_recipe") or {}
                if recipe_details.get("name"):
                    name = recipe_details["name"]

                slot: str = item.get("slot") or "Meal"
                hour, minute = SLOT_TIMES.get(slot, (12, 0))

                # Build timezone-aware start/end datetimes
                start_dt = datetime(
                    event_date.year,
                    event_date.month,
                    event_date.day,
                    hour,
                    minute,
                    0,
                    tzinfo=local_tz,
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
