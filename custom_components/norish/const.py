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

# Norish API keys are rate-limited by Better Auth (500 requests / 1 h window).
# The request counter only resets after a gap of MORE than one hour without any
# request, so continuous polling slowly exhausts the key and Norish starts
# answering 401 – which looks exactly like an expired key (v1.8.0).
#
# Nightly quiet window: no polling between these local times. The resulting
# gap (> 1 h) resets the counter every night before it can reach the limit.
QUIET_WINDOW_START = (3, 0)   # 03:00 local time
QUIET_WINDOW_END = (4, 5)     # 04:05 local time
# Pause after a 401 burst before deciding the key is really invalid.
RATE_LIMIT_COOLDOWN_SECONDS = 65 * 60
