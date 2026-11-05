"""
Pytest configuration.

Provides a lightweight fallback implementation of ``zope.event`` so
that gevent (and therefore Locust) can import cleanly inside sandboxed
environments where the official package is unavailable.
"""

import sys
import types


try:
    import zope.event  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - environment specific
    try:
        import zope  # type: ignore
    except ModuleNotFoundError:
        zope = types.ModuleType("zope")
        sys.modules["zope"] = zope

    shim = types.ModuleType("zope.event")
    shim.subscribers = []

    def notify(event):
        for subscriber in list(shim.subscribers):
            subscriber(event)

    shim.notify = notify
    zope.event = shim  # type: ignore[attr-defined]
    sys.modules["zope.event"] = shim
