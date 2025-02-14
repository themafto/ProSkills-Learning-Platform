from fastapi import FastAPI
from appBackend.routers import auth

app = FastAPI()

app.include_router(auth.router)
