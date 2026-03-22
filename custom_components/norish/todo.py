"""Todo platform for Norish shopping list."""
import logging
from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Norish todo list."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NorishShoppingList(coordinator, entry)])


class NorishShoppingList(CoordinatorEntity, TodoListEntity):
    """Norish Shopping List Entity."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Norish Einkaufsliste"
        self._attr_unique_id = f"{entry.entry_id}_shopping_list"
        self._attr_supported_features = (
            TodoListEntityFeature.CREATE_TODO_ITEM
            | TodoListEntityFeature.UPDATE_TODO_ITEM
            | TodoListEntityFeature.DELETE_TODO_ITEM
        )

    @property
    def todo_items(self) -> list[TodoItem]:
        items = []
        if not self.coordinator.data:
            return items

        groceries = self.coordinator.data.get("groceries", [])
        
        for grocery in groceries:
            item_id = grocery.get("id", "")
            name = grocery.get("name") or grocery.get("ingredient") or "Unbekannt"
            checked = grocery.get("checked", False) or grocery.get("completed", False)
            amount = grocery.get("amount") or grocery.get("quantity", "")
            unit = grocery.get("unit", "")
            
            summary = f"{name} ({amount} {unit})".strip() if amount or unit else name

            items.append(TodoItem(
                uid=item_id,
                summary=summary,
                status=TodoItemStatus.COMPLETED if checked else TodoItemStatus.NEEDS_ACTION,
            ))

        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        _LOGGER.info(f"Erstelle Todo: {item.summary}")
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        _LOGGER.info(f"Update Todo: {item.uid}")
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        _LOGGER.info(f"Lösche Todos: {uids}")
        await self.coordinator.async_request_refresh()
