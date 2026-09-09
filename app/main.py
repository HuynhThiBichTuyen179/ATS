from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.routers import (
    ai,
    applications,
    audit,
    auth,
    candidate_sources,
    candidates,
    dashboard,
    departments,
    email_templates,
    interview,
    jobs,
    offers,
    resumes,
    users,
)

# Import de dam bao moi model duoc dang ky voi Base truoc khi create_all
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ATS API",
    description="Recruitment Management System API (Offer 4-eyes approval, "
    "unlimited re-apply, prefixed Business ID, AI CV Screening, Interview "
    "scheduling, Audit Log, Email Automation)",
    version="2.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(departments.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(offers.router)
app.include_router(email_templates.router)
app.include_router(ai.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
app.include_router(candidates.router)
app.include_router(candidate_sources.router)
app.include_router(resumes.router)
app.include_router(interview.router)


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/reset-password", include_in_schema=False)
def serve_reset_password_page():
    # link trong email Forgot Password tro ve day (xem
    # password_reset_service.py). SPA tu doc "?token=" tren URL va mo modal
    # dat lai mat khau (xem autoOpenResetPasswordFromUrl() trong index.html).
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}
