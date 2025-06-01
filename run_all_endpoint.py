import os
import time
import requests
from fastapi import APIRouter, Body
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()

BASE_URL = "http://localhost:8000"  # или URL FastAPI на Render

class TopicRequest(BaseModel):
    topic: str

@router.post("/run_all")
def run_all(req: TopicRequest = Body(...)):
    topic = req.topic

    def log_step(name, res):
        print(f"\n=== {name.upper()} ===")
        print("Status:", res.status_code)
        try:
            print("Response:", res.json())
        except:
            print("Raw Response:", res.text)

    try:
        # 1. Сгенерировать текст
        r1 = requests.post(f"{BASE_URL}/generate_text", json={"topic": topic})
        log_step("generate_text", r1)
        if r1.status_code != 200:
            return JSONResponse(status_code=500, content={"step": "generate_text", "error": r1.text})
        session_id = r1.json()["session_id"]
        time.sleep(1)

        # 2. Сгенерировать озвучку
        r2 = requests.post(f"{BASE_URL}/generate_voice/{session_id}")
        log_step("generate_voice", r2)
        if r2.status_code != 200:
            return JSONResponse(status_code=500, content={"step": "generate_voice", "error": r2.text})
        time.sleep(1)

        # 3. Скачать видеоклипы
        r3 = requests.post(f"{BASE_URL}/download_video/{session_id}")
        log_step("download_video", r3)
        if r3.status_code != 200:
            return JSONResponse(status_code=500, content={"step": "download_video", "error": r3.text})
        time.sleep(1)

        # 4. Собрать финальное видео
        r4 = requests.post(f"{BASE_URL}/build_video/{session_id}")
        log_step("build_video", r4)
        if r4.status_code != 200:
            return JSONResponse(status_code=500, content={"step": "build_video", "error": r4.text})
        time.sleep(1)

        # 5. Отправить в Telegram
        r5 = requests.post(f"{BASE_URL}/send_video/{session_id}")
        log_step("send_video", r5)
        if r5.status_code != 200:
            return JSONResponse(status_code=500, content={"step": "send_video", "error": r5.text})

        return {
            "detail": "Готово ✅",
            "session_id": session_id,
            "output_path": r4.json().get("output_path"),
            "telegram_status": "OK"
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Ошибка выполнения: {str(e)}"})
