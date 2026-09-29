from pathlib import Path

from resume_cli.cli import main
from resume_cli.display import cell_width, format_resume, wrap_line
from resume_cli.files import parse_pdf


def test_markers_join_text_and_headings_stand_out():
    output = format_resume("个人优势\n具备开发经验\n技术栈\n•\nAI / Agent:\n◦\nLangGraph\n◦\nMCP", "sample.pdf")
    assert "【个人优势】" in output
    assert "【技术栈】" in output
    assert "  AI / Agent:" in output
    assert "    - LangGraph\n    - MCP" in output
    assert "◦" not in output
    assert "•" not in output


def test_unicode_width_and_long_words():
    lines = wrap_line("中文 mixed words " + "x" * 70, 24, "  - ", "    ")
    assert all(cell_width(line) <= 24 for line in lines)
    assert "".join(lines).replace(" ", "") == "-中文mixedwords" + "x" * 70


def test_narrow_terminal():
    output = format_resume("工作经历\n" + "科学计算平台" * 12, "very-long-file-name.pdf", width=24)
    assert all(cell_width(line) <= 24 for line in output.splitlines())


def test_plain_redirect_and_pretty_export(tmp_path, capsys):
    path = Path(__file__).resolve().parents[1] / "examples" / "resume.pdf"
    text = parse_pdf(path)
    assert main(["parse", str(path)]) == 0
    assert capsys.readouterr().out == text + "\n"
    saved = tmp_path / "resume.txt"
    assert main(["parse", str(path), "--pretty", "--output", str(saved)]) == 0
    assert "PDF 简历 |" in capsys.readouterr().out
    assert saved.read_text(encoding="utf-8") == text + "\n"
    assert main(["parse", str(path), "--plain"]) == 0
    assert capsys.readouterr().out == text + "\n"
