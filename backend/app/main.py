import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import database and models to create tables on startup
from app.core.database import Base, engine
from app.models.files import Project, File  # noqa: F401

app = FastAPI()

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# Ensure data directories exist
os.makedirs("app/data/uploads", exist_ok=True)
os.makedirs("app/data/merged", exist_ok=True)

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static/uploads", StaticFiles(directory="app/data/uploads"), name="uploads")
app.mount("/static/merged", StaticFiles(directory="app/data/merged"), name="merged")

from app.api.api import api_router
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
