import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/movieshield_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process-video/")
async def process_video(
    file: UploadFile = File(...),
    cta_text: str = Form(...),
    website_url: str = Form(...)
):
    input_path = os.path.join(UPLOAD_DIR, f"input_{file.filename}")
    output_path = os.path.join(UPLOAD_DIR, f"proc_{file.filename}")

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Updated safe FFmpeg filter to prevent syntax errors on cloud servers
        # Using simple hflip and standard video filters
        ffmpeg_command = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "hflip,colorbalance=rs=0.1:gs=0.1:bs=0.1",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",  # Muting original audio temporarily to avoid stream map mismatches
            output_path
        ]

        process = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_message = process.stderr.decode('utf-8', errors='ignore')
            raise HTTPException(status_code=500, detail=f"FFmpeg Error: {error_message}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(status_code=500, detail="Processed video was not generated properly.")

        return FileResponse(output_path, media_type="video/mp4", filename="MovieShield-AI-Ready.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "MovieShield AI Backend is Running Smoothly!"}
