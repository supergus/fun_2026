import pytest

import fun
from fun.communications.communicator import Communicator, phone_home
from fun.communications.recipients import Contacts
from fun.communications.senders import DeliveryResult, SenderSet


class FakeSender:
    def __init__(self, channel, fail=()):
        self.channel = channel
        self.fail = set(fail)
        self.calls = []

    def send(self, message, recipients):
        self.calls.append((message, list(recipients)))
        return [
            DeliveryResult(self.channel, r, r not in self.fail, "boom" if r in self.fail else None)
            for r in recipients
        ]


CONTACTS = Contacts(
    users={
        "chris": {"email": "c@x.com", "mobile": "7345555555", "ntfy_topic": "ct"},
        "joe": {"email": "j@x.com"},
    },
    groups={"admin": ["chris", "joe"]},
)


@pytest.fixture
def fakes():
    return SenderSet(
        email=FakeSender("email"), sms=FakeSender("sms", fail={"+17345555555"}), push=FakeSender("push")
    )


def test_default_channels_email_and_sms(fakes):
    res = phone_home("hi", "admin", "S", contacts=CONTACTS, senders=fakes, quiet=True)
    assert fakes.email.calls[0][1] == ["c@x.com", "j@x.com"]
    assert fakes.sms.calls[0][1] == ["+17345555555"]
    assert fakes.push.calls == []
    assert not res.ok and len(res.succeeded) == 2 and res.failed[0].recipient == "+17345555555"


def test_channel_flags(fakes):
    res = phone_home(
        "hi", "chris", contacts=CONTACTS, senders=fakes, quiet=True, email=False, sms=False, push=True
    )
    assert fakes.email.calls == [] and fakes.sms.calls == []
    assert fakes.push.calls[0][1] == ["ct"]
    assert res.ok


def test_push_default_topic(fakes, monkeypatch):
    monkeypatch.setenv("FUN_NTFY_TOPIC", "fallback")
    phone_home("hi", "joe", contacts=CONTACTS, senders=fakes, quiet=True, email=False, push=True)
    assert fakes.push.calls[0][1] == ["fallback"]


def test_legacy_kwargs(fakes):
    with pytest.warns(DeprecationWarning):
        phone_home("hi", "chris", contacts=CONTACTS, senders=fakes, quiet=True, disable_sms=True)
    assert fakes.sms.calls == [] and fakes.email.calls


def test_unknown_kwarg_rejected(fakes):
    with pytest.raises(TypeError):
        phone_home("hi", "chris", contacts=CONTACTS, senders=fakes, use_email=True)


def test_missing_attachment(fakes, tmp_path):
    with pytest.raises(FileNotFoundError):
        phone_home("hi", "chris", contacts=CONTACTS, senders=fakes, attachment=tmp_path / "nope")


def test_no_recipients(fakes):
    res = Communicator(CONTACTS, fakes, quiet=True).send_msg("hi", "nobody")
    assert not res.ok and res.unresolved == ["nobody"] and res.deliveries == []


def test_bad_flag_type(fakes):
    with pytest.raises(TypeError):
        Communicator(CONTACTS, fakes).send_msg("hi", "chris", email="yes")


def test_public_api():
    assert fun.et.phone_home is phone_home
    assert fun.__version__ == "0.2.0"
    assert callable(fun.fancy_print)
