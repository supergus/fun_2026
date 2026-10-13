"""Configuration loaded from environment variables (and an optional ``.env`` file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_NTFY_SERVER = "https://ntfy.sh"


def load_dotenv_if_available(path: str | Path | None = None) -> bool:
    """Load a ``.env`` file if ``python-dotenv`` is installed. Returns True if it was loaded."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False
    return bool(load_dotenv(dotenv_path=path, override=False))


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SmtpConfig:
    host: str | None = None
    port: int = 587
    user: str | None = None
    password: str | None = None
    from_addr: str | None = None
    starttls: bool = True
    logo_file: str | None = None  # Optional PNG embedded in the HTML signature

    @classmethod
    def from_env(cls) -> SmtpConfig:
        port = _env("FUN_SMTP_PORT")
        user = _env("FUN_SMTP_USER")
        return cls(
            host=_env("FUN_SMTP_HOST"),
            port=int(port) if port else 587,
            user=user,
            password=_env("FUN_SMTP_PASSWORD"),
            from_addr=_env("FUN_SMTP_FROM", user),
            starttls=_env_bool("FUN_SMTP_STARTTLS", True),
            logo_file=_env("FUN_EMAIL_LOGO_FILE"),
        )

    @property
    def configured(self) -> bool:
        return bool(self.host and self.from_addr)


@dataclass(frozen=True)
class TwilioConfig:
    account_sid: str | None = None
    auth_token: str | None = None
    from_number: str | None = None

    @classmethod
    def from_env(cls) -> TwilioConfig:
        return cls(
            account_sid=_env("TWILIO_ACCOUNT_SID"),
            auth_token=_env("TWILIO_AUTH_TOKEN"),
            from_number=_env("TWILIO_FROM_NUMBER"),
        )

    @property
    def configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)


@dataclass(frozen=True)
class NtfyConfig:
    server: str = DEFAULT_NTFY_SERVER
    topic: str | None = None  # Default topic when a recipient has none of their own
    token: str | None = None

    @classmethod
    def from_env(cls) -> NtfyConfig:
        return cls(
            server=_env("FUN_NTFY_SERVER", DEFAULT_NTFY_SERVER) or DEFAULT_NTFY_SERVER,
            topic=_env("FUN_NTFY_TOPIC"),
            token=_env("FUN_NTFY_TOKEN"),
        )
