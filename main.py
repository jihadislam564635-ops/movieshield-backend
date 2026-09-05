import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
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
    audio_path = os.path.join(UPLOAD_DIR, "cta_voice.mp3")
    output_path = os.path.join(UPLOAD_DIR, f"proc_{file.filename}")

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ১. ইউজার যে কাস্টম মেসেজ ও ওয়েবসাইট লিংক দিয়েছে, তা দিয়ে এআই ভয়েস (mp3) তৈরি করা
        full_message = f"{cta_text}. Visit {website_url} now!"
        tts = gTTS(text=full_message, lang='en', slow=False)
        tts.save(audio_path)

        # ২. FFmpeg দিয়ে ভিডিওর ভিজ্যুয়াল ফিল্টার এবং এআই ভয়েস অডিও একসাথে মিক্স করা
        # এখানে -pix_fmt yuv420p ও libx264 ব্যবহার করা হয়েছে যাতে উইন্ডোজ বা যেকোনো প্লেয়ারে চলে
        ffmpeg_command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", audio_path,
            "-vf", "hflip",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ]

        process = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_message = process.stderr.decode('utf-8', errors='ignore')
            raise HTTPException(status_code=500, detail=f"FFmpeg Audio Muxing Error: {error_message}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(status_code=500, detail="Processed video with AI voice was not generated properly.")

        return FileResponse(output_path, media_type="video/mp4", filename="MovieShield-AI-Ready.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "MovieShield AI Backend with AI Voice is Running Smoothly!"}
