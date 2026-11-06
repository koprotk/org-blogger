"""Configuration and credential file discovery."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "org-blogger"
SCOPES = ["https://www.googleapis.com/auth/blogger"]


def default_config_dir() -> Path:
    """Return the XDG configuration directory for org-blogger."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    return base / APP_NAME


def resolve_config_dir(explicit: str | Path | None = None) -> Path:
    """Resolve the directory that holds ``client_secret*.json`` and ``token.json``.

    Precedence:
    1. The ``--config-dir`` argument.
    2. The ``ORG_BLOGGER_CONFIG_DIR`` environment variable.
    3. ``./config`` when it exists (keeps the old in-repository workflow working).
    4. ``$XDG_CONFIG_HOME/org-blogger`` (``~/.config/org-blogger`` by default).
    """
    if explicit:
        return Path(explicit).expanduser()

    env_dir = os.environ.get("ORG_BLOGGER_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    local_config = Path.cwd() / "config"
    if local_config.is_dir():
        return local_config

    return default_config_dir()


def find_secret_file(cred_dir: str | Path) -> Path:
    """Find a Google OAuth client secret file inside ``cred_dir``."""
    cred_dir = Path(cred_dir).expanduser()
    matches = sorted(cred_dir.glob("client_secret*.json"))
    if not matches:
        raise FileNotFoundError(
            f"No 'client_secret*.json' file found in '{cred_dir}'. "
            "Download your OAuth credentials from Google Cloud and place them there."
        )
    if len(matches) > 1:
        print(
            f"Warning: found several 'client_secret*.json' files, using '{matches[0]}'."
        )
    return matches[0]
