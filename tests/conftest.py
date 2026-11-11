import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())


def pytest_configure(config):
    config.addinivalue_line("markers", "live: calls a paid API; skipped by default")
