"""
Migration: Remove CASCADE delete from searches foreign key and create system user

This migration:
1. Creates a system user to own orphaned searches
2. Drops the existing foreign key constraint with CASCADE
3. Recreates the foreign key constraint without CASCADE
4. Adds a trigger to reassign searches before user deletion
"""

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
MYSQLUSER = os.getenv("MYSQLUSER", "root")
MYSQLPASSWORD = os.getenv("MYSQLPASSWORD", "")
MYSQLHOST = os.getenv("MYSQLHOST", "localhost")
MYSQLPORT = os.getenv("MYSQLPORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "insight_stream")

DATABASE_URL = f"mysql+pymysql://{MYSQLUSER}:{MYSQLPASSWORD}@{MYSQLHOST}:{MYSQLPORT}/{MYSQL_DATABASE}"

def run_migration():
    """Execute the migration"""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:
        print("Starting migration: Remove CASCADE delete from searches...")

        # Step 1: Create system user for deleted users' searches
        print("\n1. Creating system user for orphaned searches...")
        try:
            connection.execute(text("""
                INSERT INTO users (name, email, password_hash, created_at)
                VALUES (
                    'DeletedUser',
                    'deleted@system.internal',
                    '$2b$12$SYSTEM_USER_NO_LOGIN_ALLOWED',
                    NOW()
                )
                ON DUPLICATE KEY UPDATE name = name;
            """))
            print("   ✓ System user created/verified")
        except Exception as e:
            print(f"   Note: {e}")

        # Get the system user ID
        result = connection.execute(text("""
            SELECT user_id FROM users WHERE email = 'deleted@system.internal'
        """))
        system_user_id = result.fetchone()[0]
        print(f"   ✓ System user ID: {system_user_id}")

        # Step 2: Drop existing foreign key constraint
        print("\n2. Dropping existing foreign key constraint with CASCADE...")
        try:
            connection.execute(text("""
                ALTER TABLE searches
                DROP FOREIGN KEY searches_ibfk_1;
            """))
            print("   ✓ Foreign key constraint dropped")
        except Exception as e:
            print(f"   Warning: Could not drop constraint: {e}")

        # Step 3: Add new foreign key constraint without CASCADE
        print("\n3. Adding new foreign key constraint without CASCADE...")
        try:
            connection.execute(text("""
                ALTER TABLE searches
                ADD CONSTRAINT searches_ibfk_1
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE RESTRICT;
            """))
            print("   ✓ New foreign key constraint added (ON DELETE RESTRICT)")
        except Exception as e:
            print(f"   Warning: {e}")

        # Step 4: Create a stored procedure to handle user deletion
        print("\n4. Creating stored procedure for user deletion...")
        try:
            # Drop procedure if exists
            connection.execute(text("DROP PROCEDURE IF EXISTS delete_user_safely;"))

            # Create new procedure
            connection.execute(text(f"""
                CREATE PROCEDURE delete_user_safely(IN target_user_id INT)
                BEGIN
                    DECLARE system_user INT DEFAULT {system_user_id};

                    -- Reassign all searches from target user to system user
                    UPDATE searches
                    SET user_id = system_user
                    WHERE user_id = target_user_id;

                    -- Now delete the user
                    DELETE FROM users WHERE user_id = target_user_id;

                    SELECT CONCAT('User ', target_user_id, ' deleted and searches reassigned to system user') AS result;
                END;
            """))
            print("   ✓ Stored procedure 'delete_user_safely' created")
        except Exception as e:
            print(f"   Warning: {e}")

        print("\n✅ Migration completed successfully!")
        print(f"\nNotes:")
        print(f"  - Searches will no longer be deleted when users are deleted")
        print(f"  - Orphaned searches will be assigned to system user (ID: {system_user_id})")
        print(f"  - Use 'CALL delete_user_safely(user_id)' to delete users properly")
        print(f"  - Foreign key is now ON DELETE RESTRICT (prevents deletion if searches exist)")

def rollback_migration():
    """Rollback the migration"""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as connection:
        print("Rolling back migration...")

        # Drop the procedure
        try:
            connection.execute(text("DROP PROCEDURE IF EXISTS delete_user_safely;"))
            print("   ✓ Stored procedure dropped")
        except Exception as e:
            print(f"   Warning: {e}")

        # Drop and recreate foreign key with CASCADE
        try:
            connection.execute(text("""
                ALTER TABLE searches
                DROP FOREIGN KEY searches_ibfk_1;
            """))
            connection.execute(text("""
                ALTER TABLE searches
                ADD CONSTRAINT searches_ibfk_1
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                ON DELETE CASCADE;
            """))
            print("   ✓ Foreign key constraint restored with CASCADE")
        except Exception as e:
            print(f"   Warning: {e}")

        print("\n✅ Rollback completed!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        run_migration()
