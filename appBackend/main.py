from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from appBackend.routers import auth, courses
from appBackend.db.session import Base, engine


app = FastAPI()

origins = [
  "http://localhost:3000",
  "http://localhost:8001", # на всякий
  "http://localhost" # и это тоже
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(courses.router)


