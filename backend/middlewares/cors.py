import os
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app):
    # Default development origins
    default_origins = [
        "http://localhost:5173",    # Vite default
        "http://localhost:3000",    # React default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Get additional origins from environment or use defaults
    allow_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",")
    allow_origins = [origin.strip() for origin in allow_origins if origin.strip()]
    
    # Combine default and environment origins
    origins = default_origins + allow_origins if allow_origins else default_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
