"""
Cookie-Based Auth Transport
============================

Default authentication transport using HTTP cookies for
session management. Configured for local development
with sensible security defaults.
"""

from __future__ import annotations

import os

from fastapi_users.authentication import CookieTransport


# Cookie configuration from environment
_AUTH_COOKIE_NAME = os.getenv("AUTH_TOKEN_COOKIE_NAME", "auth_token")


def _create_cookie_transport() -> CookieTransport:
    """
    Build the cookie transport with configured settings.

    Returns
    -------
    CookieTransport
        Configured transport instance.
    """
    transport = CookieTransport(
        cookie_name=_AUTH_COOKIE_NAME,
        cookie_secure=False,  # Enable for HTTPS in production
        cookie_httponly=True,
        cookie_samesite="Lax",
        cookie_domain="localhost",
    )
    transport.name = "cookie"
    return transport


# Singleton transport instance
default_transport = _create_cookie_transport()
