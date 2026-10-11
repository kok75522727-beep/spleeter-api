import os
import tempfile
import subprocess
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI(title="Demucs Cinematic SFX & Vocals API")

def cleanup_temp_dir(dir_path: str):
    """လုပ်ငန်းစဉ်ပြီးဆုံးပါက ဆာဗာ Storage မပြည့်အောင် Temp ဖိုင်များကို ရှင်းလင်းမည်"""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)

# ၁။ နောက်ခံအသံ (SFX) သီးသန့် တောင်းယူရန် (Movie Dub နောက်ခံအတွက်)
@app.post("/separate")
async def separate_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp()
    input_filename = "input_audio.mp3"
    input_path = os.path.join(temp_dir, input_filename)
    
    with open(input_path, "wb") as f:
        f.write(await file.read())
        
    try:
        subprocess.run(["demucs", "--two-stems=vocals", "-o", temp_dir, input_path], check=True, capture_output=True)
        bg_audio_path = os.path.join(temp_dir, "htdemucs", "input_audio", "no_vocals.wav")
        
        if os.path.exists(bg_audio_path):
            background_tasks.add_task(cleanup_temp_dir, temp_dir)
            return FileResponse(bg_audio_path, media_type="audio/wav", filename="cinematic_sfx.wav")
            
        return {"error": "Separation failed. Demucs output not found."}
        
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return {"error": str(e)}

# ၂။ လူသံ (Vocals) သီးသန့် တောင်းယူရန် (Whisper ဖြင့် စာသားဖတ်ရန်အတွက်)
@app.post("/vocals")
async def extract_vocals(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp()
    input_filename = "input_audio.mp3"
    input_path = os.path.join(temp_dir, input_filename)
    
    with open(input_path, "wb") as f:
        f.write(await file.read())
        
    try:
        subprocess.run(["demucs", "--two-stems=vocals", "-o", temp_dir, input_path], check=True, capture_output=True)
        vocals_path = os.path.join(temp_dir, "htdemucs", "input_audio", "vocals.wav")
        
        if os.path.exists(vocals_path):
            background_tasks.add_task(cleanup_temp_dir, temp_dir)
            return FileResponse(vocals_path, media_type="audio/wav", filename="vocals.wav")
            
        return {"error": "Separation failed. Vocals output not found."}
        
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return {"error": str(e)}
