from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from database import engine, Base
import models
from routers import tasks, preferences, auth, schedule, chat
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import os

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ultron Prototype Mark II", version="0.2.0")

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(preferences.router)
app.include_router(auth.router)
app.include_router(schedule.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Ultron Mark II - Timekeeper Online"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "Ultron Mark II"}
