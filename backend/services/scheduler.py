import datetime
from sqlalchemy.orm import Session
import models, crud
from services import calendar_integration
from dateutil import parser
import pytz

# Helper to parse HH:MM to time object
def parse_time_str(time_str):
    return datetime.datetime.strptime(time_str, "%H:%M").time()

def get_events_for_range(user: models.User, start_dt: datetime.datetime, end_dt: datetime.datetime, db: Session = None):
    """Fetches events from Google Calendar AND Fixed Schedules for the given range."""
    normalized_events = []

    # 1. Google Calendar Events
    if user.google_token:
        try:
            events = calendar_integration.list_events(
                user.google_token, 
                time_min=start_dt.isoformat(), 
                time_max=end_dt.isoformat()
            )
            for event in events:
                # Handle 'dateTime' (Timed events)
                if 'dateTime' in event['start']:
                    start = parser.isoparse(event['start']['dateTime'])
                    end = parser.isoparse(event['end']['dateTime'])
                    normalized_events.append({
                        'start': start, 
                        'end': end, 
                        'title': event.get('summary', 'Busy'),
                        'google_event_id': event.get('id'),
                        'source': 'google'
                    })
                # Handle 'date' (All-day events)
                elif 'date' in event['start']:
                    # All day events are YYYY-MM-DD
                    start_date = datetime.datetime.strptime(event['start']['date'], "%Y-%m-%d").date()
                    end_date = datetime.datetime.strptime(event['end']['date'], "%Y-%m-%d").date()
                    
                    # Convert to datetime (Start of day to End of day)
                    # Use start_dt timezone if available, else local
                    tz = start_dt.tzinfo or datetime.timezone.utc
                    
                    # Create start/end times for the all-day event
                    # Note: Google Calendar all-day events end on the *next* day (exclusive)
                    start = datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=tz)
                    # We subtract 1 second to keep it within the day for display/logic purposes if needed, 
                    # or keep it as midnight next day. Let's keep it as midnight next day but ensure logic handles it.
                    end = datetime.datetime.combine(end_date, datetime.time.min).replace(tzinfo=tz)
                    
                    normalized_events.append({
                        'start': start, 
                        'end': end, 
                        'title': event.get('summary', 'All Day Event'),
                        'google_event_id': event.get('id'),
                        'source': 'google'
                    })
        except Exception as e:
            print(f"Google Calendar Fetch Error: {e}")

    # 2. Fixed Schedules (Classes/Work)
    if db:
        fixed_schedules = crud.get_fixed_schedules(db, user.id)
        # Map day names to weekday numbers (Monday=0, Sunday=6)
        day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, 
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        # Iterate through each day in the range
        current_day = start_dt.date()
        end_day = end_dt.date()
        
        while current_day <= end_day:
            weekday = current_day.weekday()
            
            # Track daily campus blocks (University + Work) for commute calculation
            campus_starts = []
            campus_ends = []
            
            for schedule in fixed_schedules:
                if day_map.get(schedule.day_of_week) == weekday:
                    # Create datetime for this specific instance
                    start_time = parse_time_str(schedule.start_time)
                    end_time = parse_time_str(schedule.end_time)
                    
                    # Combine with current date and timezone
                    tz = start_dt.tzinfo
                    instance_start = datetime.datetime.combine(current_day, start_time).replace(tzinfo=tz)
                    instance_end = datetime.datetime.combine(current_day, end_time).replace(tzinfo=tz)
                    
                    normalized_events.append({'start': instance_start, 'end': instance_end, 'title': schedule.title})
                    
                    # Treat both University and Work as "Campus" activities that require commute
                    if schedule.category in ["university", "work"]:
                        campus_starts.append(instance_start)
                        campus_ends.append(instance_end)
            
            # Add Commute Blocks (Before first campus activity, After last campus activity)
            if campus_starts and user.preferences:
                commute_mins = user.preferences.commute_duration_mins or 90
                first_activity = min(campus_starts)
                last_activity = max(campus_ends)
                
                # Check for daily overrides
                date_str = current_day.strftime("%Y-%m-%d")
                overrides = crud.get_daily_overrides(db, user.id, date_str) if db else []
                override_map = {o.override_type: o.value for o in overrides}
                
                # Check for skip_commute override
                if override_map.get("skip_commute") != "true":
                    # Check for custom departure time override
                    if "departure_time" in override_map:
                        # User specified exact departure time
                        dep_time = parse_time_str(override_map["departure_time"])
                        commute_to_start = datetime.datetime.combine(current_day, dep_time).replace(tzinfo=tz)
                    else:
                        # Default: commute_mins before first activity
                        commute_to_start = first_activity - datetime.timedelta(minutes=commute_mins)
                    
                    # Commute To Campus
                    normalized_events.append({'start': commute_to_start, 'end': first_activity, 'title': "Commute"})
                    
                    # Commute Back Home
                    commute_back_end = last_activity + datetime.timedelta(minutes=commute_mins)
                    normalized_events.append({'start': last_activity, 'end': commute_back_end, 'title': "Commute"})
            
            # Add Dinner Block (if configured and not skipped)
            if user.preferences and user.preferences.dinner_time:
                # Check for skip_dinner override
                date_str = current_day.strftime("%Y-%m-%d")
                overrides = crud.get_daily_overrides(db, user.id, date_str) if db else []
                override_map = {o.override_type: o.value for o in overrides}
                
                if override_map.get("skip_dinner") != "true":
                    dinner_time = parse_time_str(user.preferences.dinner_time)
                    tz = start_dt.tzinfo
                    dinner_start = datetime.datetime.combine(current_day, dinner_time).replace(tzinfo=tz)
                    # Assume 1 hour for dinner
                    dinner_end = dinner_start + datetime.timedelta(hours=1)
                    normalized_events.append({'start': dinner_start, 'end': dinner_end, 'title': "Dinner"})

            current_day += datetime.timedelta(days=1)

    return normalized_events

