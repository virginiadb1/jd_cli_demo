from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader

from .errors import ResumeError

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_TEXT_CHARS = 60_000


def clean_pdf_text(text: str) -> str:
    """Replace PDF layout control codes without joining words or changing Unicode text."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        " " if char != "\n" and unicodedata.category(char) in {"Cc", "Zs"} else char
        for char in text
    )
    return "\n".join(re.sub(r" +", " ", line).rstrip() for line in text.split("\n")).strip()


def check_file(path: Path, label: str) -> None:
    if not path.exists():
        raise ResumeError(f"{label}文件不存在：{path}")
    if not path.is_file():
        raise ResumeError(f"{label}路径不是文件：{path}")
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ResumeError(f"{label}文件超过 20 MB 限制。")
    except OSError as exc:
        raise ResumeError(f"无法访问{label}文件。请检查权限。") from exc


def parse_pdf(path: Path) -> str:
    check_file(path, "PDF")
    if path.suffix.lower() != ".pdf":
        raise ResumeError("文件不是 PDF：请提供 .pdf 文件。")
    try:
        with path.open("rb") as stream:
            if b"%PDF-" not in stream.read(1024):
                raise ResumeError("文件不是有效的 PDF（缺少 PDF 标识）。")
            stream.seek(0)
            reader = PdfReader(stream)
            if reader.is_encrypted:
                raise ResumeError("PDF 已加密，请先解密后重试。")
            if len(reader.pages) > 100:
                raise ResumeError("PDF 超过 100 页限制。")
            text = clean_pdf_text("\n\n".join(page.extract_text() or "" for page in reader.pages))
    except ResumeError:
        raise
    except Exception as exc:
        raise ResumeError("PDF 无法读取：文件可能已损坏或无访问权限。") from exc
    if not text:
        raise ResumeError("PDF 文本为空：可能是扫描件；本工具暂不支持 OCR。")
    return text


def read_jd(path: Path) -> str:
    check_file(path, "JD")
    try:
        text = path.read_text(encoding="utf-8-sig").strip()
    except UnicodeError as exc:
        raise ResumeError("JD 编码错误：请另存为 UTF-8 文本文件。") from exc
    except OSError as exc:
        raise ResumeError("JD 文件无法读取，请检查权限。") from exc
    if not text:
        raise ResumeError("JD 文件为空。")
    return text


def check_ai_length(text: str) -> None:
    if len(text) > MAX_TEXT_CHARS:
        raise ResumeError("输入总文本超过 60000 字符，请缩短简历或 JD 后重试。")
