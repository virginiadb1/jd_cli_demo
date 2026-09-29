"""Fixed offline demonstration data, deliberately unrelated to the input files."""

from .models import Education, MatchScore, Resume


def mock_extract(_text: str) -> Resume:
    """Return complete fictional data so every JSON field is visible in a demo."""
    return Resume(
        name="张明（虚构）",
        phone="13800000000",
        email="demo@example.com",
        city="杭州",
        education=[Education(
            school="示例大学",
            major="计算机科学与技术",
            degree="本科",
            graduation_time="2020-06",
        )],
        skills=["Node.js", "React", "Python", "Golang", "Docker", "Git", "OpenAI API"],
    )


def mock_score(_text: str, _jd: str) -> MatchScore:
    """Return a complete fixed score, independent of the resume and JD contents."""
    return MatchScore(
        overall_score=86,
        skill_score=90,
        experience_score=85,
        education_score=75,
        comment=("[MOCK 固定演示数据] 候选人的 Node.js、React 与 Python 技能和岗位较匹配，"
                 "具备全栈项目经验；建议面试时进一步核实 Golang 熟练度及专有云交付经验。"),
        interview_questions=[
            "请介绍一个你主导的 Node.js 与 React 全栈项目，以及关键技术取舍。",
            "你如何设计前后端联调、错误处理和性能监控流程？",
            "请说明你参与专有云部署或交付的实际经验。",
        ],
    )