def calculate_free_gaps(
    start_dt: datetime.datetime, 
    end_dt: datetime.datetime, 
    existing_events: list, 
    preferences: models.Preference
):
    """
    Finds free time slots between start_dt and end_dt, respecting:
    - Existing events
    - Wake/Sleep times
    """
    gaps = []
    
    wake_time = parse_time_str(preferences.wake_time)
    sleep_time = parse_time_str(preferences.sleep_time)
    
    # Iterate day by day
    current_day = start_dt.date()
    end_day = end_dt.date()
    
    while current_day <= end_day:
        # Define the "awake window" for this day
        # We need to handle timezones carefully. Let's assume the input datetimes are timezone aware.
        # We'll construct the window in the same timezone as start_dt
        tz = start_dt.tzinfo
        
        day_start = datetime.datetime.combine(current_day, wake_time).replace(tzinfo=tz)
        day_end = datetime.datetime.combine(current_day, sleep_time).replace(tzinfo=tz)
        
        # If today is the start day, clamp to start_dt (if it's later than wake time)
        if current_day == start_dt.date():
            day_start = max(day_start, start_dt)
            
        # If today is the end day, clamp to end_dt
        if current_day == end_dt.date():
            day_end = min(day_end, end_dt)
            
        if day_start >= day_end:
            current_day += datetime.timedelta(days=1)
            continue

        # Find events that overlap with this day's window
        day_events = []
        for event in existing_events:
            ev_start = event['start']
            ev_end = event['end']
            # Check overlap
            if ev_end > day_start and ev_start < day_end:
                # Clip event to the window
                clamped_start = max(ev_start, day_start)
                clamped_end = min(ev_end, day_end)
                day_events.append((clamped_start, clamped_end))
        
        # Sort events by start time
        day_events.sort(key=lambda x: x[0])
        
        # Compute gaps between events
        cursor = day_start
        for ev_start, ev_end in day_events:
            if ev_start > cursor:
                gaps.append((cursor, ev_start))
            cursor = max(cursor, ev_end)
            
        # Add final gap after last event
        if cursor < day_end:
            gaps.append((cursor, day_end))
            
        current_day += datetime.timedelta(days=1)
        
    return gaps

