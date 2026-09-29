"""Readable, dependency-free terminal presentation; never changes exported/AI text."""
import re
import shutil
import unicodedata

HEADINGS = {
    "基本信息", "个人信息", "个人优势", "个人简介", "专业技能", "技术栈", "技能清单",
    "工作经历", "工作经验", "项目经历", "项目经验", "教育经历", "教育背景", "自我评价",
    "荣誉奖项", "证书", "联系方式", "education", "skills", "experience", "project",
    "projects", "summary", "contact",
}
MARKERS = {"•", "●", "▪", "■", "◦", "○", "·", "‣", "-", "*"}
SUB_MARKERS = {"◦", "○", "·"}


def cell_width(text: str) -> int:
    return sum(0 if unicodedata.combining(char) else
               2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in text)


def wrap_line(text: str, width: int, prefix: str = "", continuation: str = "") -> list[str]:
    """Wrap CJK by character and English by word when possible."""
    tokens = re.findall(r"[\x21-\x7e]+|[^\x21-\x7e]", text)
    lines = []
    line = prefix
    used = cell_width(prefix)
    for token in tokens:
        size = cell_width(token)
        if used + size > width and line.strip() and size <= width - cell_width(continuation):
            lines.append(line.rstrip())
            line, used = continuation, cell_width(continuation)
            if token.isspace():
                continue
        for char in token:
            size = cell_width(char)
            if used + size > width:
                lines.append(line.rstrip())
                line, used = continuation, cell_width(continuation)
            if not line.strip() and char.isspace():
                continue
            line += char
            used += size
    if line.strip():
        lines.append(line.rstrip())
    return lines


def format_resume(text: str, filename: str, width: int | None = None) -> str:
    width = max(20, min(width or shutil.get_terminal_size((96, 24)).columns - 2, 96))
    output = wrap_line(f"PDF 简历 | {filename}", width)
    output += [f"本地文本解析 · {len(text)} 字符", "=" * width]
    pending = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in MARKERS:
            if pending is not None:
                output.append("  -")
            pending = line
            continue
        inline = re.match(r"^([•●▪■◦○·‣])\s*(.+)$", line)
        if inline:
            marker, line = inline.groups()
        else:
            marker = pending
        pending = None
        heading = line.rstrip(":：").lower() in HEADINGS
        category = len(line) <= 32 and line.endswith((":", "："))
        if heading or category:
            if output[-1] != "":
                output.append("")
            if heading:
                output.extend(wrap_line(f"【{line.rstrip(':：')}】", width))
            else:
                output.extend(wrap_line(line, width, "  ", "  "))
        elif marker:
            prefix = "    - " if marker in SUB_MARKERS else "  - "
            output.extend(wrap_line(line, width, prefix, " " * len(prefix)))
        else:
            output.extend(wrap_line(line, width))
    if pending is not None:
        output.append("  -")
    output += ["", "-" * width, "提示：--plain 输出纯文本；--output 保存提取文本。"]
    # Metadata and footer must also fit narrow terminals.
    return "\n".join(part for line in output for part in (
        wrap_line(line, width) if cell_width(line) > width else [line]
    ))
