"""ET Phone Home! Send messages via email, SMS (Twilio) and push (ntfy).

Credentials come from environment variables (see ``.env.example``). If
``python-dotenv`` is installed, a ``.env`` file in the working directory is loaded.
"""

from __future__ import annotations

__author__ = "Christopher Couch"
__license__ = "MIT"

import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fun.communications.config import NtfyConfig, load_dotenv_if_available
from fun.communications.recipients import Contacts, Recipients
from fun.communications.senders import (
    DeliveryResult,
    Message,
    NtfyPushSender,
    Sender,
    SenderSet,
    SmtpEmailSender,
    TwilioSmsSender,
)
from fun.printing.formatted_console_print import fancy_print

__all__ = [
    "Communicator",
    "DeliveryResult",
    "Message",
    "NtfyPushSender",
    "SendResult",
    "Sender",
    "SenderSet",
    "SmtpEmailSender",
    "TwilioSmsSender",
    "phone_home",
]

logger = logging.getLogger(__name__)

COMMUNICATOR_MSG_COLOR = "light_cerulean"
COMMUNICATOR_WARN_COLOR = "yellow"


@dataclass
class SendResult:
    """Outcome of a send: one :class:`DeliveryResult` per recipient per channel."""

    deliveries: list[DeliveryResult] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if at least one delivery was attempted and all of them succeeded."""
        return bool(self.deliveries) and all(d.ok for d in self.deliveries)

    @property
    def succeeded(self) -> list[DeliveryResult]:
        return [d for d in self.deliveries if d.ok]

    @property
    def failed(self) -> list[DeliveryResult]:
        return [d for d in self.deliveries if not d.ok]

    def __bool__(self) -> bool:
        return self.ok


class Communicator:
    """Resolves recipients from the contacts directory and dispatches to senders."""

    def __init__(
        self,
        contacts: Contacts | str | Path | None = None,
        senders: SenderSet | None = None,
        default_ntfy_topic: str | None = None,
        quiet: bool = False,
    ) -> None:
        load_dotenv_if_available()
        self.contacts = contacts if isinstance(contacts, Contacts) else Contacts.load(contacts)
        self.senders = senders or SenderSet.from_env()
        self.default_ntfy_topic = default_ntfy_topic or NtfyConfig.from_env().topic
        self.quiet = quiet

    def __repr__(self) -> str:
        return "Communicator(email, sms, push)"

    def _say(self, text: str, color: str = COMMUNICATOR_MSG_COLOR) -> None:
        if not self.quiet:
            fancy_print(text, fg=color)

    def send_msg(
        self,
        body: str,
        who: Any,
        subject: str | None = None,
        *,
        email: bool = True,
        sms: bool = True,
        push: bool = False,
        attachment: str | Path | None = None,
    ) -> SendResult:
        """Send a message. See :func:`phone_home` for argument details."""
        for name, flag in (("email", email), ("sms", sms), ("push", push)):
            if not isinstance(flag, bool):
                raise TypeError(f"'{name}' must be bool, not {type(flag).__name__}")
        if attachment is not None:
            attachment = Path(attachment)
            if not attachment.is_file():
                raise FileNotFoundError(f"Attachment not found: {attachment}")

        recipients: Recipients = self.contacts.resolve(who)
        result = SendResult(unresolved=list(recipients.unresolved))
        for item in recipients.unresolved:
            logger.warning("could not resolve recipient %r", item)
            self._say(f"COMMUNICATOR WARNING: Unrecognized recipient {item!r}", COMMUNICATOR_WARN_COLOR)

        topics = list(recipients.ntfy_topics)
        if push and not topics and self.default_ntfy_topic:
            topics = [self.default_ntfy_topic]

        message = Message(body=str(body), subject=subject or None, attachment=attachment)
        plan: list[tuple[bool, Sender | None, list[str], str]] = [
            (email, self.senders.email, recipients.emails, "email"),
            (sms, self.senders.sms, recipients.phones, "sms"),
            (push, self.senders.push, topics, "push"),
        ]
        for enabled, sender, targets, channel in plan:
            if not enabled or not targets:
                continue
            if sender is None:
                result.deliveries += [
                    DeliveryResult(channel, t, False, f"no {channel} sender configured") for t in targets
                ]
                continue
            self._say(f"COMMUNICATOR MESSAGE: Sending {channel} to {', '.join(targets)}")
            result.deliveries += sender.send(message, targets)

        if not result.deliveries:
            self._say(
                "COMMUNICATOR WARNING: No recipients for the selected channels.", COMMUNICATOR_WARN_COLOR
            )
        for d in result.failed:
            self._say(
                f"COMMUNICATOR WARNING: {d.channel} to {d.recipient} failed: {d.error}",
                COMMUNICATOR_WARN_COLOR,
            )
        return result


def phone_home(
    body: str,
    who: Any,
    subject: str | None = None,
    *,
    email: bool = True,
    sms: bool = True,
    push: bool = False,
    attachment: str | Path | None = None,
    contacts: Contacts | str | Path | None = None,
    senders: SenderSet | None = None,
    quiet: bool = False,
    **legacy: Any,
) -> SendResult:
    """Send email, SMS and/or push messages.

    ``who`` can be a user name or group name from ``contact_list.json``, an email
    address, a phone number (any format; 10 digits are treated as US +1, or use a
    leading ``+`` for international), or a list mixing any of these.

    Arguments:
        body: Message text. It is HTML-escaped in the HTML part of emails.
        who: Recipient(s); see above.
        subject: Optional subject (email subject, SMS first line, push title).

    Keyword Arguments:
        email: Send email to any resolved addresses. Default True.
        sms: Send SMS (Twilio) to any resolved phone numbers. Default True.
        push: Send ntfy push to users' ``ntfy_topic`` (or ``FUN_NTFY_TOPIC``). Default False.
        attachment: Optional path to a file attached to emails.
        contacts: Optional alternate contacts JSON path or :class:`Contacts` object.
        senders: Optional :class:`SenderSet` to override the default senders.
        quiet: Suppress colored console output (logging still applies).

    The legacy keywords ``disable_email`` / ``disable_sms`` are still accepted
    (with a ``DeprecationWarning``).

    Returns:
        A :class:`SendResult` with one entry per recipient per channel.
    """
    if "disable_email" in legacy:
        warnings.warn("disable_email is deprecated; use email=False", DeprecationWarning, stacklevel=2)
        email = not legacy.pop("disable_email")
    if "disable_sms" in legacy:
        warnings.warn("disable_sms is deprecated; use sms=False", DeprecationWarning, stacklevel=2)
        sms = not legacy.pop("disable_sms")
    if legacy:
        raise TypeError(f"phone_home() got unexpected keyword argument(s): {', '.join(legacy)}")

    c = Communicator(contacts=contacts, senders=senders, quiet=quiet)
    return c.send_msg(body, who, subject, email=email, sms=sms, push=push, attachment=attachment)
