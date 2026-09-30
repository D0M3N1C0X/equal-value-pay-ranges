import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import model  # noqa: E402


@pytest.fixture(scope="session")
def out():
    return model.run()
