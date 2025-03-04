from fastapi import FastAPI
from backend.controllers import auth, courses, students
from backend.database import Base, engine
from backend.middlewares.cors import setup_cors

app = FastAPI()



setup_cors(app)
Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(students.router)


