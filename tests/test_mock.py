from resume_cli.mock import mock_extract, mock_score


def test_mock_extract_is_complete_and_input_independent():
    first = mock_extract("")
    second = mock_extract("完全不同的简历内容")
    assert first == second
    assert all((first.name, first.phone, first.email, first.city))
    assert first.education
    education = first.education[0]
    assert all((education.school, education.major, education.degree, education.graduation_time))
    assert first.skills


def test_mock_score_is_complete_and_input_independent():
    first = mock_score("", "")
    second = mock_score("不同简历", "不同 JD")
    assert first == second
    assert all((first.overall_score, first.skill_score, first.experience_score,
                first.education_score, first.comment, first.interview_questions))
    assert "MOCK" in first.comment
