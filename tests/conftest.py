import pytest


@pytest.fixture(autouse=True)
def isolate_credentials(monkeypatch, tmp_path):
    """Tests never read or modify the developer's real configuration or key."""
    for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "RESUME_AI_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("resume_cli.config.config_path", lambda: tmp_path / "settings" / "config.json")
    monkeypatch.chdir(tmp_path)
