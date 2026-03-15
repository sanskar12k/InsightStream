# Database Migration: Remove Cascade Delete from Searches

## Overview

This migration removes the `ON DELETE CASCADE` behavior from the `searches` table foreign key constraint. When a user is deleted, their searches will now be **preserved** and automatically reassigned to a system user instead of being deleted.

## Why This Change?

**Before:**
- When a user was deleted, all their searches were automatically deleted (`ON DELETE CASCADE`)
- This resulted in data loss and made it impossible to maintain search history

**After:**
- When a user is deleted, their searches are preserved
- Searches are reassigned to a special system user ("DeletedUser")
- No search data is lost
- User deletion is handled safely with automatic reassignment

## Files Changed/Added

### New Files
1. **`backend/database/remove_cascade_delete.py`** - Migration script
2. **`backend/utils/user_utils.py`** - User management utilities
3. **`backend/database/MIGRATION_README.md`** - This documentation

### Modified Files
1. **`backend/database/setup.sql`** - Updated for new installations
2. **`backend/api/routes/user.py`** - Updated delete endpoints
3. **`backend/models/db_models.py`** - No changes needed (SQLAlchemy handles this)

## How to Apply the Migration

### Step 1: Backup Your Database (IMPORTANT!)

```bash
# Backup the entire database
mysqldump -u your_user -p insight_stream > backup_before_migration.sql

# Or backup just the users and searches tables
mysqldump -u your_user -p insight_stream users searches > backup_users_searches.sql
```

### Step 2: Run the Migration

```bash
# Navigate to the backend directory
cd backend

# Run the migration
python -m database.remove_cascade_delete

# Expected output:
# Starting migration: Remove CASCADE delete from searches...
#
# 1. Creating system user for orphaned searches...
#    ✓ System user created/verified
#    ✓ System user ID: X
#
# 2. Dropping existing foreign key constraint with CASCADE...
#    ✓ Foreign key constraint dropped
#
# 3. Adding new foreign key constraint without CASCADE...
#    ✓ New foreign key constraint added (ON DELETE RESTRICT)
#
# 4. Creating stored procedure for user deletion...
#    ✓ Stored procedure 'delete_user_safely' created
#
# ✅ Migration completed successfully!
```

### Step 3: Verify the Migration

```bash
# Connect to MySQL
mysql -u your_user -p insight_stream

# Check the system user exists
SELECT user_id, name, email FROM users WHERE email = 'deleted@system.internal';

# Check the foreign key constraint
SHOW CREATE TABLE searches;
# Should show: ON DELETE RESTRICT (not CASCADE)

# Check the stored procedure exists
SHOW PROCEDURE STATUS WHERE Db = 'insight_stream' AND Name = 'delete_user_safely';
```

## How to Use After Migration

### Deleting Users via API

The API endpoints have been updated to automatically handle safe deletion:

```bash
# Delete current user (requires authentication)
DELETE /users/me

# Delete user by ID
DELETE /users/{user_id}

# Response will include:
{
    "message": "User X deleted successfully. Y searches reassigned to system user.",
    "searches_reassigned": Y
}
```

### Deleting Users Programmatically

```python
from backend.utils.user_utils import delete_user_safely
from backend.database.database import SessionLocal

db = SessionLocal()

# Safe deletion with automatic search reassignment
result = delete_user_safely(db, user_id=5)

if result["success"]:
    print(f"User deleted: {result['message']}")
    print(f"Searches reassigned: {result['searches_reassigned']}")
else:
    print(f"Error: {result['message']}")
```

### Using the Stored Procedure (MySQL)

```sql
-- Delete a user safely (reassigns searches automatically)
CALL delete_user_safely(5);

-- Check orphaned searches
SELECT COUNT(*)
FROM searches
WHERE user_id = (SELECT user_id FROM users WHERE email = 'deleted@system.internal');
```

## Additional Utility Functions

The `backend/utils/user_utils.py` module provides several helpful functions:

