from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv


# DB_USER = 'insight_stream_backend'
# DB_PASSWORD = '<password>'
# DB_HOST = 'localhost'
# DB_PORT = '3306'
# DB_DATABASE = 'ecommerce_research'

# Load environment variables
# Priority: .env.local (local dev) > .env (production/default)
backend_dir = Path(__file__).parent.parent
env_local = backend_dir / ".env.local"
env_default = backend_dir / ".env"

if env_local.exists():
    load_dotenv(dotenv_path=env_local)
else:
    load_dotenv(dotenv_path=env_default)

DB_USER = os.getenv('MYSQLUSER')
DB_PASSWORD = os.getenv('MYSQLPASSWORD')
DB_HOST = os.getenv('MYSQLHOST')
DB_PORT = os.getenv('MYSQLPORT')
DB_DATABASE = os.getenv('MYSQL_DATABASE')
MYSQL_PUBLIC_URL = os.getenv('MYSQL_PUBLIC_URL')

DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
print(f"MYSQL_PUBLIC_URL: {DB_URL}")
engine = create_engine(DB_URL,
                       pool_pre_ping=True,
                       pool_size=10,
                       max_overflow=20,  
                       echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    DB Session for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()