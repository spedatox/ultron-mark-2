from services import scheduler
import crud
from database import SessionLocal
from datetime import datetime, timedelta

db = SessionLocal()
user = crud.get_user(db, 1)
prefs = crud.get_preferences(db, 1)

print(f"Prefs: wake={prefs.wake_time}, sleep={prefs.sleep_time}")

tz = datetime.now().astimezone().tzinfo

# Check TODAY (Sunday Nov 30)
start = datetime(2025, 11, 30, 0, 0, 0, tzinfo=tz)
end = datetime(2025, 11, 30, 23, 59, 59, tzinfo=tz)

print(f"Checking SUNDAY Nov 30 (today)")

events = scheduler.get_events_for_range(user, start, end, db=db)
print(f"Events: {len(events)}")
for e in events:
    print(f"  {e['start'].strftime('%H:%M')}-{e['end'].strftime('%H:%M')} {e['title']}")

gaps = scheduler.calculate_free_gaps(start, end, events, prefs)
print(f"\nGaps: {len(gaps)}")

for g in gaps:
    duration = int((g[1] - g[0]).total_seconds() / 60)
    print(f"  {g[0].strftime('%H:%M')} - {g[1].strftime('%H:%M')} ({duration} mins)")
