"""
Database utilities and connection management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException
import logging

from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database setup - only if DATABASE_URL is provided
if settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    engine = None
    SessionLocal = None
    Base = declarative_base()


async def init_database():
    """Initialize database tables"""
    settings = get_settings()

    # If no DATABASE_URL is configured, use Databricks as primary database
    if not settings.DATABASE_URL:
        logger.info(
            "No DATABASE_URL configured - using Databricks as primary database")
        return

    try:
        # Test database connection first
        with engine.connect() as connection:
            connection.execute("SELECT 1")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {str(e)}")
        logger.warning(
            "Running in database-disconnected mode (using Databricks)")
        # Don't raise the exception, allow the server to start without database


def get_db():
    """Get database session"""
    if not SessionLocal:
        raise HTTPException(
            status_code=503,
            detail="Database not configured - using Databricks as primary database"
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database models will be defined here
# Example:
# class AnalysisResult(Base):
#     __tablename__ = "analysis_results"
#
#     id = Column(Integer, primary_key=True, index=True)
#     analysis_id = Column(String, unique=True, index=True)
#     coordinates = Column(JSON)
#     results = Column(JSON)
#     created_at = Column(DateTime, default=datetime.utcnow)
