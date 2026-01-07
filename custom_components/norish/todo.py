from homeassistant.components.todo import TodoListEntity, TodoItem, TodoItemStatus, TodoListEntityFeature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wir übergeben nun die entry_id an die Entity-Klasse
    entities = [NorishTodoListEntity(coordinator, "unsorted", "Unsortiert", entry.entry_id)]
    
    if coordinator.store_map:
        for sid, sname in coordinator.store_map.items():
            # Sicherstellen, dass wir 'unsorted' nicht doppelt hinzufügen
            if sid != "unsorted":
                entities.append(NorishTodoListEntity(coordinator, sid, sname, entry.entry_id))
                
    async_add_entities(entities)

class NorishTodoListEntity(TodoListEntity):
    def __init__(self, coordinator, store_id, store_name, entry_id):
        super().__init__()
        self._coordinator = coordinator
        self._store_id = store_id
        self._attr_name = f"Norish: {store_name}"
        
        # FIX: Unique ID enthält jetzt die Entry ID, um Konflikte zu vermeiden
        self._attr_unique_id = f"{entry_id}_norish_todo_{store_id}"
        
        self._attr_supported_features = (
            TodoListEntityFeature.CREATE_TODO_ITEM | 
            TodoListEntityFeature.UPDATE_TODO_ITEM | 
            TodoListEntityFeature.DELETE_TODO_ITEM
        )

    @property
    def todo_items(self):
        if not self._coordinator.data: return []
        # Fallback auf leeres Dict, falls 'groceries' fehlt
        groceries = self._coordinator.data.get("groceries") or {}
        raw = groceries.get(self._store_id, [])
        
        return [TodoItem(
            summary=i.get("name", "Unbekannt"), 
            uid=str(i.get("id")), 
            status=TodoItemStatus.COMPLETED if i.get("isDone") else TodoItemStatus.NEEDS_ACTION
        ) for i in raw]

    async def async_create_todo_item(self, item: TodoItem):
        payload = [{
            "name": item.summary,
            "isDone": False,
            "unit": "",
            "amount": 1,
            "storeId": None if self._store_id == "unsorted" else self._store_id
        }]
        
        await self._coordinator.mutate_trpc("groceries.create", payload)
        await self._coordinator.async_refresh()

    async def async_update_todo_item(self, item: TodoItem):
        payload = {"groceryIds": [item.uid], "isDone": (item.status == TodoItemStatus.COMPLETED)}
        await self._coordinator.mutate_trpc("groceries.toggle", payload)
        await self._coordinator.async_refresh()

    async def async_delete_todo_items(self, uids: list[str]):
        await self._coordinator.mutate_trpc("groceries.delete", {"groceryIds": uids})
        await self._coordinator.async_refresh()