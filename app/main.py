import logging
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import LogConfig

dictConfig(LogConfig().dict())
logger = logging.getLogger("app")

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Starter!"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Documentation",
        version="1.0.0",
        description="Docs for Starter Project",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
