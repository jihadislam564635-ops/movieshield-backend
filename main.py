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
    return {"status": "MovieShield AI Masterclass Bypass Engine is Live!"}

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
        # Save uploaded file safely
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 🛡️ ADVANCED MONETIZATION & COPYRIGHT BYPASS ENGINE (FFmpeg)
        # 1. -vf "hflip,scale=iw*0.98:ih*0.98,pad=iw/0.98:ih/0.98:(ow-iw)/2:(oh-ih)/2,hue=h=12:s=1.15": 
        #    - hflip: Mirror flip
        #    - scale & pad: Tiny micro-resize to destroy native video resolution fingerprint/hash
        #    - hue: Color shifting to alter pixel signatures
        # 2. -af "asetrate=44100*1.03,aresample=44100,atempo=0.97": 
        #    - Alters audio frequency and pitch slightly to bypass Facebook Audio ID/Content ID bots while keeping vocals clear.
        
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", "hflip,scale=trunc(iw/2)*2:trunc(ih/2)*2,hue=h=12:s=1.15",
            "-af", "asetrate=44100*1.02,aresample=44100,atempo=0.98",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-map_metadata", "-1",  # Strips all original video metadata/tags
            "-y", output_path
        ]

        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"FFmpeg Bypass Error: {process.stderr[-300:]}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(status_code=500, detail="Protected video generation failed.")

        return FileResponse(output_path, media_type="video/mp4", filename="FB-Monetization-Safe.mp4")

    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        raise HTTPException(status_code=500, detail=str(e))
