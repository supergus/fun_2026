import pytest

from fun.communications.recipients import Contacts, normalize_email, normalize_phone


@pytest.mark.parametrize(
    "addr",
    [
        "first.last@sub.domain.com",
        "a+tag@example.co.uk",
        "x@y.io",
        "Name <bob@example.org>",
        "a_b-c@d-e.museum",
    ],
)
def test_valid_emails(addr):
    assert normalize_email(addr) is not None


@pytest.mark.parametrize("addr", ["nope", "a@b", "a..b@c.com", "@c.com", "a@.com", None, 5, ".a@b.com"])
def test_invalid_emails(addr):
    assert normalize_email(addr) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("734.555.5555", "+17345555555"),
        (7345555555, "+17345555555"),
        ("1-734-555-5555", "+17345555555"),
        ("(734) 555-5555", "+17345555555"),
        ("+44 20 7946 0958", "+442079460958"),
        ("0044 20 7946 0958", "+442079460958"),
        ("12345", None),
        ("a@b.com", None),
        ("joe", None),
        (True, None),
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def contacts():
    return Contacts(
        users={
            "chris": {"email": "chris@x.com", "mobile": "734.555.5555", "ntfy_topic": "chris-t"},
            "joe": {"email": "joe@x.com", "mobile": "248-555-5555"},
        },
        groups={"admin": ["chris", "joe", "ghost"], "solo": ["chris"]},
    )


def test_resolve_mixed_dedup():
    r = contacts().resolve(["admin", "chris", "a.b+c@sub.x.com", 2485555555, "???"])
    assert r.emails == ["chris@x.com", "joe@x.com", "a.b+c@sub.x.com"]
    assert r.phones == ["+17345555555", "+12485555555"]
    assert r.ntfy_topics == ["chris-t"]
    assert r.unresolved == ["admin:ghost", "???"]


def test_resolve_type_error():
    with pytest.raises(TypeError):
        contacts().resolve(3.5)


def test_default_contacts_file_loads():
    c = Contacts.load()
    assert "chris" in c.users and "admin" in c.groups
