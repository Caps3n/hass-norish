"""Constants for the Norish integration."""

DOMAIN = "norish"
DEFAULT_URL = "https://norish.example.com"

ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_UNKNOWN = "unknown"

DEFAULT_SHOW_BREAKFAST = True
DEFAULT_SHOW_LUNCH = True
DEFAULT_SHOW_DINNER = True
DEFAULT_SHOW_SNACK = True

# Options: configurable poll interval
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_POLL_INTERVAL = 900  # 15 minutes

# Available poll interval choices (seconds → human-readable label)
POLL_INTERVAL_OPTIONS: dict[int, str] = {
    60:   "1 minute",
    300:  "5 minutes",
    600:  "10 minutes",
    900:  "15 minutes",
    1800: "30 minutes",
    3600: "60 minutes",
}

# Optional Norish login credentials for automatic API key renewal (v1.6.9).
# When stored, the coordinator can silently create a new API key when the
# current one is exhausted — no manual "Reconfigure" required.
CONF_NORISH_EMAIL = "norish_email"
CONF_NORISH_PASSWORD = "norish_password"
