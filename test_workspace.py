import os

# Create dummy config before importing anything else
with open("workspace.properties", "w") as f:
    f.write("base_path=./workspace\ngpt_shared_secret=some-magical-key")

from workspace import app, CONFIG
import pytest

@pytest.fixture(scope="session", autouse=True)
def cleanup_dummy_config():
    yield
    os.remove("workspace.properties")

def test_dummy():
    assert app is not None
    assert CONFIG is not None