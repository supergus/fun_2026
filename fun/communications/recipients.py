"""Recipient parsing: contacts directory, email validation and E.164 phone normalization."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from email.utils import parseaddr
from pathlib import Path
from typing import Any

DEFAULT_CONTACTS_FILE = Path(__file__).parent / "contact_list.json"

# Permissive: local part may contain dots, plus tags, etc.; domain may have subdomains.
_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}$"
)


def normalize_email(value: Any) -> str | None:
    """Return a bare, valid email address or None."""
    if not isinstance(value, str) or "@" not in value:
        return None
    _, addr = parseaddr(value.strip())
    if not addr or ".." in addr or addr.startswith(".") or ".@" in addr:
        return None
    return addr if _EMAIL_RE.match(addr) else None


def normalize_phone(value: Any, default_country_code: str = "1") -> str | None:
    """Normalize a phone number to E.164 (``+15551234567``) or return None.

    * Strings starting with ``+`` are kept as international numbers (8-15 digits).
    * 10 digits are treated as US/Canada and get ``+1``.
    * 11 digits starting with ``1`` become ``+1...``.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if "@" in raw:
        return None
    if re.search(r"[A-Za-z]", raw):
        return None
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        return f"+{digits}" if 8 <= len(digits) <= 15 else None
    if raw.startswith("00") and 10 <= len(digits) - 2 <= 15:
        return f"+{digits[2:]}"
    if len(digits) == 10:
        return f"+{default_country_code}{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None


@dataclass
class Recipients:
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    ntfy_topics: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    def _add(self, bucket: list[str], value: str | None) -> None:
        if value and value not in bucket:
            bucket.append(value)

    @property
    def empty(self) -> bool:
        return not (self.emails or self.phones or self.ntfy_topics)


@dataclass
class Contacts:
    users: dict[str, dict[str, Any]] = field(default_factory=dict)
    groups: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> Contacts:
        path = Path(path) if path else DEFAULT_CONTACTS_FILE
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(users=data.get("users", {}), groups=data.get("groups", {}))

    def resolve(self, who: Any) -> Recipients:
        """Resolve ``who`` (user, group, email, phone, or a list of these).

        Lookup order per item: user name, group name, phone number, email address.
        """
        if isinstance(who, (str, int)) and not isinstance(who, bool):
            items: Iterable[Any] = [who]
        elif isinstance(who, (list, tuple, set)):
            items = who
        else:
            raise TypeError(f"'who' must be a string, int or list, not {type(who).__name__}")

        out = Recipients()
        for w in items:
            if isinstance(w, str) and w in self.users:
                self._add_user(out, w)
            elif isinstance(w, str) and w in self.groups:
                for u in self.groups[w]:
                    if u in self.users:
                        self._add_user(out, u)
                    else:
                        out.unresolved.append(f"{w}:{u}")
            elif (phone := normalize_phone(w)) is not None:
                out._add(out.phones, phone)
            elif (addr := normalize_email(w)) is not None:
                out._add(out.emails, addr)
            else:
                out.unresolved.append(str(w))
        return out

    def _add_user(self, out: Recipients, name: str) -> None:
        user = self.users[name]
        out._add(out.emails, normalize_email(user.get("email")))
        out._add(out.phones, normalize_phone(user.get("mobile")))
        topic = user.get("ntfy_topic")
        if isinstance(topic, str) and topic.strip():
            out._add(out.ntfy_topics, topic.strip())
