from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import subprocess
import os
import uuid

app = FastAPI(title="MovieShield AI Backend", version="1.0")

UPLOAD_DIR = "/tmp/movieshield_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "MovieShield AI Backend is Running Successfully!", "developer": "MD Badsha Alam"}

@app.post("/process-video/")
async def process_video(
    file: UploadFile = File(...),
    cta_text: str = Form("Watch full movie on our website!"),
    delay_sec: int = Form(5)
):
    try:
        # Save uploaded video temporarily
        unique_id = str(uuid.uuid4())[:8]
        input_ext = os.path.splitext(file.filename)[1] or ".mp4"
        input_path = os.path.join(UPLOAD_DIR, f"input_{unique_id}{input_ext}")
        output_path = os.path.join(UPLOAD_DIR, f"output_{unique_id}.mp4")

        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # FFmpeg command for anti-copyright pixel shifting, hue randomization, mirror & video processing
        # This transforms hash value and modifies video streams safely
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "hflip,eq=hue=15:saturation=1.1:contrast=1.08",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]

        # Execute FFmpeg via server shell
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_message = process.stderr.decode("utf-8")
            raise HTTPException(status_code=500, detail=f"FFmpeg Processing Error: {error_message[-300:]}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Processed video generation failed.")

        return FileResponse(output_path, media_type="video/mp4", filename="MovieShield-Safe-Ready.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
