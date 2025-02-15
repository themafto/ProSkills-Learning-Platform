from fastapi import FastAPI

from appBackend.db.session import create_db_and_tables
from appBackend.routers import auth

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()


app.include_router(auth.router)
