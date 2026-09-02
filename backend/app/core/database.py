import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

logger = logging.getLogger("bankassist.database")

# Build SQLAlchemy engine with resilience
database_url = settings.sqlalchemy_database_uri

try:
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url, connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info(f"Connected to database: {settings.MYSQL_DATABASE} at {settings.MYSQL_HOST}")
except Exception as e:
    logger.warning(
        f"Could not connect to primary MySQL database ({e}). "
        f"Falling back to local SQLite database for development."
    )
    fallback_url = "sqlite:///./data/bankassist_local.db"
    engine = create_engine(
        fallback_url, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
