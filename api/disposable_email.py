"""Disposable / throw-away email domain blocklist.

Used at signup to refuse the most common temp-mail providers — the cheapest
anti-abuse layer for the 14-day Pro trial. The trial is generous (no card,
full feature unlock) so we want to block obvious cycling.

This is a curated short list, not exhaustive. We deliberately don't pull in
a 50k-domain blocklist package because:
  - Most of those lists are stale and have false positives
  - A determined abuser will just buy a $2 domain anyway
  - Email verification (the actual gate) catches what this misses

If a real customer complains their domain is blocked, add an env override:
    DISPOSABLE_EMAIL_ALLOW=mydomain.com,othermail.in
"""
from __future__ import annotations

import os
from functools import lru_cache

# Curated list of the most-used disposable mailbox providers. Sorted
# alphabetically so future merges read cleanly.
_BLOCKED_DOMAINS = frozenset({
    "0-mail.com", "10minutemail.com", "10minutemail.net", "20minutemail.com",
    "30minutemail.com", "anonymbox.com", "asdasd.ru",
    "burnermail.io", "byom.de",
    "deadaddress.com", "disposableinbox.com", "disposablemail.com", "dispostable.com",
    "emailondeck.com", "emailtemporanea.com", "emailtemporario.com.br",
    "fakeinbox.com", "fakemail.fr", "fakemailgenerator.com", "fastmail.fm",
    "getairmail.com", "getnada.com", "guerrillamail.biz", "guerrillamail.com",
    "guerrillamail.de", "guerrillamail.info", "guerrillamail.net", "guerrillamail.org",
    "guerrillamailblock.com",
    "harakirimail.com",
    "incognitomail.com", "inboxalias.com", "inboxbear.com",
    "jetable.com", "jetable.fr.nf", "jetable.org",
    "mail-temporaire.fr", "mail.tm", "mailcatch.com", "maildrop.cc",
    "mailexpire.com", "mailforspam.com", "mailinator.com", "mailinator.net",
    "mailinator.org", "mailnesia.com", "mailnull.com", "mailtothis.com",
    "moakt.com", "mohmal.com", "mvrht.com", "mytrashmail.com",
    "nada.email", "nada.ltd", "noclickemail.com", "no-spam.ws",
    "ohi.tw", "onlatedotcom.info", "openmailbox.org",
    "pokemail.net", "putthisinyourspamdatabase.com",
    "rcpt.at",
    "sharklasers.com", "sneakemail.com", "snkmail.com", "sogetthis.com",
    "spam4.me", "spamavert.com", "spambog.com", "spambox.us", "spamfree24.com",
    "spamfree24.de", "spamfree24.eu", "spamfree24.info", "spamfree24.net",
    "spamfree24.org", "spamgourmet.com", "spaml.de", "spammotel.com",
    "spamspot.com", "spamthis.co.uk", "superrito.com",
    "tempemail.co", "tempinbox.com", "tempmail.com", "tempmail.de",
    "tempmail.email", "tempmail.eu", "tempmail.in", "tempmail.io", "tempmail.it",
    "tempmail.net", "tempmail.ninja", "tempmail.org", "tempmail.us",
    "tempmail.ws", "tempmailaddress.com", "tempmail-id.com", "tempmail-plus.com",
    "tempmailo.com", "tempr.email", "thankyou2010.com",
    "throwaway.email", "throwawaymail.com", "tmail.ws", "tmailinator.com",
    "trashmail.at", "trashmail.com", "trashmail.de", "trashmail.io",
    "trashmail.me", "trashmail.net", "trashmail.org", "trbvm.com",
    "wegwerfemail.de", "wegwerfmail.de", "wegwerfmail.info", "wegwerfmail.net",
    "wegwerfmail.org",
    "yopmail.com", "yopmail.fr", "yopmail.net",
})


@lru_cache(maxsize=1)
def _allowlist() -> frozenset[str]:
    """Env-driven allowlist override — let an admin un-block a domain
    without redeploying if a real customer hits a false positive."""
    raw = (os.getenv("DISPOSABLE_EMAIL_ALLOW") or "").strip()
    if not raw:
        return frozenset()
    return frozenset(d.strip().lower() for d in raw.split(",") if d.strip())


def is_disposable(email: str) -> bool:
    """Return True if the email's domain is on the disposable list AND
    isn't overridden via DISPOSABLE_EMAIL_ALLOW."""
    if not email or "@" not in email:
        return False
    domain = email.rsplit("@", 1)[-1].strip().lower()
    if domain in _allowlist():
        return False
    return domain in _BLOCKED_DOMAINS
