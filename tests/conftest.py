
import pytest
import ray
import sys
import os

# Add src to path for all tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session", autouse=True)
def ray_session():
    """Initialize Ray once for the entire test session"""
    if not ray.is_initialized():
        try:
            # Try to init with minimal resources to be safe
            ray.init(ignore_reinit_error=True, num_cpus=2)
        except Exception as e:
            print(f"Failed to init Ray: {e}")
            # Fallback or fail
    
    yield
    
    if ray.is_initialized():
        ray.shutdown()
