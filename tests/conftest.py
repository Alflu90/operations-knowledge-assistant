import pytest

from app import config


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Ogni test usa un database SQLite temporaneo."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
