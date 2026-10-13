import io
import json
import smtplib
import urllib.error
from email import message_from_bytes, policy
from unittest import mock

from fun.communications import senders
from fun.communications.config import NtfyConfig, SmtpConfig, TwilioConfig
from fun.communications.senders import Message, NtfyPushSender, SmtpEmailSender, TwilioSmsSender

SMTP_CFG = SmtpConfig(host="smtp.test", port=587, user="u", password="p", from_addr="me@test.com")


def test_email_build_escapes_html_and_attaches_with_filename(tmp_path):
    f = tmp_path / "report.csv"
    f.write_text("a,b\n")
    msg = SmtpEmailSender(SMTP_CFG).build_message(Message("<b>hi</b> & bye\nline2", None, f), "to@test.com")
    assert "Subject" not in msg
    parsed = message_from_bytes(bytes(msg), policy=policy.default)
    html = parsed.get_body(("html",)).get_content()
    assert "&lt;b&gt;hi&lt;/b&gt; &amp; bye<br>" in html
    assert "liveline" not in html.lower()
    atts = list(parsed.iter_attachments())
    assert [a.get_filename() for a in atts] == ["report.csv"]
    assert atts[0].get_content_type() == "text/csv"


def test_email_optional_logo(tmp_path):
    logo = tmp_path / "logo.png"
    logo.write_bytes(b"\x89PNG fake")
    cfg = SmtpConfig(host="h", from_addr="me@test.com", logo_file=str(logo))
    raw = bytes(SmtpEmailSender(cfg).build_message(Message("hi", "S"), "to@test.com"))
    assert b"cid:" in raw and b"image/png" in raw


def test_email_send_per_recipient_results():
    with mock.patch.object(senders.smtplib, "SMTP") as smtp:
        sess = smtp.return_value
        sess.send_message.side_effect = [{}, smtplib.SMTPRecipientsRefused({"b@t.com": (550, b"no")})]
        res = SmtpEmailSender(SMTP_CFG).send(Message("hi", "Subj"), ["a@t.com", "b@t.com"])
    smtp.assert_called_once_with("smtp.test", 587, timeout=senders.HTTP_TIMEOUT)
    sess.starttls.assert_called_once()
    sess.login.assert_called_once_with("u", "p")
    assert [r.ok for r in res] == [True, False]
    sent = sess.send_message.call_args_list[0].args[0]
    assert sent["Subject"] == "Subj" and sent["To"] == "a@t.com"


def test_email_login_failure_reported():
    with mock.patch.object(senders.smtplib, "SMTP") as smtp:
        smtp.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad")
        res = SmtpEmailSender(SMTP_CFG).send(Message("hi"), ["a@t.com"])
    assert not res[0].ok and "login failed" in res[0].error


def test_email_not_configured():
    res = SmtpEmailSender(SmtpConfig()).send(Message("hi"), ["a@t.com"])
    assert not res[0].ok and "not configured" in res[0].error


def test_twilio_posts_form():
    cfg = TwilioConfig("ACabc", "tok", "+15550001111")
    with mock.patch.object(
        senders, "_http_post", return_value=(201, json.dumps({"sid": "SM1"}).encode())
    ) as post:
        res = TwilioSmsSender(cfg).send(Message("body", "Title"), ["+17345555555"])
    url, data, headers = post.call_args.args
    assert url == "https://api.twilio.com/2010-04-01/Accounts/ACabc/Messages.json"
    assert b"To=%2B17345555555" in data and b"Body=Title%0Abody" in data
    assert headers["Authorization"].startswith("Basic ")
    assert res[0].ok and res[0].detail == "SM1"


def test_twilio_http_error():
    cfg = TwilioConfig("ACabc", "tok", "+15550001111")
    err = urllib.error.HTTPError("u", 400, "Bad", {}, io.BytesIO(b'{"message":"invalid To"}'))
    with mock.patch.object(senders, "_http_post", side_effect=err):
        res = TwilioSmsSender(cfg).send(Message("b"), ["+1", "+2"])
    assert [r.ok for r in res] == [False, False]
    assert "HTTP 400" in res[0].error and "invalid To" in res[0].error


def test_twilio_not_configured():
    assert not TwilioSmsSender(TwilioConfig()).send(Message("b"), ["+1"])[0].ok


def test_ntfy_post():
    cfg = NtfyConfig(server="https://ntfy.example/", token="tk_1")
    with mock.patch.object(senders, "_http_post", return_value=(200, b"{}")) as post:
        res = NtfyPushSender(cfg).send(Message("héllo", "Tïtle ✓"), ["my topic"])
    url, data, headers = post.call_args.args
    assert url == "https://ntfy.example/my%20topic"
    assert data == "héllo".encode()
    assert headers["Authorization"] == "Bearer tk_1"
    assert headers["Title"].startswith("=?UTF-8?B?")
    assert res[0].ok


def test_ntfy_network_error():
    with mock.patch.object(senders, "_http_post", side_effect=urllib.error.URLError("down")):
        res = NtfyPushSender(NtfyConfig()).send(Message("x"), ["t"])
    assert not res[0].ok


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("FUN_SMTP_HOST", "h")
    monkeypatch.setenv("FUN_SMTP_PORT", "2525")
    monkeypatch.setenv("FUN_SMTP_USER", "me@x.com")
    cfg = SmtpConfig.from_env()
    assert cfg.port == 2525 and cfg.from_addr == "me@x.com" and cfg.configured
    assert NtfyConfig.from_env().server == "https://ntfy.sh"
