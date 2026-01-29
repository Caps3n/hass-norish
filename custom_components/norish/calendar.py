"""Calendar Entity für Norish Integration."""
from datetime import datetime, timedelta, time
import logging
from typing import Optional, List

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SLOT_TIMES,
    DEFAULT_MEAL_TIME,
    EVENT_DURATION_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup calendar entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishCalendar(coordinator, entry)], True)


class NorishCalendar(CoordinatorEntity, CalendarEntity):
    """Norish Calendar Entity für den Speiseplan."""

    def __init__(self, coordinator, entry):
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = "Norish Speiseplan"
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_icon = "mdi:calendar-month"

    @property
    def event(self) -> Optional[CalendarEvent]:
        """Return the next upcoming event."""
        now = dt_util.now()
        events = self._get_events_for_range(now, now + timedelta(days=7))
        return events[0] if events else None

    async def async_get_events(
        self, hass, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events_for_range(start_date, end_date)

    def _get_events_for_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Get calendar events for a specific date range."""
        if not self.coordinator.data:
            return []

        raw_events = self.coordinator.data.get("calendar", [])
        events = []

        for item in raw_events:
            try:
                # Datum extrahieren
                date_raw = item.get("date") or item.get("day")
                if not date_raw:
                    continue

                # ISO-Format parsen
                dt_day = datetime.fromisoformat(
                    date_raw.replace("Z", "+00:00")
                ).date()

                # Mahlzeit-Typ
                raw_slot = str(
                    item.get("type") or item.get("slot") or "LUNCH"
                ).upper()

                # Uhrzeit basierend auf Mahlzeit-Typ
                slot_time = SLOT_TIMES.get(raw_slot, DEFAULT_MEAL_TIME)

                # Start- und Endzeit
                start_dt = dt_util.as_local(datetime.combine(dt_day, slot_time))

                # Nur Events im gewünschten Zeitbereich
                if not (start_date <= start_dt <= end_date):
                    continue

                # Rezept-Name extrahieren
                recipe = item.get("recipe")
                summary = "Unbekanntes Gericht"

                if isinstance(recipe, dict) and recipe.get("name"):
                    summary = recipe.get("name")
                elif item.get("recipeName"):
                    summary = item.get("recipeName")
                elif item.get("title"):
                    summary = item.get("title")

                # Beschreibung erstellen
                description_parts = [f"Typ: {raw_slot.capitalize()}"]

                if isinstance(recipe, dict):
                    if recipe.get("description"):
                        description_parts.append(recipe.get("description"))
                    if recipe.get("cookingTime"):
                        description_parts.append(
                            f"Zubereitungszeit: {recipe.get('cookingTime')} Min."
                        )
                    if recipe.get("servings"):
                        description_parts.append(
                            f"Portionen: {recipe.get('servings')}"
                        )

                # Event erstellen
                events.append(
                    CalendarEvent(
                        summary=f"{raw_slot.capitalize()}: {summary}",
                        start=start_dt,
                        end=start_dt + timedelta(minutes=EVENT_DURATION_MINUTES),
                        description="\\n".join(description_parts),
                    )
                )

            except Exception as e:
                _LOGGER.debug("Fehler beim Parsen eines Kalender-Events: %s", e)
                continue

        # Nach Zeit sortieren
        return sorted(events, key=lambda x: x.start)
