"""
Pytest configuration and shared fixtures.
"""

import os
import socket
import sys
import threading
import time
import types
import pytest
import requests
import uvicorn


TEST_HOST = "127.0.0.1"
TEST_PORT = int(os.getenv("MAAPS_TEST_PORT", "18000"))
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"
WS_URL = f"ws://{TEST_HOST}:{TEST_PORT}/ws"

os.environ["MAAPS_TEST_PORT"] = str(TEST_PORT)
os.environ["MAAPS_BASE_URL"] = BASE_URL
os.environ["MAAPS_WS_URL"] = WS_URL


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


def _is_maaps_server(host: str, port: int) -> bool:
    try:
        r = requests.get(f"http://{host}:{port}/health", timeout=1.0)
        return r.status_code == 200 and ("health_score" in r.text or "healthy" in r.text)
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_api_server():
    """Ensure the FastAPI server is running for integration tests."""
    if _is_maaps_server(TEST_HOST, TEST_PORT):
        yield
        return

    from api.main import app

    config = uvicorn.Config(app, host=TEST_HOST, port=TEST_PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait until server is ready
    deadline = time.time() + 15.0
    while time.time() < deadline:
        if _is_maaps_server(TEST_HOST, TEST_PORT):
            break
        time.sleep(0.2)

    yield

    server.should_exit = True
    thread.join(timeout=5.0)
