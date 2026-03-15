"""
Google OAuth 2.0 Authentication Routes
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from dotenv import load_dotenv

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

# OAuth configuration
oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


@router.get("/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.

    Redirects user to Google's OAuth consent screen.
    """
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')

    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.

    After user authorizes on Google, this endpoint:
    1. Receives authorization code
    2. Exchanges it for access token
    3. Fetches user info from Google
    4. Creates or updates user in database
    5. Returns JWT token

    Returns:
        TokenResponse with JWT token and user info
    """
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)

        # Get user info from Google
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google"
            )

        # Extract user data
        google_id = user_info.get('sub')  # Google's unique user ID
        email = user_info.get('email')
        name = user_info.get('name') or email.split('@')[0]  # Use email prefix if name not available

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

        # For web app: Redirect to frontend with token
        import urllib.parse
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        user_json = urllib.parse.quote(str(user_data).replace("'", '"'))

        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}&user={user_json}"
        )

        # For API response (if you need JSON instead of redirect):
        # return TokenResponse(
        #     access_token=access_token,
        #     token_type="bearer",
        #     expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        #     user=UserResponse(
        #         user_id=user.user_id,
        #         name=user.name,
        #         email=user.email,
        #         created_at=user.created_at,
        #         last_login=user.last_login
        #     )
        # )

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
