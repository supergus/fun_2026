import pytest

ENV_VARS = [
    "FUN_SMTP_HOST",
    "FUN_SMTP_PORT",
    "FUN_SMTP_USER",
    "FUN_SMTP_PASSWORD",
    "FUN_SMTP_FROM",
    "FUN_SMTP_STARTTLS",
    "FUN_EMAIL_LOGO_FILE",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_FROM_NUMBER",
    "FUN_NTFY_SERVER",
    "FUN_NTFY_TOPIC",
    "FUN_NTFY_TOKEN",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in ENV_VARS:
        monkeypatch.delenv(v, raising=False)
    # Never load a developer's real .env during tests
    monkeypatch.setattr("fun.communications.communicator.load_dotenv_if_available", lambda *a, **k: False)
