import pytest
from pypdf import PdfWriter

from resume_cli.errors import ResumeError
from resume_cli.files import clean_pdf_text, parse_pdf


def test_pdf_control_codes_preserve_word_boundaries_and_chinese():
    assert clean_pdf_text("基本信息\x01\nAI\x01Agent: \x01\nTool\x01/\x01Function\x01Calling\x01") == (
        "基本信息\nAI Agent:\nTool / Function Calling"
    )


def test_control_sequences_cannot_reach_terminal():
    cleaned = clean_pdf_text("hello\x1b[31m\x00\x07world\x7f\x85!")
    assert not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in cleaned)
    assert "world" in cleaned


def test_preserve_newlines_and_visible_unicode():
    assert clean_pdf_text("中文，标点！\r\nPython\tReact\u00a0Docker\u2009Git\r下一段") == (
        "中文，标点！\nPython React Docker Git\n下一段"
    )
    assert clean_pdf_text("👩\u200d💻 café") == "👩\u200d💻 café"


def test_control_only_pdf_is_empty(tmp_path, monkeypatch):
    path = tmp_path / "control.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(path)
    monkeypatch.setattr("pypdf._page.PageObject.extract_text", lambda self: "\x01\x00\t \n")
    with pytest.raises(ResumeError, match="文本为空"):
        parse_pdf(path)
