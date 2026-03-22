"""Authentication operations — login, logout, whoami."""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def login(client: WukongClient, username: str, password: str) -> str:
    """Login with username and password. Returns auth token.

    Raises:
        WukongAPIError: Invalid credentials
        WukongConnectionError: Server unreachable
    """
    token = client.post(
        "/login",
        {"username": username, "password": password},
        auth=False,
    )
    if not isinstance(token, str):
        raise ValueError(f"Unexpected login response: {token!r}")
    return token


def logout(client: WukongClient) -> None:
    """Invalidate the current session token on the server."""
    client.post("/adminUser/logout")


def whoami(client: WukongClient) -> dict:
    """Return current user info dict.

    Returns:
        {"userId": ..., "username": "...", "nickname": "...", "isAdmin": bool}
    """
    result = client.post("/adminUser/queryLoginUser")
    return result or {}


def query_user_list(client: WukongClient) -> list:
    """Return list of users (local implementation returns current user)."""
    result = client.post("/adminUser/queryUserList")
    if isinstance(result, dict):
        return result.get("list", [])
    return result or []
