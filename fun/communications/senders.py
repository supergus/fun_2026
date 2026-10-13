"""Pluggable message senders: SMTP email, Twilio SMS and ntfy push."""

from __future__ import annotations

import base64
import html
import json
import logging
import mimetypes
import smtplib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from typing import Protocol, runtime_checkable

from fun.communications.config import NtfyConfig, SmtpConfig, TwilioConfig

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 15  # seconds


@dataclass(frozen=True)
class Message:
    body: str
    subject: str | None = None
    attachment: Path | None = None


@dataclass(frozen=True)
class DeliveryResult:
    channel: str  # "email", "sms" or "push"
    recipient: str
    ok: bool
    error: str | None = None
    detail: str | None = None  # e.g. provider message id


@runtime_checkable
class Sender(Protocol):
    """Anything that can deliver a :class:`Message` to a list of recipients on one channel."""

    channel: str

    def send(self, message: Message, recipients: list[str]) -> list[DeliveryResult]: ...


def _fail_all(channel: str, recipients: list[str], error: str) -> list[DeliveryResult]:
    logger.warning("%s: %s", channel, error)
    return [DeliveryResult(channel, r, False, error) for r in recipients]


def _http_post(
    url: str, data: bytes, headers: dict[str, str], timeout: float = HTTP_TIMEOUT
) -> tuple[int, bytes]:
    if not url.lower().startswith(("https://", "http://")):
        raise ValueError(f"Refusing non-HTTP URL: {url!r}")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")  # noqa: S310 (scheme checked)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return resp.status, resp.read()


def _http_error_text(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", "replace")[:300]
        except OSError:
            body = ""
        return f"HTTP {exc.code}: {body or exc.reason}"
    return f"{type(exc).__name__}: {exc}"


# ----------------------------------------------------------------------------
# Email
# ----------------------------------------------------------------------------


class SmtpEmailSender:
    channel = "email"

    def __init__(self, config: SmtpConfig | None = None, cc: list[str] | None = None) -> None:
        self.config = config or SmtpConfig.from_env()
        self.cc = list(cc or [])

    def build_message(self, message: Message, to: str) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.config.from_addr or ""
        msg["To"] = to
        if message.subject:
            msg["Subject"] = message.subject
        if self.cc:
            msg["Cc"] = ", ".join(self.cc)

        msg.set_content(message.body)

        body_html = html.escape(message.body).replace("\n", "<br>\n")
        logo = Path(self.config.logo_file) if self.config.logo_file else None
        logo_cid = make_msgid() if logo and logo.is_file() else None
        logo_html = f'<p><img src="cid:{logo_cid[1:-1]}" alt="" /></p>' if logo_cid else ""
        msg.add_alternative(
            f"<html><head></head><body><p>{body_html}</p>{logo_html}</body></html>",
            subtype="html",
        )
        if logo and logo_cid:
            ctype = mimetypes.guess_type(logo.name)[0] or "image/png"
            maintype, subtype = ctype.split("/", 1)
            msg.get_payload()[1].add_related(logo.read_bytes(), maintype, subtype, cid=logo_cid)

        if message.attachment is not None:
            path = Path(message.attachment)
            ctype, encoding = mimetypes.guess_type(path.name)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            msg.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)
        return msg

    def send(self, message: Message, recipients: list[str]) -> list[DeliveryResult]:
        if not recipients:
            return []
        cfg = self.config
        if not cfg.configured:
            return _fail_all(
                self.channel, recipients, "SMTP not configured (set FUN_SMTP_HOST and FUN_SMTP_FROM)"
            )
        try:
            sess = smtplib.SMTP(cfg.host, cfg.port, timeout=HTTP_TIMEOUT)
        except (OSError, smtplib.SMTPException) as exc:
            return _fail_all(self.channel, recipients, f"SMTP connect failed: {exc}")

        results: list[DeliveryResult] = []
        try:
            if cfg.starttls:
                sess.starttls()
            if cfg.user and cfg.password:
                sess.login(cfg.user, cfg.password)
        except (OSError, smtplib.SMTPException) as exc:
            sess.close()
            return _fail_all(self.channel, recipients, f"SMTP login failed: {exc}")

        try:
            for to in recipients:
                try:
                    refused = sess.send_message(self.build_message(message, to))
                except (OSError, smtplib.SMTPException) as exc:
                    logger.warning("email to %s failed: %s", to, exc)
                    results.append(DeliveryResult(self.channel, to, False, str(exc)))
                    continue
                if to in (refused or {}):
                    results.append(DeliveryResult(self.channel, to, False, str(refused[to])))
                else:
                    logger.info("email sent to %s", to)
                    results.append(DeliveryResult(self.channel, to, True))
        finally:
            try:
                sess.quit()
            except (OSError, smtplib.SMTPException):
                sess.close()
        return results


