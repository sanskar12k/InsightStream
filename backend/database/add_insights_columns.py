"""
Database migration script to add new columns to the searches table:
- total_products_scraped: Integer field to track the actual number of products scraped
- insight_generated: Boolean field to track if insights have been generated
- auto_generate_insights: Boolean field to track if insights should be auto-generated

Run this script to update the database schema.
"""

from sqlalchemy import create_engine, Column, Integer, text
from backend.config import setting

def add_columns_to_searches():
    """
    Add new columns to the searches table if they don't exist.
    """
    engine = create_engine(setting.DATABASE_URL)

    with engine.connect() as connection:
        # Start a transaction
        trans = connection.begin()

        try:
            # Check if columns exist and add them if they don't
            print("Adding new columns to searches table...")

            # Add total_products_scraped column
            try:
                connection.execute(text(
                    "ALTER TABLE searches ADD COLUMN total_products_scraped INTEGER DEFAULT 0"
                ))
                print("✓ Added total_products_scraped column")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("- total_products_scraped column already exists")
                else:
                    raise

            # Add insight_generated column
            try:
                connection.execute(text(
                    "ALTER TABLE searches ADD COLUMN insight_generated INTEGER DEFAULT 0 NOT NULL"
                ))
                print("✓ Added insight_generated column")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("- insight_generated column already exists")
                else:
                    raise

            # Add auto_generate_insights column
            try:
                connection.execute(text(
                    "ALTER TABLE searches ADD COLUMN auto_generate_insights INTEGER DEFAULT 0 NOT NULL"
                ))
                print("✓ Added auto_generate_insights column")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("- auto_generate_insights column already exists")
                else:
                    raise

            # Commit the transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")

        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Insights Columns")
    print("=" * 60)
    print()

    try:
        add_columns_to_searches()
    except Exception as e:
        print(f"\nError: {e}")
        exit(1)

    print("\nMigration script completed.")
    print("=" * 60)
