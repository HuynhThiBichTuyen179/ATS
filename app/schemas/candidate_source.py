from pydantic import BaseModel


class CandidateSourceCreateRequest(BaseModel):
    name: str


class CandidateSourceUpdateRequest(BaseModel):
    name: str | None = None
    status: str | None = None 


class CandidateSourceOut(BaseModel):
    business_id: str
    name: str
    status: str
