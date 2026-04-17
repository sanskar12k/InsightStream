"""
Google OAuth 2.0 Authentication Routes
"""
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from urllib.parse import urlencode

from backend.database.database import get_db
from backend.services.db_services import DatabaseService as DBService
from backend.auth.jwt_auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models.user_models import TokenResponse, UserResponse

load_dotenv()

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth login flow.

    Redirects user to Google's OAuth consent screen.
    """
    # Build the Google OAuth URL manually to avoid session-based state
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account"
    }

    google_auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str = None, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.

    After user authorizes on Google, this endpoint:
    1. Receives authorization code
    2. Exchanges it for access token
    3. Fetches user info from Google
    4. Creates or updates user in database
    5. Returns JWT token

    Returns:
        Redirects to frontend with JWT token and user info
    """
    try:
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not provided"
            )

        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange authorization code: {token_response.text}"
                )

            token_data = token_response.json()
            google_access_token = token_data.get("access_token")

            # Fetch user info from Google
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {google_access_token}"}
            )

            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information from Google"
                )

            user_info = userinfo_response.json()

        # Extract user data
        google_id = user_info.get('id')  # Google's unique user ID
        email = user_info.get('email')
        name = user_info.get('name') or email.split('@')[0]

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete user information from Google"
            )

        # Create or update user in database
        user = DBService.update_or_create_google_user(
            db=db,
            google_id=google_id,
            email=email,
            name=name
        )

        # Create JWT access token
        access_token = create_access_token(
            data={"sub": str(user.user_id)}
        )

        # Prepare user data
        user_data = {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }

        # Redirect to frontend with token
        import urllib.parse
        import json
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        user_json = urllib.parse.quote(json.dumps(user_data))

        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}&user={user_json}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/google/status")
async def google_auth_status():
    """
    Check if Google OAuth is properly configured.

    Returns configuration status (without exposing secrets).
    """
    return {
        "google_oauth_configured": bool(os.getenv('GOOGLE_CLIENT_ID')),
        "redirect_uri": os.getenv('GOOGLE_REDIRECT_URI'),
        "client_id": os.getenv('GOOGLE_CLIENT_ID')[:20] + "..." if os.getenv('GOOGLE_CLIENT_ID') else None
    }
