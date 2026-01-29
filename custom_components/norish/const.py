"""Konstanten für die Norish Integration."""
from datetime import time

# Domain
DOMAIN = "norish"

# Konfigurations-Schlüssel
CONF_URL = "url"
CONF_API_KEY = "api_key"

# Standard URL
DEFAULT_URL = "https://norish.deine-domain.com"

# Update-Intervalle
UPDATE_INTERVAL_SECONDS = 300  # 5 Minuten
UPDATE_INTERVAL_FAST_SECONDS = 30  # 30 Sekunden für schnelle Updates

# Kalender-Konfiguration
CALENDAR_DAYS_PAST = 1
CALENDAR_DAYS_FUTURE = 14
EVENT_DURATION_MINUTES = 45

# Mahlzeiten-Slots und Uhrzeiten
SLOT_BREAKFAST = "BREAKFAST"
SLOT_LUNCH = "LUNCH"
SLOT_SNACK = "SNACK"
SLOT_DINNER = "DINNER"

SLOT_TIMES = {
    SLOT_BREAKFAST: time(8, 0),
    SLOT_LUNCH: time(12, 0),
    SLOT_SNACK: time(15, 0),
    SLOT_DINNER: time(18, 0),
}

# Default Fallback-Zeit wenn Slot unbekannt
DEFAULT_MEAL_TIME = time(12, 0)

# API-Konfiguration
API_TIMEOUT_SECONDS = 10
API_MAX_RETRIES = 3
API_RETRY_DELAY_BASE = 1  # Sekunden für exponentielles Backoff

# tRPC Endpoints
ENDPOINT_STORES_LIST = "stores.list"
ENDPOINT_CALENDAR_LIST = "calendar.listRecipes"
ENDPOINT_GROCERIES_LIST = "groceries.list"
ENDPOINT_GROCERIES_CREATE = "groceries.create"
ENDPOINT_GROCERIES_TOGGLE = "groceries.toggle"
ENDPOINT_GROCERIES_DELETE = "groceries.delete"

# Grocery Store IDs
STORE_UNSORTED = "unsorted"

# Icons
ICON_MEAL = "mdi:chef-hat"
ICON_GROCERY = "mdi:cart"
ICON_CALENDAR = "mdi:calendar-month"

# Attribute Keys für Entities
ATTR_RAW_DATA = "raw_data"
ATTR_LISTE = "liste"
ATTR_LAST_UPDATE = "last_update"
ATTR_STORE_NAME = "store_name"
ATTR_ITEM_COUNT = "item_count"

# Fehlermeldungen
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"

# Options Flow Defaults
DEFAULT_SHOW_BREAKFAST = True
DEFAULT_SHOW_LUNCH = True
DEFAULT_SHOW_DINNER = True
DEFAULT_SHOW_SNACK = True
