"""Sensor platform for Norish meal planning - Norish v0.16+ API."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up Norish sensor entities."""
    coordinator: NorishListCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = [
        NorishMealSensor(coordinator, entry, "all"),
        NorishMealSensor(coordinator, entry, "breakfast"),
        NorishMealSensor(coordinator, entry, "lunch"),
        NorishMealSensor(coordinator, entry, "dinner"),
        NorishMealSensor(coordinator, entry, "snack"),
        NorishWeekPlannerSensor(coordinator, entry),
    ]

    async_add_entities(sensors)


class NorishMealSensor(CoordinatorEntity, SensorEntity):
    """Sensor for Norish meals."""

    def __init__(
        self,
        coordinator: NorishListCoordinator,
        entry: ConfigEntry,
        meal_type: str = "all",
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._meal_type = meal_type.upper()

        type_names: dict[str, str] = {
            "ALL": "Norish Meals Today",
            "BREAKFAST": "Norish Breakfast",
            "LUNCH": "Norish Lunch",
            "DINNER": "Norish Dinner",
            "SNACK": "Norish Snack",
        }

        self._attr_name = type_names.get(self._meal_type, "Norish Meal")
        self._attr_unique_id = f"{entry.entry_id}_meal_{meal_type}"
        self._attr_icon = "mdi:chef-hat"

    def _get_base_url(self) -> str:
        """Return the Norish base URL."""
        return self.coordinator.api_data.get("url", "").rstrip("/")

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        meals = self._get_filtered_meals()
        if not meals:
            return "No plan"
        if len(meals) == 1:
            return meals[0]["name"]
        return f"{len(meals)} meals"

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture."""
        meals = self._get_filtered_meals()
        if not meals:
            return None
        return meals[0].get("image")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        meals = self._get_filtered_meals()

        attributes: dict[str, Any] = {
            "meal_count": len(meals),
            "meals": [f"{m['type']}: {m['name']}" for m in meals],
            "raw_data": meals,
        }

        if meals:
            first = meals[0]
            if first.get("image"):
                attributes["image_url"] = first["image"]
            if first.get("recipe_id"):
                attributes["recipe_id"] = first["recipe_id"]

        return attributes

    def _get_filtered_meals(self) -> list[dict[str, Any]]:
        """Get today's meals filtered by type."""
        all_meals = self._get_todays_meals()
        if self._meal_type == "ALL":
            return all_meals
        return [m for m in all_meals if m["type"].upper() == self._meal_type]

    def _get_todays_meals(self) -> list[dict[str, Any]]:
        """Return today's meals from coordinator data."""
        filtered: list[dict[str, Any]] = []

        if not self.coordinator.data:
            return filtered

        events: list[dict[str, Any]] = self.coordinator.data.get("calendar", [])
        today_str = dt_util.now().strftime("%Y-%m-%d")
        base_url = self._get_base_url()

        for event in events:
            event_date = event.get("date", "")
            if event_date != today_str:
                continue

            # Prefer recipe name from detail fetch, fall back to event field
            name: str = event.get("recipeName") or "Unknown"
            recipe_details: dict[str, Any] = event.get("_recipe") or {}
            if recipe_details.get("name"):
                name = recipe_details["name"]

            slot: str = event.get("slot") or "meal"
            meal_type = slot.upper() if slot else "MEAL"

            recipe_id: str | None = event.get("recipeId")

            # Prefer locally cached image, then remote, then fallback URL
            image_url: str | None = event.get("_local_image")
            if not image_url:
                if recipe_details:
                    image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                if image_url and image_url.startswith("/") and base_url:
                    image_url = f"{base_url}{image_url}"
                elif not image_url and recipe_id and base_url:
                    image_url = f"{base_url}/api/recipes/{recipe_id}/image"

            filtered.append(
                {
                    "name": name,
                    "type": meal_type.capitalize(),
                    "recipe_id": recipe_id,
                    "image": image_url,
                }
            )

        return filtered


class NorishWeekPlannerSensor(CoordinatorEntity, SensorEntity):
    """Sensor providing a 7-day meal plan overview."""

    def __init__(
        self,
        coordinator: NorishListCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the week planner sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Norish Week Planner"
        self._attr_unique_id = f"{entry.entry_id}_week_planner"
        self._attr_icon = "mdi:calendar-week"

    def _get_base_url(self) -> str:
        """Return the Norish base URL."""
        return self.coordinator.api_data.get("url", "").rstrip("/")

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        week_data = self._get_week_data()
        days_with_meals = sum(1 for day in week_data if day.get("meals"))

        if days_with_meals == 0:
            return "No meals planned"
        if days_with_meals == 7:
            return "Full week planned"
        return f"{days_with_meals} days planned"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        week_data = self._get_week_data()

        attributes: dict[str, Any] = {
            "week_data": week_data,
            "days_planned": sum(1 for day in week_data if day.get("meals")),
            "total_meals": sum(len(day.get("meals", [])) for day in week_data),
        }

        for day_data in week_data:
            day_key = day_data.get("weekday_short", "xx").lower()
            attributes[day_key] = day_data

        return attributes

    def _get_week_data(self) -> list[dict[str, Any]]:
        """Return meal data for the next 7 days."""
        if not self.coordinator.data or not self.coordinator.data.get("calendar"):
            return self._generate_empty_week()

        events: list[dict[str, Any]] = self.coordinator.data["calendar"]
        today = dt_util.now().date()
        base_url = self._get_base_url()

        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_short = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        type_order = {"BREAKFAST": 0, "LUNCH": 1, "DINNER": 2, "SNACK": 3}

        week_data: list[dict[str, Any]] = []

        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            current_date_str = current_date.strftime("%Y-%m-%d")
            weekday_index = current_date.weekday()

            day_meals: list[dict[str, Any]] = []

            for event in events:
                if event.get("date", "") != current_date_str:
                    continue

                name: str = event.get("recipeName") or "Unknown"
                recipe_details: dict[str, Any] = event.get("_recipe") or {}
                if recipe_details.get("name"):
                    name = recipe_details["name"]

                slot: str = event.get("slot") or "meal"
                meal_type = slot.upper() if slot else "MEAL"

                recipe_id: str | None = event.get("recipeId")

                image_url: str | None = event.get("_local_image")
                if not image_url:
                    if recipe_details:
                        image_url = recipe_details.get("image") or recipe_details.get("imageUrl")
                    if image_url and image_url.startswith("/") and base_url:
                        image_url = f"{base_url}{image_url}"
                    elif not image_url and recipe_id and base_url:
                        image_url = f"{base_url}/api/recipes/{recipe_id}/image"

                day_meals.append(
                    {
                        "name": name,
                        "type": meal_type,
                        "recipe_id": recipe_id,
                        "image": image_url,
                    }
                )

            day_meals.sort(key=lambda x: type_order.get(x.get("type", ""), 99))

            week_data.append(
                {
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
            )

        return week_data

    def _generate_empty_week(self) -> list[dict[str, Any]]:
        """Return an empty 7-day week structure."""
        today = dt_util.now().date()
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_short = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

        return [
            {
                "date": (today + timedelta(days=i)).strftime("%Y-%m-%d"),
                "date_formatted": (today + timedelta(days=i)).strftime("%d.%m."),
                "weekday": weekday_names[(today + timedelta(days=i)).weekday()],
                "weekday_short": weekday_short[(today + timedelta(days=i)).weekday()],
                "is_today": i == 0,
                "is_weekend": (today + timedelta(days=i)).weekday() >= 5,
                "meals": [],
                "meal_count": 0,
                "has_meals": False,
            }
            for i in range(7)
        ]
