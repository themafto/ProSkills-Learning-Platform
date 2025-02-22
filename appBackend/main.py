from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from appBackend.controllers import auth, courses
from appBackend.database import Base, engine
from appBackend.middlewares.cors import setup_cors

app = FastAPI()



setup_cors(app)
Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(courses.router)


