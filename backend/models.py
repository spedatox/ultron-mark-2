from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_token = Column(String, nullable=True) # Store OAuth token/credentials blob
    
    preferences = relationship("Preference", back_populates="user", uselist=False)
    tasks = relationship("Task", back_populates="user")
    fixed_schedules = relationship("FixedSchedule", back_populates="user")
    daily_overrides = relationship("DailyOverride", back_populates="user")

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    wake_time = Column(String, default="08:00") # HH:MM format
    sleep_time = Column(String, default="23:00") # HH:MM format
    study_block_length = Column(Integer, default=50) # in minutes
    max_study_minutes_per_day = Column(Integer, default=240) # e.g. 4 hours
    
    # New Constraints
    commute_duration_mins = Column(Integer, default=90) # Commute to Uni
    dinner_time = Column(String, default="20:00") # Must be back by this time
    
    user = relationship("User", back_populates="preferences")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String, index=True)
    course_tag = Column(String, nullable=True)
    total_required_time = Column(Integer) # in minutes
    deadline = Column(DateTime)
    priority = Column(String, default="normal") # normal, high
    is_completed = Column(Boolean, default=False)
    
    # Status tracking
    scheduled_minutes = Column(Integer, default=0)
    status = Column(String, default="pending") # pending, scheduled, underplanned, completed
    
    user = relationship("User", back_populates="tasks")
    study_blocks = relationship("StudyBlock", back_populates="task")

class StudyBlock(Base):
    __tablename__ = "study_blocks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    google_event_id = Column(String, nullable=True) # ID of the event in Google Calendar
    
    task = relationship("Task", back_populates="study_blocks")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String) # user, assistant, system
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # For file uploads (optional)
    attachment_url = Column(String, nullable=True)
    attachment_type = Column(String, nullable=True) # image, file
    
    session = relationship("ChatSession", back_populates="messages")

class FixedSchedule(Base):
    __tablename__ = "fixed_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String) # e.g. "Math 101", "Work"
    category = Column(String, default="university") # university, work, other
    day_of_week = Column(String) # Monday, Tuesday, etc.
    start_time = Column(String) # HH:MM
    end_time = Column(String) # HH:MM
    
    user = relationship("User", back_populates="fixed_schedules")


class DailyOverride(Base):
    """Temporary overrides for specific dates (e.g., leaving early, skipping commute)"""
    __tablename__ = "daily_overrides"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    date = Column(String)  # YYYY-MM-DD format
    override_type = Column(String)  # "departure_time", "skip_commute", "skip_dinner", "custom_wake"
    value = Column(String)  # e.g., "10:00" for departure time, "true" for skip
    note = Column(String, nullable=True)  # Optional note
    
    user = relationship("User", back_populates="daily_overrides")
