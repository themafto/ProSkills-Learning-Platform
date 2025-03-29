from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from backend.controllers import (
    auth,
    courses,
    students,
    assignments,
    filesForCourse,
    sections,
    progress,
)
from backend.database import Base, engine
from backend.dependencies.getdb import get_db
from backend.middlewares.cors import setup_cors
from backend.utils import create_admin_user

app = FastAPI()

setup_cors(app)
Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(students.router)
app.include_router(assignments.router)
app.include_router(filesForCourse.router)
app.include_router(sections.router)
app.include_router(progress.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application data on startup"""
    db = next(get_db())
    try:
        # Create admin user if it doesn't exist
        create_admin_user(db)
    finally:
        db.close()
