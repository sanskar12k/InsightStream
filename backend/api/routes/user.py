import hashlib
from requests import Session
from backend.auth.jwt_auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, get_current_user_id, hash_password, validate_password_strength, verify_password
from backend.database.database import SessionLocal, get_db
from backend.models.db_models import Status, AuthProvider
from backend.models.scrapper_models import ScrapperRequest, ScrapperResponse, ScrapperStatus
from backend.models.user_models import TokenResponse, UserCreate, UserLogin, UserLoginResponse, UserResponse, UserUpdatePassword
from fastapi import APIRouter,BackgroundTasks, HTTPException, status, Depends
from pydantic import BaseModel
from backend.services.db_services import DatabaseService as DBService
from backend.utils.user_utils import delete_user_safely
router = APIRouter(
    prefix="/users",
    tags=["scrapper"],
    responses={404: {"description": "Not found"}},
)


# def hash_password(password: str) -> str:
#     """Hash a password using SHA256"""
#     return hashlib.sha256(password.encode()).hexdigest()

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password against its hash"""
#     return hash_password(plain_password) == hashed_password

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **name**: Unique username (3-50 characters)
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 6 characters)
    
    Returns the created user data (without password)
    """
    # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjUsImV4cCI6MTc3MzA4MDg3NCwiaWF0IjoxNzcyOTk0NDc0fQ._6Ih3qc-tbt0ttD9na5cdJ0gzz5HkXI6xYmEwjo2oDg
    # try:
    #     validate_password_strength(user_data.password)
    # except ValueError as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=str(e)
        # )
    
    existing_user = DBService.getUserByEmail(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        hashed_password = hash_password(user_data.password)
        new_user = DBService.create_user(db, name=user_data.name, email=user_data.email, password_hash=hashed_password)
        access_token = create_access_token(
            data={"sub": str(new_user.user_id)}
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                user_id=new_user.user_id,
                name=new_user.name,
                email=new_user.email,
                created_at=new_user.created_at
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login user with email and password

    - **email**: User's email address
    - **password**: User's password

    Returns user data on successful login
    """
    print(f"DEBUG: Login attempt for email: {user_data.email}")
    user = DBService.getUserByEmail(db, user_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})

    # Check if user registered via OAuth and has no password set
    if user.password_hash is None or user.password_hash == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account was created using {user.auth_provider.value} login. Please sign in with {user.auth_provider.value} or set a password first."
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        DBService.update_last_login(db, user.user_id)
        # token = create_jwt_token(user.user_id)
        access_token= create_access_token(
            data={"sub": str(user.user_id)}
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )
    
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user's information
    
    Requires: Valid JWT token in Authorization header
    
    Returns user data of the authenticated user
    """
    return UserResponse(
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/id/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Get user by ID
    
    Returns user data (without password)
    """
    user = DBService.getUserById(db, int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        x=user.last_login
    )

@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """
    Get user by email address
    
    Returns user data (without password)
    """
    user = DBService.getUserByEmail(db, email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        last_login=user.last_login
    )

@router.post("/password/set", status_code=status.HTTP_200_OK)
async def set_password(
    new_password: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set password for OAuth users who don't have one yet

    Requires: Valid JWT token in Authorization header

    - **new_password**: New password to set
    """

    # Check if user already has a password
    if current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a password set. Use /password endpoint to update it."
        )

    # Validate password strength
    try:
        validate_password_strength(new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    try:
        # Set password
        new_password_hash = hash_password(new_password)
        DBService.update_user_password(db, current_user.user_id, new_password_hash)

        return {
            "message": "Password set successfully. You can now login with email and password.",
            "user_id": current_user.user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting password: {str(e)}"
        )

@router.put("/password", status_code=status.HTTP_200_OK)
async def update_password(
    password_data: UserUpdatePassword,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's password

    Requires: Valid JWT token in Authorization header

    - **old_password**: Current password (for verification)
    - **new_password**: New password (min 8 chars, requires uppercase, lowercase, and number)
    """

    # Check if user has no password (OAuth user)
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You don't have a password set yet. Use /password/set endpoint first."
        )

    # ==================== VALIDATE PASSWORD STRENGTH ====================
    try:
        validate_password_strength(password_data.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # ==================== VERIFY OLD PASSWORD ====================
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    try:
        # ==================== UPDATE PASSWORD ====================
        new_password_hash = hash_password(password_data.new_password)
        DBService.update_user_password(db, current_user.user_id, new_password_hash)

        return {
            "message": "Password updated successfully",
            "user_id": current_user.user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating password: {str(e)}"
        )

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's account

    Requires: Valid JWT token in Authorization header

    Note: User's searches will be preserved and reassigned to a system user
    """
    result = delete_user_safely(db, current_user.user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

    return {
        "message": result["message"],
        "searches_reassigned": result["searches_reassigned"]
    }

@router.get("/")
async def list_users(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    List all users (paginated)
    
    Requires: Valid JWT token in Authorization header
    
    - **limit**: Number of users to return (default: 10, max: 100)
    - **offset**: Number of users to skip (for pagination)
    """
    if limit > 100:
        limit = 100
    
    users = DBService.get_all_users(db, limit, offset)
    
    return {
        "total_returned": len(users),
        "limit": limit,
        "offset": offset,
        "users": [
            {
                "user_id": u.user_id,
                "name": u.name,
                "email": u.email,
                "created_at": u.created_at,
                "last_login": u.last_login
            }
            for u in users
        ]
    }

@router.put("/{user_id}/password", status_code=status.HTTP_200_OK)
async def update_user_password_by_id(
    user_id: int,
    password_data: UserUpdatePassword,
    db: Session = Depends(get_db)
):
    """
    Update user password by user ID

    - **old_password**: Current password (for verification)
    - **new_password**: New password (minimum 6 characters)
    """

    # ==================== GET USER ====================
    user = DBService.getUserById(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Check if user has no password (OAuth user)
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user has no password set (OAuth account). Cannot update non-existent password."
        )

    # ==================== VERIFY OLD PASSWORD ====================
    if not verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    try:
        # ==================== UPDATE PASSWORD ====================
        new_password_hash = hash_password(password_data.new_password)
        DBService.update_user_password(db, user_id, new_password_hash)

        return {
            "message": "Password updated successfully",
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating password: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user account

    Note: User's searches will be preserved and reassigned to a system user
    """
    user = DBService.getUserById(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    result = delete_user_safely(db, user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

    return {
        "message": result["message"],
        "searches_reassigned": result["searches_reassigned"]
    }

@router.get("/")
async def list_users(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all users (paginated)
    
    - **limit**: Number of users to return (default: 10, max: 100)
    - **offset**: Number of users to skip (for pagination)
    """
    if limit > 100:
        limit = 100
    
    users = DBService.get_all_users(db, limit, offset)
    
    return {
        "total_returned": len(users),
        "limit": limit,
        "offset": offset,
        "users": [
            {
                "user_id": u.user_id,
                "name": u.name,
                "email": u.email,
                "created_at": u.created_at,
                "last_login": u.last_login
            }
            for u in users
        ]
    }

@router.get("/get_all_user")
async def list_users(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all users (paginated)
    
    - **limit**: Number of users to return (default: 10, max: 100)
    - **offset**: Number of users to skip (for pagination)
    """
    if limit > 100:
        limit = 100
    
    users = DBService.get_all_users(db, limit, offset)
    
    return {
        "total_returned": len(users),
        "limit": limit,
        "offset": offset,
        "users": [
            {
                "user_id": u.user_id,
                "name": u.name,
                "email": u.email,
                "created_at": u.created_at,
                "last_login": u.last_login
            }
            for u in users
        ]
    }