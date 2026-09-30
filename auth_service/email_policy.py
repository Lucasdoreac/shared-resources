"""Email recipient and delivery policies for authentication links."""

import os


def is_email_dry_run(value=None):
    """Return whether outbound email delivery is explicitly disabled."""
    if value is None:
        value = os.getenv("EMAIL_DRY_RUN", "")
    return str(value).strip().casefold() == "true"


def is_email_allowed(email, additional_allowlist=""):
    """Allow institutional addresses and explicitly listed exact addresses.

    ``additional_allowlist`` is a comma-separated environment value. Keep any
    developer-only entries scoped to the Staging service, leaving it empty in
    Production.
    """
    if not isinstance(email, str):
        return False

    normalized_email = email.strip().casefold()
    if not normalized_email or normalized_email.count("@") != 1:
        return False

    local_part, domain = normalized_email.split("@", 1)
    if not local_part or not domain:
        return False

    if domain == "udf.edu.br":
        return True

    allowed_addresses = {
        address.strip().casefold()
        for address in additional_allowlist.split(",")
        if address.strip()
    }
    return normalized_email in allowed_addresses
