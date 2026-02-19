import sys
import os
sys.path.append(os.getcwd())

from database import Base, engine
import models

# Ensure the table is known
print("Tables known:", Base.metadata.tables.keys())

if 'preferences' in Base.metadata.tables:
    print("Dropping preferences...")
    Base.metadata.drop_all(bind=engine, tables=[Base.metadata.tables['preferences']])
    print("Dropped.")

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
