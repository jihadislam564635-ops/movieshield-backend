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

        # ২. FFmpeg দিয়ে মূল ভিডিওর ফুল লেন্স এবং অডিও বজায় রেখে ব্যাকগ্রাউন্ডে এআই ভয়েস মিক্স করা
        # এখানে মূল ভিডিওর অডিও ([0:a]) এবং এআই ভয়েস অডিও ([1:a]) কে amix ফিল্টার দিয়ে মিক্স করা হয়েছে 
        # যাতে মূল মুভির সাউন্ড ঠিক থাকে এবং সাথে এআই ভয়েস অ্যালার্টও শোনা যায়। -shortest ব্যবহার করা হয়নি যাতে ভিডিও না কাটে।
        ffmpeg_command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", audio_path,
            "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.8[a1];[a0][a1] amix=inputs=2:duration=first:dropout_transition=2 [a]",
            "-vf", "hflip,hue=h=12:s=1.15",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-map", "0:v:0",
            "-map", "[a]",
            "-ac", "2",
            output_path
        ]

        process = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_message = process.stderr.decode('utf-8', errors='ignore')
            raise HTTPException(status_code=500, detail=f"FFmpeg Full Length Mixing Error: {error_message}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(status_code=500, detail="Processed video was not generated properly.")

        return FileResponse(output_path, media_type="video/mp4", filename="MovieShield-AI-Protected.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "MovieShield AI Professional Backend is Running Smoothly!"}
