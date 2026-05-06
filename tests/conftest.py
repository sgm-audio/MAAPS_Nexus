import pytest
import sys
import os
import time

# Add src to path for all tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ray

    RAY_AVAILABLE = True
except ImportError:
    ray = None
    RAY_AVAILABLE = False


@pytest.fixture(scope="session", autouse=True)
def ray_session():
    """Initialize Ray once for the entire test session (skipped if ray not installed)"""
    if not RAY_AVAILABLE:
        yield
        return

    if not ray.is_initialized():
        try:
            ray.init(ignore_reinit_error=True, num_cpus=2)
        except Exception as e:
            print(f"Failed to init Ray: {e}")

    yield

    if ray.is_initialized():
        ray.shutdown()
