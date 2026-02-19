from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services import calendar_integration
import crud
import json
from fastapi.responses import RedirectResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# Hardcoded user_id for prototype
USER_ID = 1

@router.get("/google/url")
def get_google_auth_url():
    try:
        url = calendar_integration.get_auth_url()
        return {"url": url}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/google/callback")
def google_auth_callback(code: str, db: Session = Depends(get_db)):
    try:
        credentials = calendar_integration.get_credentials_from_code(code)
        creds_dict = calendar_integration.credentials_to_dict(credentials)
        creds_json = json.dumps(creds_dict)
        
        # Save to DB
        crud.update_user_token(db, USER_ID, creds_json)
        
        # Redirect back to frontend settings page
        return RedirectResponse(url="http://localhost:3000/settings?connected=true")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def get_auth_status(db: Session = Depends(get_db)):
    user = crud.get_user(db, USER_ID)
    if user and user.google_token:
        # Actually test if the token works
        try:
            # Try to get service - this will fail if token is expired/revoked
            service, _ = calendar_integration.get_service(user.google_token)
            # If we got here, token is valid
            return {"connected": True, "status": "valid"}
        except Exception as e:
            error_msg = str(e)
            if "invalid_grant" in error_msg or "expired" in error_msg.lower() or "revoked" in error_msg.lower() or "re-authenticate" in error_msg.lower():
                return {"connected": False, "status": "expired", "message": "Token expired or revoked. Please reconnect."}
            # Other errors
            return {"connected": False, "status": "error", "message": str(e)}
    return {"connected": False, "status": "none"}
