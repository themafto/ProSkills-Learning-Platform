import os
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app):
    allow_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
