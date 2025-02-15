from fastapi import FastAPI

from appBackend.routers import auth
from appBackend.db.session import Base, engine

app = FastAPI()
Base.metadata.create_all(bind=engine)
app.include_router(auth.router)


