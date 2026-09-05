from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import uuid
from gtts import gTTS

app = FastAPI(title="MovieShield AI Backend with CTA & Voice", version="2.0")

# CORS Middleware Setup (নেটলিফাই বা যেকোনো ফ্রন্টএন্ড থেকে রিকোয়েস্ট এলাও করার জন্য)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/movieshield_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "MovieShield AI Backend with AI Voice & CTA is Running!", "developer": "MD Badsha Alam"}

@app.post("/process-video/")
async def process_video(
    file: UploadFile = File(...),
    cta_text: str = Form("Watch full movie on our website!"),
    website_url: str = Form("virulworld.pro")
):
    try:
        # Save uploaded video temporarily
        unique_id = str(uuid.uuid4())[:8]
        input_ext = os.path.splitext(file.filename)[1] or ".mp4"
        input_path = os.path.join(UPLOAD_DIR, f"input_{unique_id}{input_ext}")
        processed_video_path = os.path.join(UPLOAD_DIR, f"proc_{unique_id}.mp4")
        audio_path = os.path.join(UPLOAD_DIR, f"audio_{unique_id}.mp3")
        output_path = os.path.join(UPLOAD_DIR, f"output_{unique_id}.mp4")

        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 1. Generate AI Voice for Call to Action (CTA)
        full_cta_speech = f"Attention movie lovers! {cta_text}. Visit {website_url} now!"
        tts = gTTS(text=full_cta_speech, lang='en', slow=False)
        tts.save(audio_path)

        # 2. FFmpeg Video Processing (Pixel shift, hue change, mirror to bypass copyright)
        ffmpeg_video_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "hflip,eq=hue=15:saturation=1.1:contrast=1.08",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an", processed_video_path
        ]
        subprocess.run(ffmpeg_video_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 3. Merge Processed Video with AI Voice Audio
        ffmpeg_merge_cmd = [
            "ffmpeg", "-y",
            "-i", processed_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            output_path
        ]
        
        process = subprocess.run(ffmpeg_merge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_message = process.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg Merge Error: {error_message[-300:]}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Final video generation failed.")

        return FileResponse(output_path, media_type="video/mp4", filename="MovieShield-AI-Ready.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
