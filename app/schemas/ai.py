import json

from pydantic import BaseModel

from app.core.time_utils import to_iso_utc
from app.models.ai_analysis import AIAnalysis


class AIAnalysisOut(BaseModel):
    business_id: str
    provider: str
    model: str
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    experience_summary: str
    recommendation: str
    is_latest: bool
    created_at: str

    @classmethod
    def from_model(cls, a: AIAnalysis) -> "AIAnalysisOut":
        return cls(
            business_id=a.business_id,
            provider=a.provider,
            model=a.model,
            match_score=a.match_score,
            matched_skills=json.loads(a.matched_skills or "[]"),
            missing_skills=json.loads(a.missing_skills or "[]"),
            strengths=json.loads(a.strengths or "[]"),
            weaknesses=json.loads(a.weaknesses or "[]"),
            experience_summary=a.experience_summary or "",
            recommendation=a.recommendation or "",
            is_latest=a.is_latest,
            created_at=to_iso_utc(a.created_at),
        )
