import json

import httpx
import pytest
from openai import OpenAI

from resume_cli.ai import request_ai, validate_response
from resume_cli.errors import ResumeError
from resume_cli.models import MatchScore, Resume

RESUME = dict(name="测试", phone="", email="", city="", education=[], skills=["Python"])
SCORE = dict(overall_score=82, skill_score=88, experience_score=80, education_score=70,
             comment="有技能证据", interview_questions=["介绍项目"])


def test_markdown_json():
    result = validate_response("```json\n" + json.dumps(RESUME) + "\n```", Resume)
    assert result.name == "测试"


@pytest.mark.parametrize("value", [-1, 101, 80.5, "80", True, None])
def test_invalid_score(value):
    with pytest.raises(ResumeError):
        validate_response(json.dumps({**SCORE, "skill_score": value}), MatchScore)


@pytest.mark.parametrize("raw", ['{}', '{bad}', '[]', json.dumps({**RESUME, "extra": 1})])
def test_invalid_resume(raw):
    with pytest.raises(ResumeError):
        validate_response(raw, Resume)


@pytest.mark.parametrize("field,value", [("comment", " "), ("interview_questions", []),
                                        ("interview_questions", [""])])
def test_empty_reason(field, value):
    with pytest.raises(ResumeError):
        validate_response(json.dumps({**SCORE, field: value}), MatchScore)


def install_transport(monkeypatch, handler):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://mock.invalid/v1")
    monkeypatch.setattr("resume_cli.ai.OpenAI", lambda **kwargs: OpenAI(
        **{**kwargs, "max_retries": 0},
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ))


def completion(content, finish="stop"):
    return {"id": "demo", "object": "chat.completion", "created": 1, "model": "demo",
            "choices": [{"index": 0, "finish_reason": finish,
                         "message": {"role": "assistant", "content": content}}]}


@pytest.mark.parametrize("jd", [None, "Python engineer"])
def test_sdk_success(monkeypatch, jd):
    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        assert json.loads(body["messages"][1]["content"])["resume"] == "resume text"
        return httpx.Response(200, json=completion(json.dumps(RESUME if jd is None else SCORE)))
    install_transport(monkeypatch, handler)
    result = request_ai("resume text", jd)
    assert isinstance(result, Resume if jd is None else MatchScore)
    if jd is not None:
        assert result.overall_score == 82


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_api_error(monkeypatch, status):
    install_transport(monkeypatch, lambda request: httpx.Response(
        status, json={"error": {"message": "sensitive content", "type": "api_error"}}))
    with pytest.raises(ResumeError, match=str(status)) as exc:
        request_ai("private resume")
    assert "sensitive" not in str(exc.value)


def test_timeout(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("private data", request=request)
    install_transport(monkeypatch, handler)
    with pytest.raises(ResumeError, match="超时"):
        request_ai("resume")


@pytest.mark.parametrize("content,finish", [(None, "stop"), ('{}', "length"), ('bad', "stop")])
def test_bad_completion(monkeypatch, content, finish):
    install_transport(monkeypatch, lambda request: httpx.Response(
        200, json=completion(content, finish)))
    with pytest.raises(ResumeError):
        request_ai("resume")
