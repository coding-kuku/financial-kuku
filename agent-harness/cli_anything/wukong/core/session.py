"""Session management — persists base_url, auth token, and active account set."""

import json
import os
import fcntl
from pathlib import Path
from typing import Optional

_SESSION_DIR = Path.home() / ".cli-anything-wukong"
_SESSION_FILE = _SESSION_DIR / "session.json"

_DEFAULT_BASE_URL = "http://localhost:44316"


def _locked_save_json(path: Path, data: dict) -> None:
    """Atomically write JSON with exclusive file locking."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        f = open(path, "r+")
    except FileNotFoundError:
        f = open(path, "w")
    with f:
        _locked = False
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            _locked = True
        except (ImportError, OSError):
            pass
        try:
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
        finally:
            if _locked:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def load_session() -> dict:
    """Load session from disk. Returns defaults if file not found."""
    if _SESSION_FILE.exists():
        try:
            with open(_SESSION_FILE) as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "base_url": _DEFAULT_BASE_URL,
        "token": None,
        "account_id": None,
    }


def save_session(session: dict) -> None:
    """Persist session to disk."""
    _locked_save_json(_SESSION_FILE, session)


def get_base_url(session: Optional[dict] = None) -> str:
    """Get the base URL from session or environment."""
    env_url = os.environ.get("WUKONG_URL")
    if env_url:
        return env_url.rstrip("/")
    if session:
        return session.get("base_url", _DEFAULT_BASE_URL).rstrip("/")
    return load_session().get("base_url", _DEFAULT_BASE_URL).rstrip("/")


def get_token(session: Optional[dict] = None) -> Optional[str]:
    """Get the auth token from session."""
    if session:
        return session.get("token")
    return load_session().get("token")


def get_account_id(session: Optional[dict] = None) -> Optional[int]:
    """Get the active account set ID."""
    if session:
        return session.get("account_id")
    return load_session().get("account_id")


def set_token(token: Optional[str]) -> dict:
    """Set auth token and save. Returns updated session."""
    sess = load_session()
    sess["token"] = token
    save_session(sess)
    return sess


def set_account_id(account_id: Optional[int]) -> dict:
    """Set active account set ID and save. Returns updated session."""
    sess = load_session()
    sess["account_id"] = account_id
    save_session(sess)
    return sess


def set_base_url(url: str) -> dict:
    """Set base URL and save. Returns updated session."""
    sess = load_session()
    sess["base_url"] = url.rstrip("/")
    save_session(sess)
    return sess


def clear_session() -> None:
    """Clear authentication from session (logout)."""
    sess = load_session()
    sess["token"] = None
    sess["account_id"] = None
    save_session(sess)
