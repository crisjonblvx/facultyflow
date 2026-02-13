"""
Student Edition Database Models
SQLAlchemy ORM models for student-specific tables.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Numeric, Time
)
from sqlalchemy.orm import relationship
from datetime import datetime, time

from database import Base


class StudentCourse(Base):
    """Student's enrolled Canvas courses"""
    __tablename__ = "student_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    canvas_course_id = Column(String(100), nullable=False)
    course_code = Column(String(100))
    course_name = Column(String(255), nullable=False)
    term = Column(String(100))
    current_grade_percentage = Column(Numeric(5, 2))
    current_grade_letter = Column(String(5))
    is_favorite = Column(Boolean, default=False)
    notification_level = Column(String(20), default='all')
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    announcements = relationship("StudentAnnouncement", back_populates="course")


class StudentAnnouncement(Base):
    """Canvas announcements stored per student"""
    __tablename__ = "student_announcements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("student_courses.id", ondelete="CASCADE"), nullable=False)
    canvas_announcement_id = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    urgency = Column(String(20), default='LOW')
    urgency_score = Column(Integer, default=0)
    read_status = Column(Boolean, default=False)
    read_at = Column(DateTime)
    pinned = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=False)
    posted_by_name = Column(String(255))
    canvas_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("StudentCourse", back_populates="announcements")


class StudentNotificationPreference(Base):
    """Per-user notification settings"""
    __tablename__ = "student_notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    push_enabled = Column(Boolean, default=True)
    email_urgent_enabled = Column(Boolean, default=True)
    digest_enabled = Column(Boolean, default=True)
    digest_time = Column(Time, default=time(8, 0))
    quiet_hours_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(Time, default=time(22, 0))
    quiet_hours_end = Column(Time, default=time(7, 0))
    quiet_hours_allow_urgent = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
