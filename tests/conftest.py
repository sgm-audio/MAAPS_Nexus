"""
Pytest configuration and shared fixtures.
"""

import socket
import sys
import threading
import time
import types
import pytest
import requests
import uvicorn


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


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


@pytest.fixture(scope="session", autouse=True)
def ensure_api_server():
    """Ensure the FastAPI server is running on localhost:8000 for integration tests."""
    if _is_port_open("127.0.0.1", 8000):
        yield
        return

    from api.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait until server is ready
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if _is_port_open("127.0.0.1", 8000):
            try:
                r = requests.get("http://127.0.0.1:8000/health", timeout=2.0)
                if r.status_code == 200:
                    break
            except Exception:
                pass
        time.sleep(0.2)

    yield

    server.should_exit = True
    thread.join(timeout=5.0)
