# I want to test db connection, so I will create a simple script to test the connection to the database using the same configuration as in the database.py file.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# write a test script to verify the database connection
def test_db_connection():
    DB_USER = 'insight_stream_backend'
    DB_PASSWORD = 'backend20260220'
    DB_HOST = 'interchange.proxy.rlwy.net'
    DB_PORT = '24819'
    DB_DATABASE = 'insight_stream'

    DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
    print(f"Testing database connection with URL: {DB_URL}")
    try:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text('SHOW TABLES'))  # Simple query to test the connection
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db_connection()
