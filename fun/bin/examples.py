"""Examples from the Fun package.

Configure credentials first: copy ``.env.example`` to ``.env`` (needs ``python-dotenv``)
or export the environment variables it lists.
"""

import fun

# =================================================================
# Using ET's Communicator...!
# =================================================================

# Arbitrary phone numbers or emails (10-digit numbers are treated as US +1):
fun.et.phone_home("Ricki don't lose my number.", 7345555555, subject="Waiting by the phone")
fun.et.phone_home("Howdy, this is my message to you.", "734-555-5555", subject="Message for Chris")
fun.et.phone_home("Have you seen Barney lately?", ["fred@flintstones.com", "wilma@flintstones.com"])

# Users and groups from fun/communications/contact_list.json:
fun.et.phone_home("There can never be too much foo.", "joe", subject="Foo")
fun.et.phone_home("Fear is the mindkiller.", ["admin", "physics"], subject="I must not fear")

# By default email=True, sms=True, push=False. Pick channels explicitly:
result = fun.et.phone_home("Need those reports today.", "physics", subject="TPS Reports", sms=False)
print("all delivered" if result.ok else f"failures: {result.failed}")

# Push notification via ntfy only:
fun.et.phone_home("Build finished", "chris", subject="CI", email=False, sms=False, push=True)

# =================================================================
# Using the Fancy Printer...!
# =================================================================

fun.fancy_print("I like pretty things", fg="light_pink", bold=True, framed=True)
fun.fancy_print("Foo Fighters Rule", demo=True)
