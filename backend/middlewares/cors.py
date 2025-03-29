import os
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app):
    # Development origins
    dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Get additional origins from environment
    env_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",")
    env_origins = [origin.strip() for origin in env_origins if origin.strip()]
    
    # Combine all origins
    all_origins = list(set(dev_origins + env_origins))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )
