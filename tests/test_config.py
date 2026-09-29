import json
import socket
import warnings

import pytest
from pydantic import SecretStr

from resume_cli import config
from resume_cli.cli import main
from resume_cli.config import (AISettings, PROVIDERS, load_saved, resolve_settings,
                               save_settings, timeout_value, validate_url)
from resume_cli.errors import ResumeError

SECRET = "fake-test-secret-not-real"


def settings():
    return AISettings(provider="DeepSeek", base_url="https://api.deepseek.com",
                      model="demo-model", api_key=SecretStr(SECRET))


def terminal(monkeypatch, answers, key=SECRET):
    iterator = iter(answers)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: next(iterator))
    monkeypatch.setattr("getpass.getpass", lambda prompt: key)


@pytest.mark.parametrize("number", range(1, len(PROVIDERS)))
def test_provider_wizard_offline(monkeypatch, capsys, number):
    def no_network(*args, **kwargs):
        pytest.fail("configuration must never access the network")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    terminal(monkeypatch, [str(number), "my-model", ""])
    assert main(["configure"]) == 0
    result = load_saved()
    assert result.provider == PROVIDERS[number - 1][0]
    assert result.base_url == PROVIDERS[number - 1][1]
    assert result.api_key.get_secret_value() == SECRET
    assert SECRET not in capsys.readouterr().out
    assert SECRET not in repr(result)
    assert (config.config_path().parent / ".gitignore").read_text() == "*\n"


def test_custom_invalid_selection_and_url(monkeypatch):
    terminal(monkeypatch, ["invalid", "99", str(len(PROVIDERS)), "http://bad.example",
                           "https://custom.example/v1", "", "model-x", "y"])
    assert main(["configure"]) == 0
    assert load_saved().base_url == "https://custom.example/v1"


@pytest.mark.parametrize("key", ["", "replace-with-your-key", "secret with spaces"])
def test_invalid_key_not_saved(monkeypatch, capsys, key):
    terminal(monkeypatch, ["1", "demo-model"], key)
    assert main(["configure"]) == 1
    assert not config.config_path().exists()
    assert "配置未保存" in capsys.readouterr().err


def test_show_and_reset(capsys):
    save_settings(settings())
    assert main(["configure", "--show"]) == 0
    output = capsys.readouterr().out
    assert SECRET not in output
    assert json.loads(output)["provider"] == "DeepSeek"
    assert main(["configure", "--reset"]) == 0
    assert not config.config_path().exists()


def test_keep_existing(monkeypatch):
    save_settings(settings())
    before = config.config_path().read_bytes()
    terminal(monkeypatch, ["n"])
    assert main(["configure"]) == 0
    assert config.config_path().read_bytes() == before


def test_cancel_save(monkeypatch):
    save_settings(settings())
    before = config.config_path().read_bytes()
    terminal(monkeypatch, ["y", "1", "new-model", "n"])
    assert main(["configure"]) == 0
    assert config.config_path().read_bytes() == before


def test_noninteractive(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main(["configure"]) == 1
    assert "交互式终端" in capsys.readouterr().err


def test_echo_fallback_aborts(monkeypatch):
    import getpass
    terminal(monkeypatch, ["1", "demo-model"])
    def fallback(prompt):
        warnings.warn("cannot hide input", getpass.GetPassWarning)
        pytest.fail("Must stop before visible password entry")
    monkeypatch.setattr("getpass.getpass", fallback)
    assert main(["configure"]) == 1
    assert not config.config_path().exists()


def test_source_precedence_without_cross_provider_key_leak(monkeypatch, tmp_path):
    save_settings(settings())
    monkeypatch.setenv("OPENAI_BASE_URL", "https://other.example/v1")
    # A URL alone must never redirect a stored provider's key.
    assert resolve_settings().base_url == "https://api.deepseek.com"
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=dotenv-secret\nOPENAI_BASE_URL=https://env.example/v1\n"
        "OPENAI_MODEL=env-model\n", encoding="utf-8")
    assert resolve_settings().api_key.get_secret_value() == "dotenv-secret"
    assert resolve_settings().base_url == "https://env.example/v1"
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    assert resolve_settings().base_url == "https://other.example/v1"
    assert resolve_settings().model == "gpt-4o-mini"


def test_empty_environment_key_does_not_fall_back(monkeypatch):
    save_settings(settings())
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(ResumeError, match="configure"):
        resolve_settings()


def test_corrupt_config_is_redacted(capsys):
    config.config_path().parent.mkdir()
    config.config_path().write_text('{"api_key": "' + SECRET + '"}', encoding="utf-8")
    assert main(["configure", "--show"]) == 1
    captured = capsys.readouterr()
    assert SECRET not in captured.out + captured.err


@pytest.mark.parametrize("url", ["http://example.com", "https://user:secret@example.com",
                                "https://example.com?key=secret", "https://", "https://a:bad"])
def test_unsafe_url(url):
    with pytest.raises(ResumeError):
        validate_url(url)


def test_timeout_env_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("RESUME_AI_TIMEOUT=30\n")
    assert timeout_value() == "30"
    monkeypatch.setenv("RESUME_AI_TIMEOUT", "20")
    assert timeout_value() == "20"


@pytest.mark.parametrize("command", ["extract", "score"])
def test_no_key_never_calls_ai(monkeypatch, tmp_path, capsys, command):
    from pathlib import Path
    sample = Path(__file__).resolve().parents[1] / "examples" / "resume.pdf"
    monkeypatch.setattr("resume_cli.ai.OpenAI", lambda **kwargs: pytest.fail("Must not call AI"))
    args = [command, str(sample)]
    if command == "score":
        jd = tmp_path / "jd.txt"
        jd.write_text("Python engineer")
        args += ["--jd", str(jd)]
    assert main(args) == 1
    captured = capsys.readouterr()
    assert "configure" in captured.err
    assert not captured.out


def test_saved_config_drives_real_sdk(monkeypatch):
    import httpx
    from openai import OpenAI
    from resume_cli.ai import request_ai
    save_settings(settings())
    def handler(request):
        assert request.url.host == "api.deepseek.com"
        assert request.headers["authorization"] == f"Bearer {SECRET}"
        assert json.loads(request.content)["model"] == "demo-model"
        payload = dict(name="", phone="", email="", city="", education=[], skills=[])
        return httpx.Response(200, json={"id": "x", "created": 0, "object": "chat.completion",
            "model": "demo-model", "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(payload)}}]})
    monkeypatch.setattr("resume_cli.ai.OpenAI", lambda **kwargs: OpenAI(
        **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handler))))
    assert request_ai("fictional resume").skills == []
