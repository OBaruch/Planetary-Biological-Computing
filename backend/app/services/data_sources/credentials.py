from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


def _mask(value: str) -> str:
    """Mask a secret, revealing only the last 4 characters."""
    value = value or ""
    if len(value) <= 4:
        return "•" * len(value)
    return "•" * (len(value) - 4) + value[-4:]


class CredentialStore:
    """Per-user API credentials persisted to a local gitignored JSON file.

    This is a local-MVP store: the person running their own backend pastes
    their keys via the Settings UI and they live in ``backend/data/credentials.json``.
    Secrets never leave the backend (the API only ever exposes masked values).

    A read-only fallback to environment variables is supported for users who
    prefer ``.env``: ``GAIA_KEY_<SOURCE>_<FIELD>`` (e.g. ``GAIA_KEY_FIRMS_MAP_KEY``).
    File values take precedence over environment values.
    """

    VERSION = 1

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._data: dict = self._load()

    # -- persistence -------------------------------------------------------
    def _load(self) -> dict:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("sources"), dict):
                return raw
        except FileNotFoundError:
            pass
        except (ValueError, OSError) as exc:
            logger.warning("[GAIA] Could not read credentials file: %s", exc)
        return {"version": self.VERSION, "sources": {}}

    def _flush(self) -> None:
        """Atomic write (tmp + replace) so a crash never corrupts the file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def _entry(self, source_id: str) -> dict:
        return self._data["sources"].get(source_id, {})

    @staticmethod
    def _env_secret(source_id: str, field: str) -> str | None:
        name = f"GAIA_KEY_{source_id}_{field}".upper()
        value = os.getenv(name)
        return value.strip() if value and value.strip() else None

    # -- reads -------------------------------------------------------------
    def get_secrets(self, source_id: str, fields: list[str] | None = None) -> dict[str, str]:
        """Resolve secrets for a source: file values, then env fallback."""
        with self._lock:
            stored = dict(self._entry(source_id).get("secrets", {}))
        if fields:
            for field in fields:
                if not stored.get(field):
                    env_value = self._env_secret(source_id, field)
                    if env_value:
                        stored[field] = env_value
        return {k: v for k, v in stored.items() if v}

    def is_configured(self, source_id: str, required_fields: list[str]) -> bool:
        """True when every required credential field has a value."""
        if not required_fields:
            return True
        secrets = self.get_secrets(source_id, required_fields)
        return all(secrets.get(field) for field in required_fields)

    def enabled_flag(self, source_id: str) -> bool | None:
        """The user's explicit enable/disable choice, or None if never set."""
        with self._lock:
            entry = self._entry(source_id)
        return entry.get("enabled")

    def masked(self, source_id: str, fields: list[str]) -> dict[str, str]:
        """Masked view of configured secrets, safe to return over the API."""
        secrets = self.get_secrets(source_id, fields)
        return {field: _mask(secrets[field]) for field in fields if secrets.get(field)}

    # -- writes ------------------------------------------------------------
    def set(self, source_id: str, secrets: dict[str, str], enabled: bool = True) -> None:
        with self._lock:
            entry = dict(self._entry(source_id))
            merged = dict(entry.get("secrets", {}))
            for key, value in secrets.items():
                value = (value or "").strip()
                if value:
                    merged[key] = value
                else:
                    merged.pop(key, None)
            entry["secrets"] = merged
            entry["enabled"] = enabled
            self._data["sources"][source_id] = entry
            self._flush()

    def set_enabled(self, source_id: str, enabled: bool) -> None:
        with self._lock:
            entry = dict(self._entry(source_id))
            entry["enabled"] = enabled
            entry.setdefault("secrets", {})
            self._data["sources"][source_id] = entry
            self._flush()

    def delete(self, source_id: str) -> None:
        with self._lock:
            if source_id in self._data["sources"]:
                del self._data["sources"][source_id]
                self._flush()
