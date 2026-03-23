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


def _grocery_to_todo_item(grocery: dict) -> TodoItem:
    """Convert a Norish grocery dict to a HA TodoItem."""
    item_id: str = grocery.get("id", "")
    name: str = grocery.get("name") or grocery.get("ingredient") or "Unknown"
    is_done: bool = (
        grocery.get("isDone", False)
        or grocery.get("checked", False)
        or grocery.get("completed", False)
    )
    amount = grocery.get("amount") or grocery.get("quantity", "")
    unit: str = grocery.get("unit", "")

    # Build summary: "250g Risoni (Orzo)" style
    if amount and unit:
        summary = f"{amount}{unit} {name}"
    elif amount:
        summary = f"{amount}× {name}"
    else:
        summary = name

    return TodoItem(
        uid=item_id,
        summary=summary,
        status=TodoItemStatus.COMPLETED if is_done else TodoItemStatus.NEEDS_ACTION,
    )


class NorishShoppingList(CoordinatorEntity, TodoListEntity):
    """Norish Shopping List entity — syncs check/uncheck back to Norish."""

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
        """Return all grocery items (regular + recurring)."""
        if not self.coordinator.data:
            return []

        groceries: list[dict] = self.coordinator.data.get("groceries", [])
        recurring: list[dict] = self.coordinator.data.get("recurring_groceries", [])

        items = [_grocery_to_todo_item(g) for g in groceries]
        items += [_grocery_to_todo_item(g) for g in recurring]
        return items

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Toggle item done/undone — syncs back to Norish."""
        is_done = item.status == TodoItemStatus.COMPLETED
        _LOGGER.debug(
            "Norish: update todo item %s → isDone=%s", item.uid, is_done
        )
        if item.uid:
            await self.coordinator.async_toggle_grocery(item.uid, is_done)
        else:
            await self.coordinator.async_request_refresh()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new todo item (refresh only — creation not yet supported)."""
        _LOGGER.info("Norish: create todo item requested: %s (not supported)", item.summary)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete todo items (refresh only — deletion not yet supported)."""
        _LOGGER.info("Norish: delete todo items requested: %s (not supported)", uids)
        await self.coordinator.async_request_refresh()
