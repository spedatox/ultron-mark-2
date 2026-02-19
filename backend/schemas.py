from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Preference Schemas ---
class PreferenceBase(BaseModel):
    wake_time: str = "08:00"
    sleep_time: str = "23:00"
    study_block_length: int = 50
    max_study_minutes_per_day: int = 240
    commute_duration_mins: int = 90
    dinner_time: str = "20:00"

class PreferenceCreate(PreferenceBase):
    pass

class Preference(PreferenceBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- StudyBlock Schemas ---
class StudyBlockBase(BaseModel):
    start_time: datetime
    end_time: datetime
    google_event_id: Optional[str] = None

class StudyBlockCreate(StudyBlockBase):
    pass

class StudyBlock(StudyBlockBase):
    id: int
    task_id: int

    class Config:
        from_attributes = True

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    course_tag: Optional[str] = None
    total_required_time: int
    deadline: Optional[datetime] = None  # Made optional - will default to end of day if not provided
    priority: str = "normal"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    course_tag: Optional[str] = None
    total_required_time: Optional[int] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = None
    is_completed: Optional[bool] = None

class Task(TaskBase):
    id: int
    user_id: int
    is_completed: bool
    scheduled_minutes: int
    status: str
    study_blocks: List[StudyBlock] = []

    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    preferences: Optional[Preference] = None
    tasks: List[Task] = []

    class Config:
        from_attributes = True

# --- Fixed Schedule Schemas ---
class FixedScheduleBase(BaseModel):
    title: str
    category: str = "university" # university, work
    day_of_week: str
    start_time: str
    end_time: str

class FixedScheduleCreate(FixedScheduleBase):
    pass

class FixedSchedule(FixedScheduleBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
