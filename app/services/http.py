"""Utility helpers for HTTP sessions."""

from __future__ import annotations

from urllib import request as urllib_request

import requests

from ..settings import AppSettings


def create_session(settings: AppSettings | None = None) -> requests.Session:
    """Return a :class:`requests.Session` configured for the application.

    If *settings* enables proxy usage, the session will route requests
    through the configured proxy URL.
    """

    settings = settings or AppSettings.load()
    session = requests.Session()
    if getattr(settings, "use_proxy", False) and getattr(settings, "proxy_url", ""):
        session.proxies.update({
            "http": settings.proxy_url,
            "https": settings.proxy_url,
        })
    return session


def create_opener(settings: AppSettings | None = None) -> urllib_request.OpenerDirector:
    """Return a :class:`urllib.request.OpenerDirector` respecting proxy settings."""

    settings = settings or AppSettings.load()
    if getattr(settings, "use_proxy", False) and getattr(settings, "proxy_url", ""):
        handler = urllib_request.ProxyHandler(
            {"http": settings.proxy_url, "https": settings.proxy_url}
        )
        return urllib_request.build_opener(handler)
    return urllib_request.build_opener()
