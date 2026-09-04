from pydantic import BaseModel


class HrPerformanceOut(BaseModel):
    hr_business_id: str
    hr_name: str
    candidates_processed: int
    hired: int


class DashboardSummaryOut(BaseModel):
    total_jobs: int
    published_jobs: int
    total_applications: int
    status_breakdown: dict[str, int]
    hired_count: int
    offer_acceptance_rate: float | None
    source_breakdown: dict[str, int]
    avg_time_to_hire_days: float | None
    hr_performance: list[HrPerformanceOut]
