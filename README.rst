Having Fun with Fun!
====================

The ``fun`` package contains utilities that are entertaining yet somewhat useful. Maybe.

Installation
------------

.. code-block:: bash

    pip install fun-supergus              # core, no dependencies
    pip install "fun-supergus[dotenv]"    # also load credentials from a .env file

For development, clone the `GitHub repo`_ and run:

.. code-block:: bash

    pip install -e ".[dev,dotenv]"
    ruff check . && pytest

Requires Python 3.10 or newer (tested on 3.10-3.13).

.. _GitHub repo: https://github.com/supergus/fun_2026

Package Contents
----------------

* ``fun.communications``: E.T.'s communicator. Send email (SMTP), SMS (Twilio) and push
  notifications (ntfy) with a single command.
* ``fun.printing``: Print fancy, formatted text to the console.
* ``fun/bin``: Executable examples.

Configuration
-------------

Credentials are read from environment variables. Copy ``.env.example`` to ``.env`` (git-ignored;
loaded automatically if ``python-dotenv`` is installed) or export them in your shell:

* ``FUN_SMTP_HOST``: SMTP server, e.g. ``smtp.gmail.com``
* ``FUN_SMTP_PORT``: Default ``587`` (STARTTLS)
* ``FUN_SMTP_USER``: SMTP login
* ``FUN_SMTP_PASSWORD``: SMTP password (for Gmail use an App Password)
* ``FUN_SMTP_FROM``: From address (defaults to ``FUN_SMTP_USER``)
* ``FUN_EMAIL_LOGO_FILE``: Optional image embedded at the bottom of HTML emails
* ``TWILIO_ACCOUNT_SID``: Twilio account SID
* ``TWILIO_AUTH_TOKEN``: Twilio auth token
* ``TWILIO_FROM_NUMBER``: Your Twilio number in E.164, e.g. ``+15555550123``
* ``FUN_NTFY_SERVER``: Default ``https://ntfy.sh``
* ``FUN_NTFY_TOPIC``: Default topic when a recipient has no ``ntfy_topic``
* ``FUN_NTFY_TOKEN``: Optional ntfy access token

Note: sending SMS to US numbers through Twilio requires A2P 10DLC registration (or a verified
toll-free number). If the messages are only for you, ntfy push is far simpler.

The contact directory lives at ``fun/communications/contact_list.json``; pass ``contacts=`` to
use your own file. Users may have ``email``, ``mobile`` and an optional ``ntfy_topic``.

How to Have Fun with E.T.'s Communicator!
-----------------------------------------

.. code-block:: python

    from fun import et

    # Arbitrary phone numbers or emails (10-digit numbers are treated as US +1)
    et.phone_home('Howdy, this is my message to you.', '734-555-5555', subject='Test message')

    # Users and groups from the contact directory
    et.phone_home('There can never be too much foo.', 'joe', subject='Foo')
    et.phone_home('Fear is the mindkiller.', ['admin', 'physics'], subject='I must not fear')

    # Choose channels: defaults are email=True, sms=True, push=False
    et.phone_home('Need those reports today.', 'physics', subject='TPS Reports', sms=False)
    et.phone_home('Build finished', 'chris', email=False, sms=False, push=True)

    # Attachments (email only)
    et.phone_home('Check this out!', 'chris@somewhere.com', subject='Report',
                  attachment='/documents/tps_report.xlsx')

``phone_home()`` returns a ``SendResult``:

.. code-block:: python

    result = et.phone_home('Hello', 'admin')
    if not result.ok:
        for d in result.failed:
            print(d.channel, d.recipient, d.error)

Custom senders
~~~~~~~~~~~~~~

Any object with a ``channel`` attribute and a ``send(message, recipients)`` method returning a list
of ``DeliveryResult`` can be plugged in:

.. code-block:: python

    from fun.communications.senders import SenderSet, SmtpEmailSender, NtfyPushSender

    et.phone_home('Hi', 'chris', senders=SenderSet(email=SmtpEmailSender(), push=NtfyPushSender()),
                  push=True)

How to Have Fun with Fancy Printing!
------------------------------------

.. code-block:: python

    from fun import fancy_print

    fancy_print('I like pretty things', fg='light_pink', bold=True, framed=True)
    fancy_print('Foo Fighters Rule', demo=True)   # built-in demo

That's all for now. Be sure to have some Fun!

License
-------

MIT. See ``LICENSE``.
