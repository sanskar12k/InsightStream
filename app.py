from pathlib import Path
import sys
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from backend.config import setting

# Load environment variables
# Priority: .env.local (local dev) > .env (production/default)
backend_dir = Path(__file__).parent / "backend"
env_local = backend_dir / ".env.local"
env_default = backend_dir / ".env"

if env_local.exists():
    load_dotenv(dotenv_path=env_local)
    print(f"✅ Loaded environment from: {env_local}")
else:
    load_dotenv(dotenv_path=env_default)
    print(f"✅ Loaded environment from: {env_default}") 

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
print(f"✅ Added to Python path: {project_root}")

# Disable docs in production for security
docs_url = None if os.getenv("RAILWAY_ENVIRONMENT") else "/docs"
redoc_url = None if os.getenv("RAILWAY_ENVIRONMENT") else "/redoc"

app = FastAPI(
    title="InsghtStream",
    description="Backend API for E-commerce Scraper",
    version="1.0.0",
    docs_url=docs_url,  # Disabled in production
    redoc_url=redoc_url  # Disabled in production
)

# Session middleware (kept for potential future use, but not used for OAuth)
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-production")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie="session",
    max_age=1800,  # 30 minutes
    same_site="lax",
    https_only=os.getenv("RAILWAY_ENVIRONMENT") is not None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins= setting.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add validation error handler for user-friendly messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log for debugging
    print("=" * 80)
    print("VALIDATION ERROR:")
    print(f"URL: {request.url}")
    print(f"Errors: {exc.errors()}")
    print("=" * 80)

    # Create user-friendly error messages
    errors = exc.errors()
    error_messages = []

    for error in errors:
        field = error.get('loc', [])[-1] if error.get('loc') else 'field'
        msg = error.get('msg', 'Invalid value')
        error_type = error.get('type', '')

        # Customize messages based on error type
        if 'string_too_short' in error_type:
            if field == 'password':
                error_messages.append("Password must be at least 6 characters long")
            else:
                error_messages.append(f"{field.capitalize()} is too short")
        elif 'string_pattern_mismatch' in error_type:
            if field == 'email':
                error_messages.append("Please enter a valid email address")
            else:
                error_messages.append(f"Invalid format for {field}")
        elif 'missing' in error_type:
            error_messages.append(f"{field.capitalize()} is required")
        else:
            error_messages.append(f"{field.capitalize()}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_messages[0] if error_messages else "Validation error",
            "errors": error_messages,
            "fields": [err.get('loc', [])[-1] for err in errors if err.get('loc')]
        }
    )

@app.get("/")
def root():
    return {"message": "InsightStream Backend is running.", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

from backend.api.routes import user, scrapper, auth
app.include_router(user.router)
app.include_router(scrapper.router)
app.include_router(auth.router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Railway uses $PORT env var
    uvicorn.run(app, host="0.0.0.0", port=port)