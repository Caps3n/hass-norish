"""Coordinator for the Norish API.

v1.8.0 – Rate-limit aware polling + Norish v0.25 API changes.
- Root cause of the "API key expired" banner after ~24 h: Norish API keys are
  rate-limited (500 requests per 1 h window) and the counter only resets after
  more than one hour WITHOUT any request. Continuous polling therefore exhausts
  the key and Norish answers 401 although the key itself is still valid.
  * calendar.listItems + groceries.list are now fetched in ONE batched tRPC
    request (the key is verified once per HTTP request → half the usage).
  * Nightly quiet window (03:00–04:05 local): no polling, so the counter resets
    every night.
  * A 401 burst that survives direct validation now triggers a 65-minute
    cooldown first. Only if the key is still rejected after the cooldown is
    ConfigEntryAuthFailed raised.
- groceries.toggle / groceries.delete now take ``groceries: [{id, version}]``
  (Norish changed the input from ``groceryIds``) – fixes check/delete in HA.
- New: groceries.create and groceries.update (add / rename items from HA).
- Recipe images fall back to ``recipeImage`` returned by calendar.listItems.

v1.7.0 – Calendar notes support.
- Calendar items can now carry a free-text ``note`` field (e.g. "Going out for dinner").
- Notes are surfaced in the CalendarEvent summary (when no recipe is planned) and
  in the event description so they are visible in all HA calendar views.

v1.6.13 – Transient-401 resilience: direct key validation before auth-failed.
- When MAX_AUTH_FAILURES consecutive 401s occur (and auto-renewal is not
  possible or fails), the coordinator now performs a direct key-validation
  request before raising ConfigEntryAuthFailed.
  * If the validation succeeds → the 401s were transient (e.g. Norish server
    restarted briefly) → consecutive-auth counter is reset and the coordinator
    continues polling normally.
  * If the validation also returns 401 → the key is truly expired →
    ConfigEntryAuthFailed is raised as before.
  * If the validation hits a network error → the server is temporarily
    unreachable → UpdateFailed is raised so HA retries later.

v1.6.9 – Automatic API key renewal using stored Norish credentials.
- When the API key is exhausted (requestCount >= rateLimitMax with no refill),
  Norish returns 401 after ~2-3 days of HA polling.
- If email + password are stored in the config entry, the coordinator silently
  renews the key instead of requiring manual reconfiguration:
    1. POST /api/auth/sign-in/email  → obtain a session token
    2. POST /api/auth/api-key/create → create a new key named "HomeAssistant"
    3. Update config_entry.data and resume polling without interruption
- Without credentials the existing behaviour is preserved (Reconfigure
  notification after MAX_AUTH_FAILURES consecutive 401s).

v1.6.8 – Exponential reconnect backoff.
- After any failure (401, timeout, connection error) the update_interval is
  temporarily increased so HA waits longer before the next retry:
    1st failure  → 60 s
    2nd failure  → 5 min
    3rd+ failure → 10 min  (until MAX_AUTH_FAILURES → ConfigEntryAuthFailed)
- On the first successful response the interval resets to the user-configured
  value automatically.

v1.6.7 – Increased request timeout + transient-401 resilience.
- Request timeout raised from 10 s to 30 s to handle slow Norish API responses
  without false-positive "timeout after 3 attempts" errors in the HA log.
- All v1.6.6 features retained:
  * Consecutive-401 counter: ConfigEntryAuthFailed is only raised after
    MAX_AUTH_FAILURES (3) consecutive 401s; a single transient 401 is retried.
  * Poll interval user-configurable via the Options flow (1/5/10/15/30/60 min)
  * Store list cached in memory, refreshed every 24 hours
  * Recipe details cached until the calendar recipe-ID set changes
  * HTTP 429 raises UpdateFailed (retried next interval, not permanent failure)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import urllib.parse
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any, NoReturn

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_NORISH_EMAIL,
    CONF_NORISH_PASSWORD,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    QUIET_WINDOW_END,
    QUIET_WINDOW_START,
    RATE_LIMIT_COOLDOWN_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2
IMAGE_CACHE_DIR = "www/norish_images"

# How often to re-fetch the store list (it basically never changes).
STORE_REFRESH_HOURS = 24

# How many consecutive 401 responses before we give up and ask the user to
# re-authenticate.  A single transient 401 is treated as a temporary failure
# (UpdateFailed) so HA retries on the next poll interval instead of stopping
# all polling immediately.
MAX_AUTH_FAILURES = 3

# Exponential reconnect backoff: seconds to wait after consecutive failures.
# Index 0 → 1st failure, index 1 → 2nd failure, last entry used for all
# subsequent failures until MAX_AUTH_FAILURES is reached.
RECONNECT_BACKOFF_SECONDS: list[int] = [60, 300, 600]


class NorishCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for the Norish API with API key authentication."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        base_url: str,
        api_key: str,
        *,
        norish_email: str = "",
        norish_password: str = "",
    ) -> None:
        """Initialize the coordinator."""
        poll_interval: int = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        _LOGGER.debug("Norish: poll interval set to %d seconds", poll_interval)

        super().__init__(
            hass,
            _LOGGER,
            name="Norish API",
            update_interval=timedelta(seconds=poll_interval),
            config_entry=entry,
        )
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._norish_email = norish_email
        self._norish_password = norish_password
        # Guard: only one renewal attempt at a time
        self._renewal_in_progress: bool = False
        self.store_map: dict[str, str] = {}
        self._last_successful_update: date | None = None
        self._image_cache_path = os.path.join(
            hass.config.config_dir, IMAGE_CACHE_DIR
        )
        os.makedirs(self._image_cache_path, exist_ok=True)

        # --- Caches to avoid redundant API calls ---
        # Store cache: fetch once, refresh every STORE_REFRESH_HOURS
        self._cached_stores: dict[str, str] = {}
        self._stores_last_fetched: datetime | None = None

        # Recipe cache: { recipe_id: recipe_dict }
        # Only invalidated when the set of recipe IDs in the calendar changes.
        self._cached_recipes: dict[str, Any] = {}
        self._cached_recipe_ids: frozenset[str] = frozenset()

        # Consecutive 401 counter.  Resets to 0 on any successful request.
        # ConfigEntryAuthFailed is only raised once this reaches MAX_AUTH_FAILURES.
        self._consecutive_auth_failures: int = 0

        # Reconnect backoff: counts any type of failure across update cycles.
        # Resets to 0 on the first successful _async_update_data call.
        self._consecutive_failures: int = 0
        # Remember the user-configured interval so we can restore it after backoff.
        self._normal_update_interval = timedelta(seconds=poll_interval)

        # Rate-limit cooldown (v1.8.0): set when a 401 burst survives direct
        # validation. While active, no requests are sent so the key's rate-limit
        # window can reset. _cooldown_used stays True until the next success, so
        # a key that is still rejected after the cooldown triggers re-auth.
        self._cooldown_until: datetime | None = None
        self._cooldown_used: bool = False
        # Set while refreshing right after a user action (see mutations).
        self._force_refresh: bool = False

    def _get_headers(self) -> dict[str, str]:
        """Return headers for authenticated API requests."""
        return {
            "x-api-key": self._api_key,
            "User-Agent": "HomeAssistant/Norish",
            "Accept": "application/json",
        }

    async def _async_validate_key(self) -> bool | None:
        """Perform a direct API-key validation request.

        Returns:
            True  – key is valid (200 response)
            False – key is invalid/expired (401 response)
            None  – network/server error (cannot determine key status)
        """
        url = (
            f"{self.base_url}/api/trpc/groceries.list"
            "?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D"
        )
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    return False
                return True
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    def _apply_reconnect_backoff(self) -> None:
        """Adjust update_interval based on consecutive failure count.

        Called after every _async_update_data completion (success or failure).
        On success (failures == 0) the normal interval is restored.
        On failure the interval is increased exponentially so HA waits longer
        before the next retry, reducing wasted API requests against a dead key.
        A running rate-limit cooldown always takes precedence.
        """
        if self._cooldown_active():
            remaining = self._cooldown_until - dt_util.utcnow()  # type: ignore[operator]
            self.update_interval = max(remaining, timedelta(seconds=60))
            return

        if self._consecutive_failures <= 0:
            if self.update_interval != self._normal_update_interval:
                _LOGGER.info(
                    "Norish: connection restored – resuming normal poll interval (%ds)",
                    int(self._normal_update_interval.total_seconds()),
                )
            self.update_interval = self._normal_update_interval
            return

        idx = min(self._consecutive_failures - 1, len(RECONNECT_BACKOFF_SECONDS) - 1)
        backoff = RECONNECT_BACKOFF_SECONDS[idx]
        new_interval = timedelta(seconds=backoff)
        if self.update_interval != new_interval:
            _LOGGER.warning(
                "Norish: failure #%d – slowing down reconnect, next attempt in %ds",
                self._consecutive_failures,
                backoff,
            )
        self.update_interval = new_interval

    async def _async_renew_api_key(self) -> bool:
        """Silently renew the Norish API key using stored credentials.

        Returns True on success (self._api_key updated, config entry persisted),
        False if renewal is not possible or fails.

        Flow:
          1. POST /api/auth/sign-in/email  → session token
          2. POST /api/auth/api-key/create → new API key
          3. hass.config_entries.async_update_entry → persisted
        """
        if self._renewal_in_progress:
            _LOGGER.debug("Norish: API key renewal already in progress, skipping")
            return False

        if not self._norish_email or not self._norish_password:
            _LOGGER.debug(
                "Norish: no Norish credentials stored – skipping auto-renewal. "
                "Enter email + password in the integration settings to enable this."
            )
            return False

        self._renewal_in_progress = True
        try:
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=30)

            # --- Step 1: sign in and get a session token ---
            # Better Auth supports both email-based and username-based login.
            # Detect which one to use by checking for "@" in the credential.
            credential = self._norish_email  # may be an e-mail or a plain username
            if "@" in credential:
                sign_in_url = f"{self.base_url}/api/auth/sign-in/email"
                sign_in_payload = {
                    "email": credential,
                    "password": self._norish_password,
                    "rememberMe": False,
                }
            else:
                sign_in_url = f"{self.base_url}/api/auth/sign-in/username"
                sign_in_payload = {
                    "username": credential,
                    "password": self._norish_password,
                    "rememberMe": False,
                }
            _LOGGER.info("Norish: attempting automatic API key renewal …")
            async with session.post(
                sign_in_url,
                json=sign_in_payload,
                timeout=timeout,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    _LOGGER.warning(
                        "Norish: sign-in failed (status %d): %s", resp.status, body[:200]
                    )
                    return False
                sign_in_data: dict[str, Any] = await resp.json()

            # Better Auth returns the token either at top-level or under "token"
            token: str = (
                sign_in_data.get("token")
                or (sign_in_data.get("data") or {}).get("token", "")
            )
            if not token:
                _LOGGER.warning(
                    "Norish: sign-in response contained no token: %s",
                    str(sign_in_data)[:200],
                )
                return False

            # --- Step 2: create a new API key ---
            create_url = f"{self.base_url}/api/auth/api-key/create"
            async with session.post(
                create_url,
                json={"name": "HomeAssistant"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=timeout,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    _LOGGER.warning(
                        "Norish: API key creation failed (status %d): %s",
                        resp.status, body[:200],
                    )
                    return False
                key_data: dict[str, Any] = await resp.json()

            new_key: str = (
                key_data.get("key")
                or (key_data.get("data") or {}).get("key", "")
            )
            if not new_key:
                _LOGGER.warning(
                    "Norish: API key creation response contained no key: %s",
                    str(key_data)[:200],
                )
                return False

            # --- Step 3: persist and apply the new key ---
            self._api_key = new_key
            self._consecutive_auth_failures = 0
            self._consecutive_failures = 0

            new_data = {
                **self.config_entry.data,
                CONF_API_KEY: new_key,
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            _LOGGER.info("Norish: API key renewed automatically ✓")
            return True

        except aiohttp.ClientError as err:
            _LOGGER.warning("Norish: API key renewal network error: %s", err)
            return False
        except asyncio.TimeoutError:
            _LOGGER.warning("Norish: API key renewal timed out")
            return False
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Norish: API key renewal failed unexpectedly: %s", err)
            return False
        finally:
            self._renewal_in_progress = False

    # ------------------------------------------------------------------
    # Rate-limit helpers (v1.8.0)
    # ------------------------------------------------------------------

    def _cooldown_active(self) -> bool:
        """Return True while a rate-limit cooldown is running."""
        return (
            self._cooldown_until is not None
            and dt_util.utcnow() < self._cooldown_until
        )

    @staticmethod
    def _in_quiet_window() -> bool:
        """Return True during the nightly no-polling window (local time)."""
        now = dt_util.now().time()
        return time(*QUIET_WINDOW_START) <= now < time(*QUIET_WINDOW_END)

    async def _handle_unauthorized(self, context: str) -> NoReturn:
        """Decide how to react to a 401 from Norish. Always raises.

        Norish answers 401 both for an invalid key and for a rate-limited key,
        so a 401 alone never proves the key is dead:
          1. Fewer than MAX_AUTH_FAILURES in a row → transient, retry later.
          2. Stored credentials → renew the key silently.
          3. Direct validation succeeds → transient burst, retry later.
          4. Key still rejected → 65-minute cooldown (lets the rate-limit
             window reset). Only if the key is STILL rejected after the
             cooldown is ConfigEntryAuthFailed raised.
        """
        self._consecutive_auth_failures += 1
        _LOGGER.warning(
            "Norish: 401 for %s – consecutive auth failures: %d/%d",
            context, self._consecutive_auth_failures, MAX_AUTH_FAILURES,
        )
        if self._consecutive_auth_failures < MAX_AUTH_FAILURES:
            raise UpdateFailed(
                f"Norish: transient 401 for {context} "
                f"({self._consecutive_auth_failures}/{MAX_AUTH_FAILURES}, will retry)"
            )

        if await self._async_renew_api_key():
            raise UpdateFailed(f"Norish: API key renewed, retrying {context}")

        key_valid = await self._async_validate_key()
        if key_valid is True:
            _LOGGER.warning(
                "Norish: 401 burst but direct validation succeeded – "
                "treating as transient, resetting auth counter."
            )
            self._consecutive_auth_failures = 0
            raise UpdateFailed(f"Norish: transient 401 burst for {context}")
        if key_valid is None:
            raise UpdateFailed(
                f"Norish: cannot reach server after 401 burst for {context}"
            )

        if not self._cooldown_used:
            self._cooldown_used = True
            self._consecutive_auth_failures = 0
            self._cooldown_until = dt_util.utcnow() + timedelta(
                seconds=RATE_LIMIT_COOLDOWN_SECONDS
            )
            _LOGGER.warning(
                "Norish: API key rejected – most likely the Norish rate limit "
                "(500 requests/hour, resets only after 1 h without requests). "
                "Pausing all requests for %d minutes before re-checking.",
                RATE_LIMIT_COOLDOWN_SECONDS // 60,
            )
            raise UpdateFailed("Norish: API key rate-limited, cooling down")

        _LOGGER.error(
            "Norish: API key still rejected after the rate-limit cooldown – "
            "key is invalid or expired. Re-authentication required."
        )
        raise ConfigEntryAuthFailed("Norish API key invalid or expired")

    # ------------------------------------------------------------------
    # tRPC helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_get_trpc_result(
        data: list[Any] | None,
        default: Any = None,
        index: int = 0,
    ) -> Any:
        """Safely extract one tRPC result from a batch response."""
        if not data or not isinstance(data, list) or len(data) <= index:
            return default
        try:
            element = data[index]
            if "error" in element:
                error = element["error"].get("json", element["error"])
                _LOGGER.error(
                    "tRPC error in response: %s",
                    error.get("message", "unknown error"),
                )
                return default
            return element.get("result", {}).get("data", {}).get("json", default)
        except (KeyError, AttributeError, IndexError) as err:
            _LOGGER.warning("Failed to extract tRPC result: %s", err)
            return default

    async def _fetch_trpc(
        self,
        procedure: str,
        payload: dict[str, Any] | None = None,
    ) -> list[Any] | None:
        """Fetch a single tRPC query (see _fetch_trpc_batch)."""
        return await self._fetch_trpc_batch([(procedure, payload)])

    async def _fetch_trpc_batch(
        self,
        calls: list[tuple[str, dict[str, Any] | None]],
    ) -> list[Any] | None:
        """Fetch several tRPC queries in ONE HTTP request, with retry.

        Norish verifies the API key once per HTTP request, so batching
        directly reduces rate-limit usage. Result i belongs to calls[i].
        """
        procedures = ",".join(procedure for procedure, _ in calls)
        trpc_input = {
            str(i): {"json": payload} for i, (_, payload) in enumerate(calls)
        }
        encoded = urllib.parse.quote(
            json.dumps(trpc_input, separators=(",", ":"))
        )
        url = f"{self.base_url}/api/trpc/{procedures}?batch=1&input={encoded}"
        session = async_get_clientsession(self.hass)
        headers = self._get_headers()

        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 401:
                        await self._handle_unauthorized(procedures)

                    if resp.status == 429:
                        # Rate-limited: tell HA to wait until next poll interval.
                        retry_after = resp.headers.get("Retry-After", "unknown")
                        _LOGGER.warning(
                            "Norish: rate-limited (429) for %s – retry-after: %s. "
                            "Will retry on next poll interval.",
                            procedures, retry_after,
                        )
                        raise UpdateFailed(
                            f"Norish API rate limit reached for {procedures} "
                            f"(Retry-After: {retry_after})"
                        )

                    if resp.status == 404:
                        _LOGGER.error(
                            "Norish: endpoint not found (404): %s", procedures
                        )
                        return None

                    if resp.status >= 500:
                        if attempt < MAX_RETRIES - 1:
                            delay = RETRY_DELAY_BASE * (2 ** attempt)
                            _LOGGER.warning(
                                "Norish: server error %s for %s, retry %d/%d in %ds",
                                resp.status, procedures,
                                attempt + 1, MAX_RETRIES, delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        _LOGGER.error(
                            "Norish: server error %s for %s after %d attempts",
                            resp.status, procedures, MAX_RETRIES,
                        )
                        return None

                    # 207 = tRPC batch where only some calls failed; the
                    # per-call errors are handled by _safe_get_trpc_result.
                    if resp.status not in (200, 207):
                        text = await resp.text()
                        _LOGGER.error(
                            "Norish: unexpected status %s for %s: %s",
                            resp.status, procedures, text[:200],
                        )
                        return None

                    # Successful response – reset the auth failure counter
                    self._consecutive_auth_failures = 0
                    return await resp.json()  # type: ignore[no-any-return]

            except (ConfigEntryAuthFailed, UpdateFailed):
                raise  # Never swallow auth failures or explicit rate-limit errors

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    _LOGGER.warning(
                        "Norish: timeout for %s, retry %d/%d in %ds",
                        procedures, attempt + 1, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: timeout for %s after %d attempts",
                    procedures, MAX_RETRIES,
                )
                return None

            except (
                aiohttp.ServerDisconnectedError,
                aiohttp.ClientConnectorError,
            ) as err:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    _LOGGER.warning(
                        "Norish: connection dropped for %s (%s), retry %d/%d in %ds",
                        procedures, type(err).__name__,
                        attempt + 1, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: connection failed for %s after %d attempts: %s",
                    procedures, MAX_RETRIES, err,
                )
                return None

            except aiohttp.ClientError as err:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    _LOGGER.warning(
                        "Norish: network error for %s: %s, retry %d/%d in %ds",
                        procedures, err, attempt + 1, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                _LOGGER.error(
                    "Norish: network error for %s: %s", procedures, err
                )
                return None

        return None

    async def _post_trpc(
        self,
        procedure: str,
        payload: Any,
    ) -> list[Any] | None:
        """POST a mutation to a tRPC endpoint."""
        url = f"{self.base_url}/api/trpc/{procedure}?batch=1"
        headers = {
            **self._get_headers(),
            "Content-Type": "application/json",
        }
        body = json.dumps({"0": {"json": payload}})
        session = async_get_clientsession(self.hass)

        try:
            async with session.post(
                url, headers=headers, data=body,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    await self._handle_unauthorized(f"POST {procedure}")
                if resp.status == 429:
                    _LOGGER.warning(
                        "Norish: POST %s rate-limited (429)", procedure
                    )
                    raise UpdateFailed(
                        f"Norish API rate limit reached for POST {procedure}"
                    )
                if resp.status not in (200, 201):
                    text = await resp.text()
                    _LOGGER.error(
                        "Norish: POST %s failed with status %s: %s",
                        procedure, resp.status, text[:200],
                    )
                    return None
                self._consecutive_auth_failures = 0
                return await resp.json()  # type: ignore[no-any-return]
        except aiohttp.ClientError as err:
            _LOGGER.error("Norish: POST %s network error: %s", procedure, err)
            return None
        except asyncio.TimeoutError:
            _LOGGER.error("Norish: POST %s timed out", procedure)
            return None

    # ------------------------------------------------------------------
    # Public mutation helpers (used by todo.py)
    # ------------------------------------------------------------------

    async def _async_refresh_after_mutation(self) -> None:
        """Refresh right away so follow-up actions use the new item versions.

        Not debounced (async_request_refresh waits up to 10 s), and allowed
        inside the nightly quiet window because the user just acted.
        """
        self._force_refresh = True
        try:
            await self.async_refresh()
        finally:
            self._force_refresh = False

    def _grocery_refs(self, grocery_ids: list[str]) -> list[dict[str, Any]]:
        """Return [{id, version}] for the given IDs from the last poll.

        Norish uses optimistic locking: every grocery mutation must send the
        item's current version, otherwise the change is rejected as stale.
        """
        groceries: list[dict[str, Any]] = (
            self.data.get("groceries", []) if self.data else []
        )
        version_by_id = {g.get("id"): g.get("version") for g in groceries}
        refs: list[dict[str, Any]] = []
        for grocery_id in grocery_ids:
            version = version_by_id.get(grocery_id)
            if not isinstance(version, int) or version < 1:
                _LOGGER.warning(
                    "Norish: no version known for grocery %s – skipping", grocery_id
                )
                continue
            refs.append({"id": grocery_id, "version": version})
        return refs

    async def async_delete_groceries(self, grocery_ids: list[str]) -> bool:
        """Delete grocery items from Norish."""
        refs = self._grocery_refs(grocery_ids)
        if not refs:
            return False
        result = await self._post_trpc("groceries.delete", {"groceries": refs})
        if result is None:
            _LOGGER.error("Norish: failed to delete groceries %s", grocery_ids)
            return False
        _LOGGER.debug("Norish: deleted groceries %s", grocery_ids)
        await self._async_refresh_after_mutation()
        return True

    async def async_toggle_grocery(
        self, grocery_id: str, is_done: bool
    ) -> bool:
        """Toggle a grocery item's done state."""
        refs = self._grocery_refs([grocery_id])
        if not refs:
            return False
        payload: dict[str, Any] = {"groceries": refs, "isDone": is_done}
        result = await self._post_trpc("groceries.toggle", payload)
        if result is None:
            _LOGGER.error(
                "Norish: failed to toggle grocery %s (isDone=%s)",
                grocery_id, is_done,
            )
            return False
        _LOGGER.debug("Norish: toggled grocery %s → isDone=%s", grocery_id, is_done)
        await self._async_refresh_after_mutation()
        return True

    async def async_create_grocery(self, text: str, store_id: str | None) -> bool:
        """Add a new grocery item to Norish (optionally assigned to a store)."""
        payload = [
            {
                "id": str(uuid.uuid4()),
                "name": text,
                "unit": None,
                "amount": None,
                "isDone": False,
                "storeId": store_id,
            }
        ]
        result = await self._post_trpc("groceries.create", payload)
        if result is None:
            _LOGGER.error("Norish: failed to create grocery '%s'", text)
            return False
        _LOGGER.debug("Norish: created grocery '%s' (store %s)", text, store_id)
        await self._async_refresh_after_mutation()
        return True

    async def async_rename_grocery(self, grocery_id: str, text: str) -> bool:
        """Change a grocery item's text; Norish parses amount/unit from it."""
        refs = self._grocery_refs([grocery_id])
        if not refs:
            return False
        payload = {
            "groceryId": grocery_id,
            "raw": text,
            "version": refs[0]["version"],
        }
        result = await self._post_trpc("groceries.update", payload)
        if result is None:
            _LOGGER.error("Norish: failed to rename grocery %s", grocery_id)
            return False
        _LOGGER.debug("Norish: renamed grocery %s → '%s'", grocery_id, text)
        await self._async_refresh_after_mutation()
        return True

    # ------------------------------------------------------------------
    # Core data update
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all Norish data.

        On 401: see _handle_unauthorized (cooldown first, re-auth only after).
        On 429: raises UpdateFailed so HA retries on the next poll interval.
        On network errors: raises UpdateFailed so HA retries on next poll.
        Backoff: update_interval grows after each failure and resets on success.
        """
        # During a rate-limit cooldown or the nightly quiet window no request is
        # sent at all – that gap is what resets the key's rate-limit counter.
        # Keep serving the last data so entities stay available.
        if self._cooldown_active():
            self._apply_reconnect_backoff()
            if self.data:
                return self.data
            raise UpdateFailed("Norish: API key rate-limited, cooling down")
        if self.data and self._in_quiet_window() and not self._force_refresh:
            _LOGGER.debug("Norish: nightly quiet window – skipping poll")
            return self.data

        data: dict[str, Any] = {
            "calendar": [],
            "groceries": [],
            "stores": {},
        }

        try:
            await self._fetch_calendar_and_groceries(data)
            await self._fetch_stores_cached(data)
        except ConfigEntryAuthFailed:
            # API key is invalid → user must reconfigure
            self._consecutive_failures += 1
            self._apply_reconnect_backoff()
            raise
        except UpdateFailed:
            # Rate-limit or explicit failure → HA will retry on next interval
            self._consecutive_failures += 1
            self._apply_reconnect_backoff()
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Norish: failed to fetch core data: %s", err)
            self._consecutive_failures += 1
            self._apply_reconnect_backoff()
            raise UpdateFailed(f"Error fetching Norish data: {err}") from err

        # --- Optional: recipe details + image caching ---
        try:
            await self._fetch_recipe_details_cached(data)
            await self._download_and_cache_images(data)
        except ConfigEntryAuthFailed:
            _LOGGER.warning(
                "Norish: recipe endpoint returned 401 – core data loaded OK"
            )
        except UpdateFailed as err:
            _LOGGER.warning(
                "Norish: recipe fetch rate-limited, using cached recipes: %s", err
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Norish: recipe details / image caching failed: %s", err
            )

        # Success – reset all failure counters and restore normal poll interval
        self._consecutive_failures = 0
        self._consecutive_auth_failures = 0
        self._cooldown_used = False
        self._cooldown_until = None
        self._apply_reconnect_backoff()

        self._last_successful_update = date.today()
        _LOGGER.info(
            "Norish: loaded %d calendar events, %d grocery items",
            len(data.get("calendar", [])),
            len(data.get("groceries", [])),
        )
        return data

    # ------------------------------------------------------------------
    # Data fetch methods
    # ------------------------------------------------------------------

    async def _fetch_calendar_and_groceries(self, data: dict[str, Any]) -> None:
        """Fetch calendar entries and the grocery list in ONE request."""
        today = date.today()
        start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

        _LOGGER.debug("Norish: fetching calendar %s → %s + groceries", start_date, end_date)

        batch = await self._fetch_trpc_batch(
            [
                ("calendar.listItems", {"startISO": start_date, "endISO": end_date}),
                ("groceries.list", None),
            ]
        )
        if not batch:
            _LOGGER.warning("Norish: no calendar / grocery data received")
            return

        self._parse_calendar(data, self._safe_get_trpc_result(batch, [], index=0))
        self._parse_groceries(data, self._safe_get_trpc_result(batch, {}, index=1))

    @staticmethod
    def _parse_calendar(data: dict[str, Any], items: Any) -> None:
        """Store calendar.listItems result (recipes and notes)."""
        if isinstance(items, list):
            data["calendar"] = items
            _LOGGER.debug("Norish: loaded %d calendar items", len(items))
        else:
            _LOGGER.warning("Norish: unexpected calendar format: %s", type(items))

    @staticmethod
    def _parse_groceries(data: dict[str, Any], result: Any) -> None:
        """Store groceries.list result ({groceries, recurringGroceries, ...})."""
        if isinstance(result, list):
            items: list[Any] = result
        elif isinstance(result, dict):
            items = result.get("groceries", [])
        else:
            _LOGGER.warning("Norish: unexpected grocery format: %s", type(result))
            return

        if not isinstance(items, list):
            _LOGGER.warning(
                "Norish: unexpected groceries list format: %s", type(items)
            )
            return

        data["groceries"] = items

        recurring = (
            result.get("recurringGroceries", [])
            if isinstance(result, dict) else []
        )
        data["recurring_groceries"] = (
            recurring if isinstance(recurring, list) else []
        )

        _LOGGER.debug(
            "Norish: loaded %d grocery items, %d recurring",
            len(items), len(data["recurring_groceries"]),
        )

    async def _fetch_stores_cached(self, data: dict[str, Any]) -> None:
        """Fetch the store list, using the in-memory cache when possible.

        Stores almost never change, so we only call the API once every
        STORE_REFRESH_HOURS hours instead of on every poll.
        """
        now = datetime.now()
        cache_expired = (
            self._stores_last_fetched is None
            or (now - self._stores_last_fetched).total_seconds()
            > STORE_REFRESH_HOURS * 3600
        )

        # An empty store list is a valid cache entry too (users without stores)
        if not cache_expired:
            _LOGGER.debug("Norish: using cached store list (%d stores)", len(self._cached_stores))
            data["stores"] = dict(self._cached_stores)
            self.store_map = dict(self._cached_stores)
            return

        _LOGGER.debug("Norish: fetching store list from API")
        s_data = await self._fetch_trpc("stores.list")
        if not s_data:
            # Fall back to cache if we have one
            if self._cached_stores:
                _LOGGER.warning("Norish: stores.list returned no data, using cached store list")
                data["stores"] = dict(self._cached_stores)
                self.store_map = dict(self._cached_stores)
            return

        stores = self._safe_get_trpc_result(s_data, [])
        new_store_map: dict[str, str] = {}
        if isinstance(stores, list):
            for store in stores:
                store_id = store.get("id")
                store_name = store.get("name")
                if store_id and store_name:
                    new_store_map[store_id] = store_name

        self._cached_stores = new_store_map
        self._stores_last_fetched = now
        data["stores"] = dict(new_store_map)
        self.store_map = dict(new_store_map)
        _LOGGER.debug("Norish: fetched and cached %d stores", len(new_store_map))

    async def _fetch_recipe_details_cached(self, data: dict[str, Any]) -> None:
        """Fetch recipe details, only re-fetching when the recipe ID set changes.

        If the set of recipe IDs in the current calendar is identical to the
        last fetch, the cached recipe details are reused — zero extra API calls.
        """
        calendar_items: list[dict[str, Any]] = data.get("calendar", [])
        current_recipe_ids: frozenset[str] = frozenset(
            event["recipeId"]
            for event in calendar_items
            if event.get("recipeId")
        )

        if not current_recipe_ids:
            return

        if current_recipe_ids == self._cached_recipe_ids and self._cached_recipes:
            _LOGGER.debug(
                "Norish: recipe IDs unchanged, reusing cache (%d recipes)",
                len(self._cached_recipes),
            )
        else:
            # Fetch only the IDs we don't already have cached
            new_ids = current_recipe_ids - set(self._cached_recipes.keys())
            if new_ids:
                _LOGGER.debug(
                    "Norish: fetching %d new recipe(s) (cache has %d)",
                    len(new_ids), len(self._cached_recipes),
                )
                for recipe_id in new_ids:
                    details = await self._fetch_recipe_details(recipe_id)
                    if details:
                        self._cached_recipes[recipe_id] = details
            else:
                _LOGGER.debug("Norish: all recipes already cached")

            # Remove recipes no longer referenced in the calendar
            stale_ids = set(self._cached_recipes.keys()) - current_recipe_ids
            for stale_id in stale_ids:
                del self._cached_recipes[stale_id]

            self._cached_recipe_ids = current_recipe_ids

        # Attach cached recipe data to calendar events
        for event in calendar_items:
            recipe_id = event.get("recipeId")
            if recipe_id and recipe_id in self._cached_recipes:
                event["_recipe"] = self._cached_recipes[recipe_id]

    async def _fetch_recipe_details(
        self, recipe_id: str
    ) -> dict[str, Any] | None:
        """Fetch details for a single recipe."""
        try:
            r_data = await self._fetch_trpc("recipes.get", {"id": recipe_id})
            if r_data:
                result = self._safe_get_trpc_result(r_data, None)
                if result:
                    _LOGGER.debug(
                        "Norish: loaded recipe '%s'",
                        result.get("name", "unknown"),
                    )
                    return result  # type: ignore[no-any-return]
        except ConfigEntryAuthFailed:
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Norish: failed to load recipe %s: %s", recipe_id, err
            )
        return None

    # ------------------------------------------------------------------
    # Image caching
    # ------------------------------------------------------------------

    async def _download_and_cache_images(self, data: dict[str, Any]) -> None:
        """Download and locally cache recipe images."""
        calendar_items: list[dict[str, Any]] = data.get("calendar", [])

        for event in calendar_items:
            if event.get("itemType") == "note":
                continue
            recipe = event.get("_recipe") or {}
            # calendar.listItems already returns recipeImage (Norish v0.19+)
            image_path: str | None = (
                recipe.get("image")
                or recipe.get("imageUrl")
                or event.get("recipeImage")
            )
            if not image_path:
                continue

            image_url = (
                f"{self.base_url}{image_path}"
                if image_path.startswith("/")
                else image_path
            )
            local_path = await self._cache_image(
                image_url, event.get("recipeId", "unknown")
            )
            if local_path:
                event["_local_image"] = local_path

    async def _cache_image(
        self, image_url: str, recipe_id: str
    ) -> str | None:
        """Download an image and cache it locally."""
        try:
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]  # noqa: S324
            filename = f"{recipe_id}_{url_hash}.jpg"
            local_file_path = os.path.join(self._image_cache_path, filename)

            file_exists = await self.hass.async_add_executor_job(
                os.path.exists, local_file_path
            )
            if file_exists:
                return f"/local/norish_images/{filename}"

            headers = self._get_headers()
            session = async_get_clientsession(self.hass)

            async with session.get(
                image_url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.debug(
                        "Norish: could not download image %s (status %s)",
                        image_url, resp.status,
                    )
                    return None
                image_data = await resp.read()

            await self.hass.async_add_executor_job(
                self._write_image, local_file_path, image_data
            )
            _LOGGER.debug("Norish: cached image %s", filename)
            return f"/local/norish_images/{filename}"

        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Norish: failed to cache image %s: %s", image_url, err
            )
            return None

    @staticmethod
    def _write_image(path: str, data: bytes) -> None:
        """Write image bytes to disk (runs in executor)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
