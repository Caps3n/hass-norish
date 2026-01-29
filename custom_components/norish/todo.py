"""Todo List Entity für Norish Einkaufslisten."""
import logging
from typing import List

from homeassistant.components.todo import (
    TodoListEntity,
    TodoItem,
    TodoItemStatus,
    TodoListEntityFeature,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STORE_UNSORTED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup todo list entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Erstelle Todo-Listen für alle Stores
    entities = [
        NorishTodoListEntity(
            coordinator, STORE_UNSORTED, "Unsortiert", entry.entry_id
        )
    ]

    # Füge Todo-Listen für alle konfigurierten Stores hinzu
    if coordinator.store_map:
        for store_id, store_name in coordinator.store_map.items():
            if store_id != STORE_UNSORTED:
                entities.append(
                    NorishTodoListEntity(
                        coordinator, store_id, store_name, entry.entry_id
                    )
                )

    async_add_entities(entities)


class NorishTodoListEntity(CoordinatorEntity, TodoListEntity):
    """Todo List Entity für eine Norish Einkaufsliste."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator, store_id: str, store_name: str, entry_id: str):
        """Initialize the todo list.
        
        Args:
            coordinator: The data coordinator
            store_id: ID of the store
            store_name: Display name of the store
            entry_id: Config entry ID for unique ID generation
        """
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._store_id = store_id
        self._attr_name = f"Norish: {store_name}"
        self._attr_unique_id = f"{entry_id}_norish_todo_{store_id}"
        self._attr_icon = "mdi:cart"

    @property
    def todo_items(self) -> List[TodoItem]:
        """Return the todo items."""
        if not self._coordinator.data:
            return []

        groceries = self._coordinator.data.get("groceries") or {}
        raw_items = groceries.get(self._store_id, [])

        items = []
        for item in raw_items:
            try:
                # Name mit optionaler Menge und Einheit
                name_parts = []
                if item.get("amount") and item.get("amount") != 1:
                    name_parts.append(str(item.get("amount")))
                if item.get("unit"):
                    name_parts.append(item.get("unit"))
                name_parts.append(item.get("name", "Unbekannt"))

                summary = " ".join(name_parts)

                # Status
                status = (
                    TodoItemStatus.COMPLETED
                    if item.get("isDone")
                    else TodoItemStatus.NEEDS_ACTION
                )

                items.append(
                    TodoItem(
                        summary=summary,
                        uid=str(item.get("id")),
                        status=status,
                    )
                )
            except Exception as e:
                _LOGGER.debug("Fehler beim Parsen eines Todo-Items: %s", e)
                continue

        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new todo item."""
        # Parse Name, Menge und Einheit (einfaches Parsing)
        parts = item.summary.split(None, 2)
        amount = 1
        unit = ""
        name = item.summary

        # Versuche Menge zu extrahieren (z.B. "2 kg Äpfel" -> amount=2, unit=kg, name=Äpfel)
        if len(parts) >= 3:
            try:
                amount = float(parts[0])
                unit = parts[1]
                name = parts[2]
            except (ValueError, IndexError):
                name = item.summary
        elif len(parts) == 2:
            try:
                amount = float(parts[0])
                name = parts[1]
            except (ValueError, IndexError):
                name = item.summary

        payload = [
            {
                "name": name,
                "isDone": False,
                "unit": unit,
                "amount": amount,
                "storeId": (
                    None if self._store_id == STORE_UNSORTED else self._store_id
                ),
            }
        ]

        success = await self._coordinator.mutate_trpc(
            "groceries.create", payload
        )
        if success:
            await self._coordinator.async_refresh()
        else:
            _LOGGER.error("Fehler beim Erstellen des Todo-Items")

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a todo item."""
        payload = {
            "groceryIds": [item.uid],
            "isDone": (item.status == TodoItemStatus.COMPLETED),
        }

        success = await self._coordinator.mutate_trpc(
            "groceries.toggle", payload
        )
        if success:
            await self._coordinator.async_refresh()
        else:
            _LOGGER.error("Fehler beim Aktualisieren des Todo-Items")

    async def async_delete_todo_items(self, uids: List[str]) -> None:
        """Delete todo items."""
        payload = {"groceryIds": uids}

        success = await self._coordinator.mutate_trpc(
            "groceries.delete", payload
        )
        if success:
            await self._coordinator.async_refresh()
        else:
            _LOGGER.error("Fehler beim Löschen der Todo-Items")
