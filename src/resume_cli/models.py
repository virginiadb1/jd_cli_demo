from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class ResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Education(ResultModel):
    school: str
    major: str
    degree: str
    graduation_time: str


class Resume(ResultModel):
    name: str
    phone: str
    email: str
    city: str
    education: list[Education]
    skills: list[str]


ScoreValue = Annotated[int, Field(ge=0, le=100)]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class MatchScore(ResultModel):
    overall_score: ScoreValue
    skill_score: ScoreValue
    experience_score: ScoreValue
    education_score: ScoreValue
    comment: NonEmpty
    interview_questions: Annotated[list[NonEmpty], Field(min_length=1)]
