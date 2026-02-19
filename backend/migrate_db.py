import sqlite3

conn = sqlite3.connect('../ultron.db')
cursor = conn.cursor()

# Check if columns exist
cursor.execute("PRAGMA table_info(preferences)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Existing columns: {columns}")

if 'commute_duration_mins' not in columns:
    cursor.execute('ALTER TABLE preferences ADD COLUMN commute_duration_mins INTEGER DEFAULT 90')
    print("Added commute_duration_mins column")
else:
    print("commute_duration_mins already exists")

if 'dinner_time' not in columns:
    cursor.execute('ALTER TABLE preferences ADD COLUMN dinner_time TEXT DEFAULT "19:00"')
    print("Added dinner_time column")
else:
    print("dinner_time already exists")

conn.commit()
conn.close()
print("Migration complete!")
