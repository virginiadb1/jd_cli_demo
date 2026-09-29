"""Deterministic offline demonstration, deliberately not an AI evaluation."""
import re

from .models import MatchScore, Resume

SKILLS = ("Python", "Golang", "JavaScript", "TypeScript", "React", "Vue", "FastAPI",
          "Docker", "Kubernetes", "PostgreSQL", "MySQL", "Git", "OpenAI", "Linux")


def mock_extract(text: str) -> Resume:
    def find(pattern):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ""

    return Resume(
        name=find(r"^(?:Name|姓名)\s*[:：]\s*(.+)$"),
        phone=find(r"(?<!\d)(1[3-9]\d{9})(?!\d)"),
        email=find(r"([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})"),
        city=find(r"^(?:City|城市)\s*[:：]\s*(.+)$"),
        education=[],
        skills=[skill for skill in SKILLS if re.search(
            rf"(?<!\w){re.escape(skill)}(?!\w)", text, re.IGNORECASE
        )],
    )


def mock_score(text: str, jd: str) -> MatchScore:
    actual = set(mock_extract(text).skills)
    required = set(mock_extract(jd).skills)
    shared = sorted(actual & required)
    skill_score = round(100 * len(shared) / len(required)) if required else 0
    # Experience and education cannot be assessed by this small keyword demo.
    return MatchScore(
        overall_score=(skill_score * 50 + 50) // 100,
        skill_score=skill_score, experience_score=0, education_score=0,
        comment="[MOCK 演示] 仅按技能词命中比例计算技能分；命中："
        + ("、".join(shared) or "无")
        + "。经验及教育未评估，演示占位为 0；总分权重 50%/30%/20%，不代表真实能力。",
        interview_questions=["请介绍一个项目中你负责的模块及其技术取舍。",
                             "请说明你如何处理大模型 API 超时和不合法 JSON 响应。"],
    )
