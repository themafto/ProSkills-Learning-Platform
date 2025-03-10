import os
from starlette.middleware.cors import CORSMiddleware

def setup_cors(app):
    origins = os.environ.get("ALLOWED_ORIGINS")

    if origins:
        allow_origins = origins.split(",")
    else:
        allow_origins = ["http://localhost:5173"]  # Default value

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )