"""Storage for the Materials Project API key.

The key is kept in the operating system's credential store when the optional ``keyring``
package is installed, and otherwise in the application's settings file. The ``MP_API_KEY``
environment variable is used when nothing is stored.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QSettings

SERVICE = "pourbase"
ACCOUNT = "materials-project-api-key"
SETTINGS_KEY = "materials_project/api_key"


def _keyring():
    try:
        import keyring
        from keyring.errors import KeyringError  # noqa: F401

        backend = keyring.get_keyring()
        if type(backend).__name__ in ("FailKeyring", "NullKeyring"):
            return None
        return keyring
    except Exception:  # keyring missing or without a usable backend
        return None


def storage_description() -> str:
    if _keyring() is not None:
        return "the system keyring"
    return f"the pourbase settings file ({QSettings('pourbase', 'pourbase').fileName()})"


def load_key(settings: QSettings) -> tuple[str, str]:
    """Return ``(key, source)``; source is "keyring", "settings", "environment" or ""."""
    backend = _keyring()
    if backend is not None:
        try:
            key = backend.get_password(SERVICE, ACCOUNT)
        except Exception:
            key = None
        if key:
            return key, "keyring"
    key = str(settings.value(SETTINGS_KEY, "") or "")
    if key:
        return key, "settings"
    key = os.environ.get("MP_API_KEY", "").strip()
    return (key, "environment") if key else ("", "")


def save_key(settings: QSettings, key: str) -> str:
    """Store the key and return where it went."""
    backend = _keyring()
    if backend is not None:
        try:
            backend.set_password(SERVICE, ACCOUNT, key)
            settings.remove(SETTINGS_KEY)
            return "keyring"
        except Exception:
            pass
    settings.setValue(SETTINGS_KEY, key)
    return "settings"


def clear_key(settings: QSettings) -> None:
    backend = _keyring()
    if backend is not None:
        try:
            backend.delete_password(SERVICE, ACCOUNT)
        except Exception:
            pass
    settings.remove(SETTINGS_KEY)
