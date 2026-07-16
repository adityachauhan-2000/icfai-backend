from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

# Load .env file manually on startup (supporting multiple encodings like UTF-8 and UTF-16)
if os.path.exists(".env"):
    for enc in ["utf-8", "utf-16", "latin-1"]:
        try:
            with open(".env", "r", encoding=enc) as f:
                content = f.read()
                if enc != "utf-16" and "\x00" in content:
                    continue
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('\ufeff'):
                        line = line[1:]
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
                break
        except Exception:
            continue

from config.database import engine, Base

# Import all models here so SQLAlchemy knows about them before creating tables
from auth.models import Student
from study_plans.models import Program, Specialization, Course, Topic, ProgressStatus, CourseProgress, IsComplete
from case_studies.models import CaseStudy, CaseStudyResource
from preparation.models import Company, InterviewRound

# Database tables will now be created via Alembic migrations
Base.metadata.create_all(bind=engine)

from auth.router import router as auth_router
from study_plans.router import router as study_plans_router
from admin.router import router as admin_router
from case_studies.router import router as case_studies_router
from preparation.router import router as preparation_router
from test_router import router as test_router
from news_router import router as news_router

from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if os.getenv("FRONTEND_URL"):
    origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|.*\.vercel\.app|.*\.netlify\.app|.*\.onrender\.com|.*\.icfai\.edu|.*\.kitefish\.ai)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(study_plans_router)
app.include_router(admin_router)
app.include_router(case_studies_router, prefix="/api")
app.include_router(preparation_router, prefix="/api")
app.include_router(test_router, prefix="/test")
app.include_router(news_router)

if not os.getenv("VERCEL"):
    os.makedirs("uploads/logos", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "Welcome to the Faculty Management System!"}
