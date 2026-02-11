"""
Database Models for FacultyFlow v2.0
SQLAlchemy models for Canvas integration

Built for: FacultyFlow v2.0
Database: PostgreSQL (Railway)
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Railway uses postgres://, but SQLAlchemy needs postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()


class CanvasCredentials(Base):
    """
    Stores encrypted Canvas API credentials for each user
    """
    __tablename__ = "canvas_credentials"

    user_id = Column(Integer, primary_key=True, index=True)
    canvas_url = Column(String(255), nullable=False)
    access_token_encrypted = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, default=datetime.utcnow)

    # Relationship to courses
    courses = relationship("UserCourse", back_populates="canvas_account")


class UserCourse(Base):
    """
    Stores cached course data from Canvas
    """
    __tablename__ = "user_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("canvas_credentials.user_id"), nullable=False)
    course_id = Column(Integer, nullable=False)  # Canvas course ID
    course_name = Column(String(255), nullable=False)
    course_code = Column(String(100))
    total_students = Column(Integer)
    synced_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to canvas credentials
    canvas_account = relationship("CanvasCredentials", back_populates="courses")


def init_db():
    """
    Initialize database tables
    Call this on app startup
    """
    if engine:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
    else:
        print("⚠️  No DATABASE_URL - running without database")


def get_db():
    """
    Get database session
    Use as dependency in FastAPI endpoints
    """
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None
