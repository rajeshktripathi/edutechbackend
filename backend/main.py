from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # Add this import
import os

from app.database import init_db
from app.routes import auth, users, assessments, video_analysis, text_analysis

app = FastAPI(title="CareerPath AI API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app origin
    #allow_origins=["https://edutech-portal-sigma.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Other options
# Option 1: Use raw string with r prefix
#UPLOADS_DIR = r"D:\Uploads"
#os.makedirs(UPLOADS_DIR, exist_ok=True)

# Option 2: Use forward slashes (Windows also accepts these)
# UPLOADS_DIR = "D:/Uploads"
# os.makedirs(UPLOADS_DIR, exist_ok=True)

# Option 3: Use os.path.join for cross-platform compatibility
# UPLOADS_DIR = os.path.join("D:", "Uploads")
# os.makedirs(UPLOADS_DIR, exist_ok=True)

# Serve uploaded files - Use raw string or forward slashes
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(assessments.router)
app.include_router(text_analysis.router)
app.include_router(video_analysis.router)


@app.on_event("startup")
def on_startup():
    init_db()
    # Create upload subdirectories
    os.makedirs(os.path.join(UPLOADS_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(UPLOADS_DIR, "documents"), exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "CareerPath AI API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "CareerPath AI API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)