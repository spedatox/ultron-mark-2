import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, schemas, crud

db = SessionLocal()

# Clear existing schedules to avoid duplicates
db.query(models.FixedSchedule).delete()
db.commit()

# Assuming user ID 1 (default)
user = db.query(models.User).first()
if not user:
    print("No user found. Creating default user.")
    user = crud.create_user(db, schemas.UserCreate(email="user@example.com"))
user_id = user.id

uni_schedule = [
    # Monday
    {"title": "MIS 131 - YBS", "day_of_week": "Monday", "start_time": "09:00", "end_time": "11:50", "category": "university"},
    {"title": "IUL 151 - Univ. Giris", "day_of_week": "Monday", "start_time": "16:00", "end_time": "17:50", "category": "university"},
    {"title": "EHS 101 - Is Sagligi", "day_of_week": "Monday", "start_time": "18:00", "end_time": "19:50", "category": "university"},
    
    # Tuesday
    {"title": "MIS 141 - Matematik I", "day_of_week": "Tuesday", "start_time": "15:00", "end_time": "17:50", "category": "university"},
    
    # Wednesday
    {"title": "MIS 103 - Yonetim Org.", "day_of_week": "Wednesday", "start_time": "09:00", "end_time": "11:50", "category": "university"},
    {"title": "MIS 105 - Temel Bil. Bil.", "day_of_week": "Wednesday", "start_time": "13:00", "end_time": "14:50", "category": "university"},
    
    # Thursday
    {"title": "EPR 121 - Girisimcilik", "day_of_week": "Thursday", "start_time": "09:00", "end_time": "10:50", "category": "university"},
    {"title": "MIS 111 - Prog. Temelleri", "day_of_week": "Thursday", "start_time": "12:00", "end_time": "15:50", "category": "university"},
]

work_schedule = [
    {"title": "Work", "day_of_week": "Monday", "start_time": "13:30", "end_time": "17:00", "category": "work"},
    {"title": "Work", "day_of_week": "Tuesday", "start_time": "13:30", "end_time": "15:00", "category": "work"},
    {"title": "Work", "day_of_week": "Wednesday", "start_time": "15:00", "end_time": "17:00", "category": "work"},
    {"title": "Work", "day_of_week": "Friday", "start_time": "09:00", "end_time": "17:00", "category": "work"},
]

print("Importing University Schedule...")
for item in uni_schedule:
    sched = schemas.FixedScheduleCreate(**item)
    crud.create_fixed_schedule(db, sched, user_id)

print("Importing Work Schedule...")
for item in work_schedule:
    sched = schemas.FixedScheduleCreate(**item)
    crud.create_fixed_schedule(db, sched, user_id)

print("Import completed successfully.")
