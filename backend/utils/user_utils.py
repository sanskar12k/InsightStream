"""
User utility functions for safe user management
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

SYSTEM_USER_EMAIL = "deleted@system.internal"
SYSTEM_USER_NAME = "DeletedUser"


def get_system_user_id(db: Session) -> Optional[int]:
    """
    Get the system user ID for orphaned searches.

    Args:
        db: Database session

    Returns:
        System user ID or None if not found
    """
    try:
        result = db.execute(
            text("SELECT user_id FROM users WHERE email = :email"),
            {"email": SYSTEM_USER_EMAIL}
        )
        row = result.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error getting system user ID: {e}")
        return None


def create_system_user(db: Session) -> int:
    """
    Create the system user if it doesn't exist.

    Args:
        db: Database session

    Returns:
        System user ID
    """
    try:
        # Check if system user exists
        existing_id = get_system_user_id(db)
        if existing_id:
            return existing_id

        # Create system user
        db.execute(
            text("""
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (:name, :email, :password_hash, NOW())
            """),
            {
                "name": SYSTEM_USER_NAME,
                "email": SYSTEM_USER_EMAIL,
                "password_hash": "$2b$12$SYSTEM_USER_NO_LOGIN_ALLOWED"
            }
        )
        db.commit()

        # Get the created user ID
        return get_system_user_id(db)
    except Exception as e:
        logger.error(f"Error creating system user: {e}")
        db.rollback()
        raise


def delete_user_safely(db: Session, user_id: int) -> Dict[str, any]:
    """
    Safely delete a user by reassigning their searches to the system user.

    This function:
    1. Reassigns all of the user's searches to the system user
    2. Deletes the user record
    3. Returns information about the operation

    Args:
        db: Database session
        user_id: ID of the user to delete

    Returns:
        Dictionary with operation results:
        {
            "success": bool,
            "user_id": int,
            "searches_reassigned": int,
            "message": str
        }
    """
    try:
        # Ensure system user exists
        system_user_id = get_system_user_id(db)
        if not system_user_id:
            system_user_id = create_system_user(db)

        # Count searches before reassignment
        count_result = db.execute(
            text("SELECT COUNT(*) FROM searches WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        search_count = count_result.scalar()

        # Reassign searches to system user
        db.execute(
            text("UPDATE searches SET user_id = :system_user WHERE user_id = :target_user"),
            {"system_user": system_user_id, "target_user": user_id}
        )

        # Delete the user
        result = db.execute(
            text("DELETE FROM users WHERE user_id = :user_id"),
            {"user_id": user_id}
        )

        db.commit()

        return {
            "success": True,
            "user_id": user_id,
            "searches_reassigned": search_count,
            "message": f"User {user_id} deleted successfully. {search_count} searches reassigned to system user."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        return {
            "success": False,
            "user_id": user_id,
            "searches_reassigned": 0,
            "message": f"Failed to delete user: {str(e)}"
        }


def delete_user_with_procedure(db: Session, user_id: int) -> Dict[str, any]:
    """
    Delete a user using the stored procedure (alternative method).

    Args:
        db: Database session
        user_id: ID of the user to delete

    Returns:
        Dictionary with operation results
    """
    try:
        result = db.execute(
            text("CALL delete_user_safely(:user_id)"),
            {"user_id": user_id}
        )
        db.commit()

        return {
            "success": True,
            "user_id": user_id,
            "message": "User deleted successfully using stored procedure"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id} with procedure: {e}")
        return {
            "success": False,
            "user_id": user_id,
            "message": f"Failed to delete user: {str(e)}"
        }


def get_orphaned_searches_count(db: Session) -> int:
    """
    Get the count of searches owned by the system user (orphaned searches).

    Args:
        db: Database session

    Returns:
        Count of orphaned searches
    """
    try:
        system_user_id = get_system_user_id(db)
        if not system_user_id:
            return 0

        result = db.execute(
            text("SELECT COUNT(*) FROM searches WHERE user_id = :system_user"),
            {"system_user": system_user_id}
        )
        return result.scalar()

    except Exception as e:
        logger.error(f"Error getting orphaned searches count: {e}")
        return 0


def reassign_searches(db: Session, from_user_id: int, to_user_id: int) -> Dict[str, any]:
    """
    Reassign searches from one user to another.

    Args:
        db: Database session
        from_user_id: Source user ID
        to_user_id: Target user ID

    Returns:
        Dictionary with operation results
    """
    try:
        # Count searches to be reassigned
        count_result = db.execute(
            text("SELECT COUNT(*) FROM searches WHERE user_id = :from_user"),
            {"from_user": from_user_id}
        )
        count = count_result.scalar()

        # Reassign searches
        db.execute(
            text("UPDATE searches SET user_id = :to_user WHERE user_id = :from_user"),
            {"to_user": to_user_id, "from_user": from_user_id}
        )
        db.commit()

        return {
            "success": True,
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "searches_reassigned": count,
            "message": f"Successfully reassigned {count} searches"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error reassigning searches: {e}")
        return {
            "success": False,
            "message": f"Failed to reassign searches: {str(e)}"
        }
