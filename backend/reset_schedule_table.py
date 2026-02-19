import sys
import os
sys.path.append(os.getcwd())

from database import Base, engine
import models

# Ensure the table is known
print("Tables known:", Base.metadata.tables.keys())

if 'fixed_schedules' in Base.metadata.tables:
    print("Dropping fixed_schedules...")
    Base.metadata.drop_all(bind=engine, tables=[Base.metadata.tables['fixed_schedules']])
    print("Dropped.")

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