def schedule_task(db: Session, task_id: int):
    """
    Main scheduling logic.
    1. Fetch task and user.
    2. Fetch calendar events.
    3. Calculate gaps.
    4. Create StudyBlocks.
    5. Push to Google Calendar.
    """
    task = crud.get_task(db, task_id)
    
    if not task:
        raise ValueError("Task not found")
        
    user = crud.get_user(db, task.user_id)
    prefs = crud.get_preferences(db, user.id)
    
    # Time range: Now to Deadline
    now = datetime.datetime.now(datetime.timezone.utc).astimezone() # Local aware time
    deadline = task.deadline
    
    # Ensure deadline is aware
    if deadline.tzinfo is None:
        # Assume deadline is in local time if naive
        deadline = deadline.replace(tzinfo=now.tzinfo)
        
    if now >= deadline:
        raise ValueError("Deadline has passed")

    # 1. Fetch Existing Events (Google + Fixed)
    existing_events = get_events_for_range(user, now, deadline, db)
    
    # 2. Also fetch existing StudyBlocks for OTHER tasks to treat them as busy
    # (For this prototype, we might skip this optimization or just rely on Google Calendar if we sync immediately)
    # Let's rely on Google Calendar events since we push them there.
    
    # 3. Calculate Gaps
    gaps = calculate_free_gaps(now, deadline, existing_events, prefs)
    
    # 4. Allocate Blocks
    needed_minutes = task.total_required_time - task.scheduled_minutes
    block_len = prefs.study_block_length
    max_daily = prefs.max_study_minutes_per_day
    
    # Track daily usage (simple approximation)
    # In a real app, we'd query DB for existing study blocks per day.
    # Here we assume we are starting fresh or just counting what we add now.
    # TODO: Fetch existing daily usage to respect max_daily properly.
    
    new_blocks = []
    
    for gap_start, gap_end in gaps:
        if needed_minutes <= 0:
            break
            
        gap_duration = (gap_end - gap_start).total_seconds() / 60
        
        # While we can fit a block in this gap
        current_block_start = gap_start
        
        while gap_duration >= block_len and needed_minutes > 0:
            # Create a block
            block_end = current_block_start + datetime.timedelta(minutes=block_len)
            
            # Create DB Object
            new_block = models.StudyBlock(
                task_id=task.id,
                start_time=current_block_start,
                end_time=block_end
            )
            new_blocks.append(new_block)
            
            # Update counters
            needed_minutes -= block_len
            gap_duration -= block_len
            current_block_start = block_end
            
            # Add a small break? (Optional, not in spec)
            
    # 5. Commit and Sync
    scheduled_count = 0
    for block in new_blocks:
        # Save to DB
        db.add(block)
        db.commit() # Commit to get ID?
        
        # Sync to Google Calendar
        if user.google_token:
            try:
                summary = f"Study: {task.title}"
                if task.course_tag:
                    summary += f" ({task.course_tag})"
                    
                g_event = calendar_integration.create_event(
                    user.google_token,
                    summary=summary,
                    start_time=block.start_time,
                    end_time=block.end_time,
                    description="Auto-scheduled by Ultron"
                )
                block.google_event_id = g_event.get('id')
                db.add(block) # Update with ID
            except Exception as e:
                print(f"Failed to sync block to Google Calendar: {e}")
        
        scheduled_count += block_len

    # Update Task
    task.scheduled_minutes += scheduled_count
    if task.scheduled_minutes >= task.total_required_time:
        task.status = "scheduled"
    else:
        task.status = "underplanned"
        
    db.commit()
    
    return {"scheduled_minutes": scheduled_count, "blocks_created": len(new_blocks)}

def check_conflicts(db: Session, user_id: int):
    """
    Checks for overlaps between StudyBlocks and Google Calendar events.
    Returns a list of conflicting StudyBlocks.
    """
    user = crud.get_user(db, user_id)
    if not user or not user.google_token:
        return []
        
    # Get all future study blocks
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    future_blocks = db.query(models.StudyBlock).filter(models.StudyBlock.start_time >= now).all()
    
    if not future_blocks:
        return []
        
    # Determine range to fetch from Google
    end_time = max(b.end_time for b in future_blocks)
    
    # Fetch Google Events
    # Note: This fetches ALL events, including the ones we created.
    google_events = get_events_for_range(user, now, end_time)
    
    conflicts = []
    
    for block in future_blocks:
        # Ensure block times are aware for comparison
        b_start = block.start_time.replace(tzinfo=now.tzinfo) if block.start_time.tzinfo is None else block.start_time
        b_end = block.end_time.replace(tzinfo=now.tzinfo) if block.end_time.tzinfo is None else block.end_time
        
        for event in google_events:
            ev_start = event['start']
            ev_end = event['end']
            # Check overlap
            if ev_end > b_start and ev_start < b_end:
                # It overlaps. Is it the SAME event?
                # We don't have the Google Event ID in the normalized list easily available in get_events_for_range
                # We need to modify get_events_for_range to return IDs too.
                pass 
                
    return [] # Placeholder until we fix get_events_for_range

def reschedule_block(db: Session, block_id: int, new_start_time: datetime.datetime):
    """
    Moves a specific study block to a new time.
    Updates both DB and Google Calendar.
    """
    block = crud.get_study_block(db, block_id)
    if not block:
        raise ValueError("Study block not found")
        
    # Calculate duration to keep it constant
    duration = block.end_time - block.start_time
    
    # Update DB
    block.start_time = new_start_time
    block.end_time = new_start_time + duration
    db.commit()
    db.refresh(block)
    
    # Update Google Calendar
    if block.google_event_id:
        task = block.task
        user = task.user
        if user.google_token:
            try:
                calendar_integration.update_event(
                    user.google_token,
                    event_id=block.google_event_id,
                    start_time=block.start_time,
                    end_time=block.end_time
                )
            except Exception as e:
                print(f"Failed to update Google Calendar event: {e}")
                
    return block
