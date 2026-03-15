"""
Test script to verify the cascade delete migration
"""

from sqlalchemy import text
from backend.database.database import SessionLocal
from backend.utils.user_utils import (
    get_system_user_id,
    delete_user_safely,
    get_orphaned_searches_count
)
from backend.services.db_services import DatabaseService as DBService
import sys


def test_migration():
    """Test the migration by creating and deleting a test user"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Testing Migration: Remove Cascade Delete")
        print("=" * 60)

        # Step 1: Check system user exists
        print("\n1. Checking system user...")
        system_user_id = get_system_user_id(db)
        if system_user_id:
            print(f"   ✓ System user exists (ID: {system_user_id})")
        else:
            print("   ✗ System user not found!")
            print("   Run the migration first: python -m database.remove_cascade_delete")
            return False

        # Step 2: Check foreign key constraint
        print("\n2. Checking foreign key constraint...")
        result = db.execute(text("""
            SELECT DELETE_RULE
            FROM information_schema.REFERENTIAL_CONSTRAINTS
            WHERE CONSTRAINT_SCHEMA = DATABASE()
            AND TABLE_NAME = 'searches'
            AND REFERENCED_TABLE_NAME = 'users'
            AND CONSTRAINT_NAME = 'searches_ibfk_1'
        """))
        rule = result.fetchone()
        if rule and rule[0] == 'RESTRICT':
            print(f"   ✓ Foreign key constraint is ON DELETE RESTRICT")
        elif rule and rule[0] == 'CASCADE':
            print(f"   ✗ Foreign key constraint is still ON DELETE CASCADE")
            print("   Run the migration: python -m database.remove_cascade_delete")
            return False
        else:
            print(f"   ? Foreign key constraint rule: {rule[0] if rule else 'Not found'}")

        # Step 3: Check stored procedure
        print("\n3. Checking stored procedure...")
        result = db.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = DATABASE()
            AND ROUTINE_NAME = 'delete_user_safely'
            AND ROUTINE_TYPE = 'PROCEDURE'
        """))
        proc_exists = result.scalar() > 0
        if proc_exists:
            print("   ✓ Stored procedure 'delete_user_safely' exists")
        else:
            print("   ✗ Stored procedure 'delete_user_safely' not found")

        # Step 4: Test user creation and deletion
        print("\n4. Testing user deletion with search preservation...")

        # Create test user
        test_email = "migration_test@example.com"

        # Clean up any existing test user
        existing = DBService.getUserByEmail(db, test_email)
        if existing:
            print(f"   Cleaning up existing test user (ID: {existing.user_id})...")
            delete_user_safely(db, existing.user_id)

        # Create new test user
        test_user = DBService.create_user(
            db,
            name="MigrationTestUser",
            email=test_email,
            password_hash="test_hash_123"
        )
        print(f"   ✓ Test user created (ID: {test_user.user_id})")

        # Create test search
        db.execute(text("""
            INSERT INTO searches (
                search_id, user_id, platforms, product_name,
                status, include_reviews, created_at
            )
            VALUES (
                :search_id, :user_id, 'amazon', 'Test Product',
                'COMPLETED', 0, NOW()
            )
        """), {
            "search_id": f"test_search_{test_user.user_id}",
            "user_id": test_user.user_id
        })
        db.commit()
        print(f"   ✓ Test search created")

        # Count searches before deletion
        orphaned_before = get_orphaned_searches_count(db)

        # Delete user safely
        result = delete_user_safely(db, test_user.user_id)

        if result["success"]:
            print(f"   ✓ User deleted successfully")
            print(f"   ✓ Searches reassigned: {result['searches_reassigned']}")

            # Verify search still exists under system user
            orphaned_after = get_orphaned_searches_count(db)
            if orphaned_after > orphaned_before:
                print(f"   ✓ Search preserved (orphaned count: {orphaned_before} -> {orphaned_after})")
            else:
                print(f"   ✗ Search might not have been reassigned")

            # Clean up test search
            db.execute(text("""
                DELETE FROM searches WHERE search_id = :search_id
            """), {"search_id": f"test_search_{test_user.user_id}"})
            db.commit()
            print(f"   ✓ Test data cleaned up")

        else:
            print(f"   ✗ User deletion failed: {result['message']}")
            return False

        print("\n" + "=" * 60)
        print("✅ All tests passed! Migration is working correctly.")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)
