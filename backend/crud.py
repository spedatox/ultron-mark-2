from sqlalchemy.orm import Session
import models, schemas
from datetime import datetime

# --- User ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.email + "notreallyhashed"
    db_user = models.User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Create default preferences
    default_pref = models.Preference(user_id=db_user.id)
    db.add(default_pref)
    db.commit()
    return db_user

def update_user_token(db: Session, user_id: int, token_json: str):
    """Updates the user's Google token after a refresh."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.google_token = token_json
        db.commit()
        db.refresh(user)
    return user

# --- Preferences ---
def get_preferences(db: Session, user_id: int):
    return db.query(models.Preference).filter(models.Preference.user_id == user_id).first()

def update_preferences(db: Session, user_id: int, preferences: schemas.PreferenceCreate):
    db_pref = db.query(models.Preference).filter(models.Preference.user_id == user_id).first()
    if db_pref:
        db_pref.wake_time = preferences.wake_time
        db_pref.sleep_time = preferences.sleep_time
        db_pref.study_block_length = preferences.study_block_length
        db_pref.max_study_minutes_per_day = preferences.max_study_minutes_per_day
        db_pref.commute_duration_mins = preferences.commute_duration_mins
        db_pref.dinner_time = preferences.dinner_time
        db.commit()
        db.refresh(db_pref)
    return db_pref

def update_user_token(db: Session, user_id: int, token: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.google_token = token
        db.commit()
        db.refresh(db_user)
    return db_user

# --- Tasks ---
def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Task).filter(models.Task.user_id == user_id).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    db_task = models.Task(**task.dict(), user_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return None
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

# --- Chat Sessions ---
def get_chat_sessions(db: Session, user_id: int, limit: int = 50):
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id).order_by(models.ChatSession.updated_at.desc()).limit(limit).all()

def get_chat_session(db: Session, session_id: int):
    return db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()

def create_chat_session(db: Session, user_id: int, title: str = "New Chat"):
    db_session = models.ChatSession(user_id=user_id, title=title)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def update_chat_session_title(db: Session, session_id: int, title: str):
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if db_session:
        db_session.title = title
        db.commit()
        db.refresh(db_session)
    return db_session

def delete_chat_session(db: Session, session_id: int):
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return True

def clear_all_chat_history(db: Session, user_id: int):
    """Delete all chat sessions and messages for a user."""
    # Get all sessions for the user
    sessions = db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id).all()
    count = len(sessions)
    
    # Delete all sessions (messages will be cascade deleted if FK is set up, otherwise delete manually)
    for session in sessions:
        # Delete messages first
        db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session.id).delete()
        db.delete(session)
    
    db.commit()
    return count

def add_chat_message(db: Session, session_id: int, role: str, content: str, attachment_url: str = None, attachment_type: str = None):
    db_msg = models.ChatMessage(
        session_id=session_id, 
        role=role, 
        content=content,
        attachment_url=attachment_url,
        attachment_type=attachment_type
    )
    db.add(db_msg)
    
    # Update session timestamp
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if db_session:
        db_session.updated_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_msg)
    return db_msg

def get_chat_messages(db: Session, session_id: int):
    return db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.timestamp.asc()).all()

# --- Fixed Schedule ---
def get_fixed_schedules(db: Session, user_id: int):
    return db.query(models.FixedSchedule).filter(models.FixedSchedule.user_id == user_id).all()

def create_fixed_schedule(db: Session, schedule: schemas.FixedScheduleCreate, user_id: int):
    db_schedule = models.FixedSchedule(**schedule.dict(), user_id=user_id)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def delete_fixed_schedule(db: Session, schedule_id: int):
    db_schedule = db.query(models.FixedSchedule).filter(models.FixedSchedule.id == schedule_id).first()
    if db_schedule:
        db.delete(db_schedule)
        db.commit()
    return db_schedule

# --- Study Blocks ---
def get_study_block(db: Session, block_id: int):
    return db.query(models.StudyBlock).filter(models.StudyBlock.id == block_id).first()

def get_study_blocks_for_task(db: Session, task_id: int):
    return db.query(models.StudyBlock).filter(models.StudyBlock.task_id == task_id).all()


# --- Daily Overrides ---
def get_daily_overrides(db: Session, user_id: int, date: str = None):
    """Get overrides for a user, optionally filtered by date (YYYY-MM-DD)"""
    query = db.query(models.DailyOverride).filter(models.DailyOverride.user_id == user_id)
    if date:
        query = query.filter(models.DailyOverride.date == date)
    return query.all()

def set_daily_override(db: Session, user_id: int, date: str, override_type: str, value: str, note: str = None):
    """Set or update a daily override for a specific date"""
    # Check if override already exists for this date and type
    existing = db.query(models.DailyOverride).filter(
        models.DailyOverride.user_id == user_id,
        models.DailyOverride.date == date,
        models.DailyOverride.override_type == override_type
    ).first()
    
    if existing:
        existing.value = value
        existing.note = note
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_override = models.DailyOverride(
            user_id=user_id,
            date=date,
            override_type=override_type,
            value=value,
            note=note
        )
        db.add(new_override)
        db.commit()
        db.refresh(new_override)
        return new_override

def delete_daily_override(db: Session, override_id: int):
    """Delete a daily override"""
    override = db.query(models.DailyOverride).filter(models.DailyOverride.id == override_id).first()
    if override:
        db.delete(override)
        db.commit()
    return override

def clear_daily_overrides_for_date(db: Session, user_id: int, date: str):
    """Clear all overrides for a specific date"""
    db.query(models.DailyOverride).filter(
        models.DailyOverride.user_id == user_id,
        models.DailyOverride.date == date
    ).delete()
    db.commit()