```python
from backend.utils.user_utils import (
    get_system_user_id,
    create_system_user,
    delete_user_safely,
    get_orphaned_searches_count,
    reassign_searches
)

# Get system user ID
system_id = get_system_user_id(db)

# Count orphaned searches
orphaned_count = get_orphaned_searches_count(db)

# Manually reassign searches between users
result = reassign_searches(db, from_user_id=5, to_user_id=3)
```

## Rollback Instructions

If you need to rollback this migration:

```bash
# Run the migration with --rollback flag
python -m database.remove_cascade_delete --rollback

# This will:
# - Remove the stored procedure
# - Restore ON DELETE CASCADE behavior
```

⚠️ **Warning:** Rolling back will restore the cascade delete behavior, meaning future user deletions will delete their searches.

## System User Details

**Email:** `deleted@system.internal`
**Name:** `DeletedUser`
**Password:** Not accessible (uses invalid hash)
**Purpose:** Owns all searches from deleted users

This user cannot be used to log in and exists solely to maintain data integrity.

## Database Schema Changes

### Before
```sql
CONSTRAINT `searches_ibfk_1`
FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
ON DELETE CASCADE
```

### After
```sql
CONSTRAINT `searches_ibfk_1`
FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
ON DELETE RESTRICT
```

## Troubleshooting

### Error: "Cannot delete or update a parent row"

This means you're trying to delete a user with existing searches. Use the safe deletion methods:

```python
# Use this instead of db.delete(user)
delete_user_safely(db, user_id)
```

### Error: "System user not found"

Run the migration again or manually create the system user:

```sql
INSERT INTO users (name, email, password_hash, created_at)
VALUES (
    'DeletedUser',
    'deleted@system.internal',
    '$2b$12$SYSTEM_USER_NO_LOGIN_ALLOWED',
    NOW()
);
```

### Check Migration Status

```sql
-- Check if ON DELETE RESTRICT is applied
SELECT
    TABLE_NAME,
    CONSTRAINT_NAME,
    DELETE_RULE
FROM
    information_schema.REFERENTIAL_CONSTRAINTS
WHERE
    CONSTRAINT_SCHEMA = 'insight_stream'
    AND TABLE_NAME = 'searches'
    AND REFERENCED_TABLE_NAME = 'users';

-- Should show DELETE_RULE = 'RESTRICT'
```

## Testing the Migration

```python
# Test script to verify the migration
from backend.database.database import SessionLocal
from backend.utils.user_utils import delete_user_safely, get_orphaned_searches_count
from backend.services.db_services import DatabaseService as DBService

db = SessionLocal()

# Create a test user
test_user = DBService.create_user(
    db,
    name="TestUser",
    email="test@example.com",
    password_hash="test_hash"
)

# Create some searches for the test user
# ... create searches ...

# Count searches before deletion
search_count = db.execute(
    text("SELECT COUNT(*) FROM searches WHERE user_id = :uid"),
    {"uid": test_user.user_id}
).scalar()

print(f"Searches before deletion: {search_count}")

# Delete user safely
result = delete_user_safely(db, test_user.user_id)

print(f"Deletion result: {result}")

# Verify searches still exist
orphaned = get_orphaned_searches_count(db)
print(f"Orphaned searches: {orphaned}")

# Cleanup
db.close()
```

## Notes

- The migration is **idempotent** - you can run it multiple times safely
- Existing data is preserved during migration
- The system user will appear in user lists but cannot log in
- Search data maintains full integrity and relationships
- Consider filtering out the system user in user listings if desired

## Support

If you encounter issues with the migration:

1. Check the troubleshooting section above
2. Verify database connection settings in `.env`
3. Ensure you have proper database permissions
4. Check MySQL error logs for detailed error messages
5. Restore from backup if necessary

## Future Considerations

You may want to add:
- Admin interface to view/manage orphaned searches
- Bulk cleanup of old orphaned searches
- Analytics on deleted user patterns
- Option to permanently delete searches after X days
