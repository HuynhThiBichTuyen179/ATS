from pydantic import BaseModel


class DepartmentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None  


class DepartmentOut(BaseModel):
    business_id: str
    name: str
    description: str | None = None
    status: str
