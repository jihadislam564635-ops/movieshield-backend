import os
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS

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
    audio_path = os.path.join(UPLOAD_DIR, "cta_audio.mp3")

    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

        # Generate AI Voice CTA
        full_message = f"{cta_text}. Visit {website_url} now!"
        tts = gTTS(text=full_message, lang='en')
        tts.save(audio_path)

        # FFmpeg video processing (Anti-copyright filters + Audio merging)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", audio_path,
            "-vf", "hflip,eq=hue=15:saturation=1.1:contrast=1.08",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ]

        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"FFmpeg Error: {process.stderr[-300:]}")

        return FileResponse(output_path, media_type="video/mp4", filename="MovieShield-AI-Ready.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
