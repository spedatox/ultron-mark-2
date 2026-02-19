import os
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime

# Scopes required for the app
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_FILE = 'credentials.json'

def get_flow():
    """Creates a Google OAuth Flow instance."""
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Missing {CREDENTIALS_FILE}. Please download it from Google Cloud Console.")
    
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:8000/auth/google/callback'
    )
    return flow

def get_auth_url():
    """Generates the authorization URL."""
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

def get_credentials_from_code(code):
    """Exchanges the auth code for credentials."""
    flow = get_flow()
    flow.fetch_token(code=code)
    return flow.credentials

def credentials_to_dict(credentials):
    """Converts credentials object to a dictionary for storage."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_service(token_json):
    """Builds the Google Calendar service from stored token JSON.
    
    Returns: (service, new_token_json or None)
    - If token was refreshed, returns the new token JSON to be saved
    - If no refresh needed, returns None as second value
    """
    creds_data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    
    new_token_json = None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Token was refreshed, return new credentials to save
            new_token_json = json.dumps(credentials_to_dict(creds))
        except Exception as e:
            print(f"Token refresh failed: {e}")
            raise Exception("Token has expired and could not be refreshed. Please re-authenticate.")
    elif not creds.valid:
        raise Exception("Token is invalid. Please re-authenticate.")
        
    service = build('calendar', 'v3', credentials=creds)
    return service, new_token_json

def list_events(token_json, time_min=None, time_max=None, db=None, user_id=None):
    """Lists events from the primary calendar."""
    service, new_token = get_service(token_json)
    
    # If token was refreshed, save it
    if new_token and db and user_id:
        from crud import update_user_token
        update_user_token(db, user_id, new_token)
    
    if not time_min:
        time_min = datetime.datetime.utcnow().isoformat() + 'Z'
        
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

def create_event(token_json, summary, start_time, end_time, description="", timezone="Europe/Istanbul"):
    """Creates an event in the primary calendar (or Ultron specific one)."""
    service, _ = get_service(token_json)
    
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': timezone,
        },
    }
    
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event

def update_event(token_json, event_id, start_time, end_time, summary=None, timezone="Europe/Istanbul"):
    """Updates an existing event."""
    service, _ = get_service(token_json)
    
    # First retrieve the event to preserve other fields
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    
    event['start']['dateTime'] = start_time.isoformat()
    event['start']['timeZone'] = timezone
    event['end']['dateTime'] = end_time.isoformat()
    event['end']['timeZone'] = timezone
    
    if summary:
        event['summary'] = summary
        
    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    return updated_event

def delete_event(token_json, event_id):
    """Deletes an event from the primary calendar."""
    service, _ = get_service(token_json)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return True
