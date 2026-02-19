from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import scheduler, calendar_integration
import crud
import schemas
from typing import List

router = APIRouter(
    prefix="/schedule",
    tags=["schedule"],
)

@router.post("/task/{task_id}")
def schedule_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    try:
        result = scheduler.schedule_task(db, task_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
def get_events(start: str, end: str, db: Session = Depends(get_db)):
    """
    Get all events (Google + Ultron) for a specific range.
    start/end should be ISO strings.
    """
    user = crud.get_user(db, 1) # Hardcoded user
    if not user or not user.google_token:
        return []
    
    try:
        events = calendar_integration.list_events(
            user.google_token, 
            time_min=start, 
            time_max=end,
            db=db,
            user_id=user.id
        )
        return events
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching events: {e}")
        # If token is expired/revoked, return a specific error
        if "expired" in error_msg.lower() or "revoked" in error_msg.lower() or "invalid_grant" in error_msg.lower():
            raise HTTPException(
                status_code=401, 
                detail="Google authentication expired. Please re-connect your Google Calendar."
            )
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/conflicts")
def get_conflicts(db: Session = Depends(get_db)):
    try:
        conflicts = scheduler.check_conflicts(db, 1) # Hardcoded user
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fixed", response_model=List[schemas.FixedSchedule])
def get_fixed_schedules(db: Session = Depends(get_db)):
    return crud.get_fixed_schedules(db, user_id=1)

@router.post("/fixed", response_model=schemas.FixedSchedule)
def create_fixed_schedule(schedule: schemas.FixedScheduleCreate, db: Session = Depends(get_db)):
    return crud.create_fixed_schedule(db, schedule, user_id=1)

@router.delete("/fixed/{schedule_id}")
def delete_fixed_schedule(schedule_id: int, db: Session = Depends(get_db)):
    crud.delete_fixed_schedule(db, schedule_id)
    return {"status": "success"}
