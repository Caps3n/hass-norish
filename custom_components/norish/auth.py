"""Authentication manager for the Norish API.

Handles email/password login via better-auth, session management,
and automatic token refresh before expiry.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Refresh session 1 hour before it actually expires
SESSION_REFRESH_BUFFER_SECONDS = 3600


class NorishAuthError(Exception):
    """Raised when authentication fails (wrong credentials)."""


class NorishConnectionError(Exception):
    """Raised when the server is unreachable."""


class NorishAuthManager:
    """Manage Norish API authentication via better-auth sessions.

    Lifecycle:
      1. login(email, password) -> obtains session cookie + token
      2. ensure_valid_session() -> called before each API request;
         refreshes the session proactively if it is about to expire,
         or re-logs in if the session is dead.
      3. get_headers() -> returns headers with the current session cookie.
    """

    def __init__(self, hass: HomeAssistant, base_url: str) -> None:
        """Initialize the auth manager."""
        self._hass = hass
        self._base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

        # Credentials (stored for auto re-login)
        self._email: str = ""
        self._password: str = ""

        # Session state
        self._session_token: str | None = None
        self._session_expires_at: datetime | None = None
        self._cookie_jar: aiohttp.CookieJar | None = None
        self._session_cookie: str | None = None
        self._is_logged_in: bool = False

    @property
    def is_logged_in(self) -> bool:
        """Return whether we have an active session."""
        return self._is_logged_in and self._session_cookie is not None

    @property
    def base_url(self) -> str:
        """Return the base URL."""
        return self._base_url

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Log in with email/password via better-auth.

        Returns the session data on success.
        Raises NorishAuthError on invalid credentials.
        Raises NorishConnectionError on network issues.
        """
        self._email = email
        self._password = password

        session = async_get_clientsession(self._hass)
        url = f"{self._base_url}/api/auth/sign-in/email"

        try:
            async with session.post(
                url,
                json={"email": email, "password": password},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                body = await resp.json()

                if resp.status == 200 and "token" in body:
                    # better-auth returns token directly
                    self._apply_session(body)
                    return body

                if resp.status == 200 and "session" in body:
                    # Some better-auth versions nest under "session"
                    self._apply_session(body)
                    return body

                # Extract set-cookie header for session cookie
                cookies = resp.headers.getall("Set-Cookie", [])
                session_cookie = self._extract_session_cookie(cookies)

                if resp.status == 200 and session_cookie:
                    self._session_cookie = session_cookie
                    self._is_logged_in = True
                    # Fetch full session info
                    return await self._fetch_session_info()

                # Auth failed
                error_msg = body.get("message", "Unknown error")
                error_code = body.get("code", "")
                _LOGGER.error(
                    "Norish login failed: %s (%s)", error_msg, error_code
                )
                raise NorishAuthError(
                    f"Login failed: {error_msg}"
                )

        except aiohttp.ClientError as err:
            _LOGGER.error("Norish: connection error during login: %s", err)
            raise NorishConnectionError(
                f"Cannot connect to {self._base_url}: {err}"
            ) from err

    def _apply_session(self, data: dict[str, Any]) -> None:
        """Extract session info from login response."""
        session_data = data.get("session", data)
        self._session_token = session_data.get("token")
        expires_str = session_data.get("expiresAt")
        if expires_str:
            try:
                self._session_expires_at = datetime.fromisoformat(
                    expires_str.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                self._session_expires_at = None
        self._is_logged_in = True
        _LOGGER.info(
            "Norish: logged in successfully (expires: %s)",
            self._session_expires_at,
        )

    @staticmethod
    def _extract_session_cookie(cookies: list[str]) -> str | None:
        """Extract the session cookie from Set-Cookie headers."""
        for cookie in cookies:
            # better-auth typically uses "better-auth.session_token" or similar
            if "session" in cookie.lower():
                return cookie.split(";")[0]
        return None

    async def _fetch_session_info(self) -> dict[str, Any]:
        """Fetch current session info from /api/auth/get-session."""
        session = async_get_clientsession(self._hass)
        headers = self.get_headers()

        try:
            async with session.get(
                f"{self._base_url}/api/auth/get-session",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and "session" in data:
                        self._apply_session(data)
                    return data
                return {}
        except (aiohttp.ClientError, Exception) as err:  # noqa: BLE001
            _LOGGER.warning("Norish: failed to fetch session info: %s", err)
            return {}

    async def ensure_valid_session(self) -> None:
        """Ensure the session is valid; refresh or re-login if needed.

        Call this before every API request.
        Raises NorishAuthError if re-login fails.
        """
        if not self._is_logged_in:
            if self._email and self._password:
                await self.login(self._email, self._password)
                return
            raise NorishAuthError("Not logged in and no credentials stored")

        # Check if session is about to expire
        if self._session_expires_at:
            now = datetime.now(timezone.utc)
            remaining = (self._session_expires_at - now).total_seconds()

            if remaining < SESSION_REFRESH_BUFFER_SECONDS:
                _LOGGER.info(
                    "Norish: session expires in %d seconds, refreshing...",
                    int(remaining),
                )
                try:
                    await self._refresh_session()
                except Exception:  # noqa: BLE001
                    _LOGGER.warning(
                        "Norish: session refresh failed, attempting re-login"
                    )
                    await self.login(self._email, self._password)

    async def _refresh_session(self) -> None:
        """Refresh the current session by calling get-session."""
        data = await self._fetch_session_info()
        if not data or "session" not in data:
            raise NorishAuthError("Session refresh returned no data")

    def get_headers(self) -> dict[str, str]:
        """Return headers for authenticated API requests."""
        headers: dict[str, str] = {
            "User-Agent": "HomeAssistant/Norish",
            "Accept": "application/json",
        }

        if self._session_cookie:
            headers["Cookie"] = self._session_cookie
        if self._session_token:
            headers["Authorization"] = f"Bearer {self._session_token}"

        return headers

    async def validate_credentials(self, email: str, password: str) -> bool:
        """Validate email/password by attempting login + API call.

        Used by config_flow during setup/reconfiguration.
        Returns True on success.
        Raises NorishAuthError or NorishConnectionError on failure.
        """
        await self.login(email, password)

        # Verify the session works by calling a real endpoint
        session = async_get_clientsession(self._hass)
        headers = self.get_headers()

        try:
            async with session.get(
                f"{self._base_url}/api/trpc/groceries.list"
                "?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    self._is_logged_in = False
                    raise NorishAuthError(
                        "Session obtained but API returned 401"
                    )
                if resp.status >= 400:
                    raise NorishConnectionError(
                        f"API returned status {resp.status}"
                    )
        except aiohttp.ClientError as err:
            raise NorishConnectionError(str(err)) from err

        _LOGGER.info("Norish: credentials validated successfully")
        return True

    def logout(self) -> None:
        """Clear session state."""
        self._session_token = None
        self._session_expires_at = None
        self._session_cookie = None
        self._is_logged_in = False
        _LOGGER.info("Norish: logged out")
