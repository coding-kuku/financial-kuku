"""HTTP client for the Wukong Accounting REST API.

The Wukong server is the required dependency — this CLI is a command-line
interface TO the server, not a reimplementation of it.

If the server is not reachable, commands raise WukongConnectionError with
clear instructions.
"""

import json
from typing import Any, Optional

import requests
from requests.exceptions import ConnectionError, Timeout

_DEFAULT_TIMEOUT = 30  # seconds


class WukongError(Exception):
    """Base error for Wukong API failures."""


class WukongConnectionError(WukongError):
    """Server unreachable."""

    def __init__(self, base_url: str):
        super().__init__(
            f"Cannot connect to Wukong server at {base_url}\n"
            f"  Make sure the server is running:\n"
            f"    java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar\n"
            f"  Or set a different URL:\n"
            f"    cli-anything-wukong --url http://HOST:PORT <command>"
        )


class WukongAuthError(WukongError):
    """Not authenticated or token expired."""

    def __init__(self):
        super().__init__(
            "Not authenticated or session expired.\n"
            "  Login first: cli-anything-wukong auth login -u admin -p 123456"
        )


class WukongAPIError(WukongError):
    """API returned a non-200 business code."""

    def __init__(self, code: int, msg: str):
        super().__init__(f"API error {code}: {msg}")
        self.code = code
        self.msg = msg


class WukongClient:
    """Thin HTTP client for the Wukong Accounting API.

    Usage:
        client = WukongClient(base_url="http://localhost:44316", token="abc123")
        data = client.post("/login", {"username": "admin", "password": "123456"}, auth=False)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:44316",
        token: Optional[str] = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self, auth: bool = True) -> dict:
        headers = {"Content-Type": "application/json"}
        if auth and self.token:
            headers["AUTH-TOKEN"] = self.token
        return headers

    def post(
        self,
        path: str,
        body: Optional[Any] = None,
        params: Optional[dict] = None,
        auth: bool = True,
        raw_response: bool = False,
    ) -> Any:
        """Make a POST request and return the `data` field of the response.

        Args:
            path: API path (e.g. "/login")
            body: JSON body (dict or list)
            params: Query parameters
            auth: Whether to include AUTH-TOKEN header
            raw_response: If True, return the full response dict instead of data

        Returns:
            Response data field, or full response if raw_response=True

        Raises:
            WukongConnectionError: Cannot reach server
            WukongAuthError: 401 or token missing
            WukongAPIError: Non-200 business code
        """
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(
                url,
                json=body,
                params=params,
                headers=self._headers(auth=auth),
                timeout=self.timeout,
            )
        except (ConnectionError, Timeout, OSError):
            raise WukongConnectionError(self.base_url)

        if resp.status_code == 401:
            raise WukongAuthError()

        try:
            data = resp.json()
        except ValueError:
            raise WukongAPIError(resp.status_code, f"Non-JSON response: {resp.text[:200]}")

        if raw_response:
            return data

        code = data.get("code", 200)
        if code not in (200, 0):
            if code in (401, 302):
                raise WukongAuthError()
            raise WukongAPIError(code, data.get("msg", "Unknown error"))

        return data.get("data")

    def health_check(self) -> bool:
        """Check if the server is reachable. Returns True if up."""
        try:
            requests.get(
                f"{self.base_url}/doc.html",
                timeout=5,
                allow_redirects=False,
            )
            return True
        except Exception:
            return False


def make_client(base_url: str, token: Optional[str] = None) -> WukongClient:
    """Create a WukongClient. Verifies server is reachable."""
    client = WukongClient(base_url=base_url, token=token)
    return client
