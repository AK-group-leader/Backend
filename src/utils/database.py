"""
Database utilities and connection management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging

from src.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


async def init_database():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db():
    """Get database session"""
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