# ----------------------------------------------------------------------------
# SMS via Twilio REST API
# ----------------------------------------------------------------------------


class TwilioSmsSender:
    channel = "sms"
    api_base = "https://api.twilio.com/2010-04-01"
    max_length = 1600  # Twilio's limit for a single (concatenated) message

    def __init__(self, config: TwilioConfig | None = None) -> None:
        self.config = config or TwilioConfig.from_env()

    def format_text(self, message: Message) -> str:
        text = f"{message.subject}\n{message.body}" if message.subject else message.body
        return text[: self.max_length]

    def send(self, message: Message, recipients: list[str]) -> list[DeliveryResult]:
        if not recipients:
            return []
        cfg = self.config
        if not cfg.configured:
            return _fail_all(
                self.channel,
                recipients,
                "Twilio not configured (set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER)",
            )
        url = f"{self.api_base}/Accounts/{urllib.parse.quote(cfg.account_sid)}/Messages.json"
        auth = base64.b64encode(f"{cfg.account_sid}:{cfg.auth_token}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        text = self.format_text(message)
        results: list[DeliveryResult] = []
        for to in recipients:
            data = urllib.parse.urlencode({"To": to, "From": cfg.from_number, "Body": text})
            try:
                _, raw = _http_post(url, data.encode(), headers)
                sid = json.loads(raw or b"{}").get("sid")
            except (urllib.error.URLError, OSError, ValueError) as exc:
                err = _http_error_text(exc)
                logger.warning("sms to %s failed: %s", to, err)
                results.append(DeliveryResult(self.channel, to, False, err))
                continue
            logger.info("sms sent to %s", to)
            results.append(DeliveryResult(self.channel, to, True, detail=sid))
        return results


# ----------------------------------------------------------------------------
# Push via ntfy
# ----------------------------------------------------------------------------


class NtfyPushSender:
    channel = "push"

    def __init__(self, config: NtfyConfig | None = None) -> None:
        self.config = config or NtfyConfig.from_env()

    def send(self, message: Message, recipients: list[str]) -> list[DeliveryResult]:
        server = self.config.server.rstrip("/")
        headers = {"Content-Type": "text/plain; charset=utf-8"}
        if message.subject:
            # HTTP headers must be latin-1; ntfy accepts RFC 2047 encoded titles
            try:
                message.subject.encode("latin-1")
                headers["Title"] = message.subject
            except UnicodeEncodeError:
                encoded = base64.b64encode(message.subject.encode()).decode()
                headers["Title"] = f"=?UTF-8?B?{encoded}?="
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        results: list[DeliveryResult] = []
        for topic in recipients:
            url = f"{server}/{urllib.parse.quote(topic, safe='')}"
            try:
                _http_post(url, message.body.encode("utf-8"), headers)
            except (urllib.error.URLError, OSError) as exc:
                err = _http_error_text(exc)
                logger.warning("push to %s failed: %s", topic, err)
                results.append(DeliveryResult(self.channel, topic, False, err))
                continue
            logger.info("push sent to topic %s", topic)
            results.append(DeliveryResult(self.channel, topic, True))
        return results


@dataclass
class SenderSet:
    email: Sender | None = None
    sms: Sender | None = None
    push: Sender | None = None
    extra: dict[str, Sender] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> SenderSet:
        return cls(email=SmtpEmailSender(), sms=TwilioSmsSender(), push=NtfyPushSender())
