import os
import json
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from text_generator import generate_script
from voice_generator import generate_voices
from video_selector import get_video_clips
from video_builder import build_video
import requests
from threading import Lock

app = FastAPI()

DATA_DIR = "temp"
os.makedirs(DATA_DIR, exist_ok=True)

lock = Lock()  # Для потокобезопасности при записи/чтении JSON

class TopicRequest(BaseModel):
    topic: str

def save_data(session_id: str, data: dict):
    with lock:
        path = os.path.join(DATA_DIR, f"{session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_data(session_id: str):
    with lock:
        path = os.path.join(DATA_DIR, f"{session_id}.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

def cleanup_old_files(hours=1):
    now = time.time()
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            full_path = os.path.join(DATA_DIR, filename)
            if now - os.path.getmtime(full_path) > hours * 3600:
                try:
                    os.remove(full_path)
                    print(f"[Cleanup] Удалён файл {filename}")
                except Exception as e:
                    print(f"[Cleanup] Ошибка удаления файла {filename}: {e}")

@app.post("/generate_text")
def generate_text(req: TopicRequest):
    cleanup_old_files()
    phrases = generate_script(req.topic)
    session_id = str(int(time.time()*1000))
    save_data(session_id, {"phrases": phrases})
    return {"session_id": session_id, "phrases": phrases}

@app.post("/generate_voice/{session_id}")
def generate_voice(session_id: str):
    data = load_data(session_id)
    if "phrases" not in data:
        raise HTTPException(status_code=400, detail="Промежуточные данные не найдены")
    audio_paths = generate_voices(data["phrases"])
    data["audio_paths"] = audio_paths
    save_data(session_id, data)
    return {"audio_paths": audio_paths}

@app.post("/download_video/{session_id}")
def download_video(session_id: str):
    data = load_data(session_id)
    if "phrases" not in data:
        raise HTTPException(status_code=400, detail="Промежуточные данные не найдены")
    video_paths = get_video_clips(data["phrases"])
    data["video_paths"] = video_paths
    save_data(session_id, data)
    return {"video_paths": video_paths}

@app.post("/build_video/{session_id}")
def build_final_video(session_id: str):
    data = load_data(session_id)
    if "video_paths" not in data or "audio_paths" not in data:
        raise HTTPException(status_code=400, detail="Видео или аудио данные отсутствуют")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"static/videos/final_{timestamp}.mp4"
    os.makedirs("static/videos", exist_ok=True)

    build_video(data["video_paths"], data["audio_paths"], output_path=output_path)

    data["output_path"] = output_path
    save_data(session_id, data)
    return {"output_path": output_path}

@app.post("/send_video/{session_id}")
def send_video(session_id: str):
    data = load_data(session_id)
    if "output_path" not in data:
        raise HTTPException(status_code=400, detail="Финальное видео не найдено")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise HTTPException(status_code=500, detail="Telegram токен или chat_id не настроены")

    video_path = data["output_path"]
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Видео файл не найден")

    url = f"https://api.telegram.org/bot{token}/sendVideo"
    with open(video_path, "rb") as video:
        response = requests.post(url, data={"chat_id": chat_id}, files={"video": video})

    if response.ok:
        return {"detail": "Видео успешно отправлено в Telegram"}
    else:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки: {response.text}")
