import os
import tempfile
import subprocess
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI(title="Demucs Cinematic SFX API")

def cleanup_temp_dir(dir_path: str):
    """လုပ်ငန်းစဉ်ပြီးဆုံးပါက ဆာဗာ Storage မပြည့်အောင် Temp ဖိုင်များကို ရှင်းလင်းမည်"""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)

@app.post("/separate")
async def separate_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    temp_dir = tempfile.mkdtemp()
    input_filename = "input_audio.mp3"
    input_path = os.path.join(temp_dir, input_filename)
    
    with open(input_path, "wb") as f:
        f.write(await file.read())
        
    try:
        # 💡 Demucs ဖြင့် လူသံ (Vocals) နှင့် ကျန်အသံအားလုံး (No_Vocals) ကို အတိကျဆုံး ခွဲထုတ်ခြင်း
        subprocess.run(
            ["demucs", "--two-stems=vocals", "-o", temp_dir, input_path], 
            check=True, 
            capture_output=True
        )
        
        # Demucs မှ ထုတ်ပေးသော နောက်ခံ SFX ဖိုင်လမ်းကြောင်း (no_vocals.wav)
        bg_audio_path = os.path.join(temp_dir, "htdemucs", "input_audio", "no_vocals.wav")
        
        if os.path.exists(bg_audio_path):
            background_tasks.add_task(cleanup_temp_dir, temp_dir)
            return FileResponse(bg_audio_path, media_type="audio/wav", filename="cinematic_sfx.wav")
            
        return {"error": "Separation failed. Demucs output not found."}
        
    except subprocess.CalledProcessError as e:
        cleanup_temp_dir(temp_dir)
        return {"error": f"Demucs processing error: {e.stderr.decode('utf-8', errors='ignore')}"}
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return {"error": str(e)}
