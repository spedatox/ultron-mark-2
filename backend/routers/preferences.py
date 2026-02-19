from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, models
from database import get_db

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    responses={404: {"description": "Not found"}},
)

# Hardcoded user_id for prototype
USER_ID = 1

@router.get("/", response_model=schemas.Preference)
def read_preferences(db: Session = Depends(get_db)):
    db_pref = crud.get_preferences(db, user_id=USER_ID)
    if db_pref is None:
        # Check if user exists
        user = crud.get_user(db, user_id=USER_ID)
        if not user:
            # Create dummy user if not exists (this creates prefs too)
            user = crud.create_user(db, schemas.UserCreate(email="ahmet@example.com"))
            db_pref = crud.get_preferences(db, user_id=USER_ID)
        else:
            # User exists but prefs don't (e.g. after table reset)
            # Create default preferences for existing user
            db_pref = models.Preference(user_id=user.id)
            db.add(db_pref)
            db.commit()
            db.refresh(db_pref)
            
    return db_pref

@router.put("/", response_model=schemas.Preference)
def update_preferences(preferences: schemas.PreferenceCreate, db: Session = Depends(get_db)):
    return crud.update_preferences(db, user_id=USER_ID, preferences=preferences)
