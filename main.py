from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import os
import shutil
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "/tmp/movieshield"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "MovieShield Stable Bypass Backend is Live!"}

@app.post("/process-video/")
async def process_video(
    file: UploadFile = File(...),
    cta_text: str = Form("Watch full movie on our website!"),
    website_url: str = Form("virulworld.pro")
):
    unique_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(TEMP_DIR, f"input_{unique_id}.mp4")
    output_path = os.path.join(TEMP_DIR, f"output_{unique_id}.mp4")

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Stable & Fast Bypass Command (Lightweight for Render Free Tier)
        # - hflip: Flips video horizontally to break pHash
        # - hue: Changes color spectrum to bypass image/video hashing bots
        # - atempo: Slight audio tempo change to disrupt audio fingerprint matching without crashing
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", "hflip,hue=h=18",
            "-af", "atempo=0.98",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-map_metadata", "-1",
            "-y", output_path
        ]

        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"FFmpeg Error: {process.stderr[-200:]}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(status_code=500, detail="Video processing failed.")

        return FileResponse(output_path, media_type="video/mp4", filename="Protected-Video.mp4")

    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))
