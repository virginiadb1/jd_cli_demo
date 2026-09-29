import json
from pathlib import Path

import pytest
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from resume_cli.cli import main
from resume_cli.errors import ResumeError
from resume_cli.files import check_ai_length, parse_pdf, read_jd


@pytest.fixture
def pdf(tmp_path):
    path = tmp_path / "resume.pdf"
    document = canvas.Canvas(str(path))
    document.drawString(30, 750, "Name: Alex Chen")
    document.drawString(30, 730, "Python React alex@example.com")
    document.save()
    return path


def test_parse(pdf):
    assert "Alex Chen" in parse_pdf(pdf)


@pytest.mark.parametrize("kind, message", [
    ("missing", "不存在"), ("extension", "不是 PDF"),
    ("fake", "有效的 PDF"), ("broken", "无法读取"),
    ("blank", "文本为空"), ("encrypted", "已加密"), ("directory", "不是文件"),
])
def test_pdf_errors(tmp_path, kind, message):
    path = tmp_path / ("bad.txt" if kind == "extension" else "bad.pdf")
    if kind in {"blank", "encrypted"}:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        if kind == "encrypted":
            writer.encrypt("secret")
        writer.write(path)
    elif kind == "directory":
        path.mkdir()
    elif kind != "missing":
        path.write_bytes(b"%PDF-1.4 broken" if kind == "broken" else b"not pdf")
    with pytest.raises(ResumeError, match=message):
        parse_pdf(path)


@pytest.mark.parametrize("content,message", [(b" \n", "为空"), (b"\xff", "UTF-8")])
def test_jd_errors(tmp_path, content, message):
    path = tmp_path / "jd.txt"
    path.write_bytes(content)
    with pytest.raises(ResumeError, match=message):
        read_jd(path)


def test_missing_jd(tmp_path):
    with pytest.raises(ResumeError, match="不存在"):
        read_jd(tmp_path / "missing.txt")


def test_bom_jd(tmp_path):
    path = tmp_path / "jd.txt"
    path.write_text("岗位 Python", encoding="utf-8-sig")
    assert read_jd(path) == "岗位 Python"


@pytest.mark.parametrize("command", ["extract", "score"])
def test_mock_commands(pdf, tmp_path, capsys, command):
    output = tmp_path / "result.json"
    args = [command, str(pdf), "--mock", "--output", str(output)]
    if command == "score":
        jd = tmp_path / "jd.txt"
        jd.write_text("Python React Docker", encoding="utf-8")
        args += ["--jd", str(jd)]
    assert main(args) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == json.loads(output.read_text(encoding="utf-8"))
    assert "MOCK" in captured.err
    if command == "score":
        assert json.loads(captured.out)["skill_score"] == 67


def test_prevent_overwrite(pdf, capsys):
    original = pdf.read_bytes()
    assert main(["parse", str(pdf), "--output", str(pdf)]) == 1
    assert pdf.read_bytes() == original
    assert "不能覆盖" in capsys.readouterr().err


def test_missing_key(pdf, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["extract", str(pdf)]) == 1
    captured = capsys.readouterr()
    assert "OPENAI_API_KEY" in captured.err
    assert not captured.out


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "extract" in capsys.readouterr().out


def test_length_limit():
    with pytest.raises(ResumeError, match="60000"):
        check_ai_length("x" * 60_001)


def test_module_exit_code():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-m", "resume_cli", "parse", "absent.pdf"],
                            capture_output=True)
    assert result.returncode == 1


def test_sample_exists():
    sample = Path(__file__).resolve().parents[1] / "examples" / "resume.pdf"
    assert "Alex Chen" in parse_pdf(sample)
