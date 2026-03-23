"""Todo platform for Norish shopping list."""
from __future__ import annotations

import logging

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NorishListCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Norish todo list."""
    coordinator: NorishListCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishShoppingList(coordinator, entry)])


class NorishShoppingList(CoordinatorEntity, TodoListEntity):
    """Norish Shopping List entity."""

    def __init__(
        self,
        coordinator: NorishListCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the shopping list."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Norish Shopping List"
        self._attr_unique_id = f"{entry.entry_id}_shopping_list"
        self._attr_supported_features = (
            TodoListEntityFeature.CREATE_TODO_ITEM
            | TodoListEntityFeature.UPDATE_TODO_ITEM
            | TodoListEntityFeature.DELETE_TODO_ITEM
        )

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the current list of todo items."""
        items: list[TodoItem] = []
        if not self.coordinator.data:
            return items

        groceries: list[dict] = self.coordinator.data.get("groceries", [])

        for grocery in groceries:
            item_id: str = grocery.get("id", "")
            name: str = grocery.get("name") or grocery.get("ingredient") or "Unknown"
            checked: bool = (
                grocery.get("isDone", False)
                or grocery.get("checked", False)
                or grocery.get("completed", False)
            )
            amount: str = grocery.get("amount") or grocery.get("quantity", "")
            unit: str = grocery.get("unit", "")

            summary = f"{name} ({amount} {unit})".strip() if amount or unit else name

            items.append(
                TodoItem(
                    uid=item_id,
                    summary=summary,
                    status=TodoItemStatus.COMPLETED if checked else TodoItemStatus.NEEDS_ACTION,
                )
            )

        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new todo item (triggers data refresh)."""
        _LOGGER.info("Create todo item requested: %s", item.summary)
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a todo item (triggers data refresh)."""
        _LOGGER.info("Update todo item requested: %s", item.uid)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete todo items (triggers data refresh)."""
        _LOGGER.info("Delete todo items requested: %s", uids)
        await self.coordinator.async_request_refresh()
