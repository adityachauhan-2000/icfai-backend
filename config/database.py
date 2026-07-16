from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
import shutil

# If running on Vercel, copy the DB to /tmp to avoid read-only filesystem errors
if os.getenv("VERCEL") or os.environ.get("VERCEL_REGION"):
    db_path = "/tmp/sql_app.db"
    if not os.path.exists(db_path):
        try:
            shutil.copyfile(os.path.join(os.path.dirname(__file__), "..", "sql_app.db"), db_path)
        except Exception:
            pass
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
