import os
from datetime import datetime
from text_generator import generate_script
from voice_generator import generate_voices
from video_selector import get_video_clips
from video_builder import build_video
import requests

def send_video_to_telegram(video_path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[!] TELEGRAM_BOT_TOKEN или CHAT_ID не указаны")
        return

    url = f"https://api.telegram.org/bot{token}/sendVideo"
    with open(video_path, "rb") as video:
        response = requests.post(url, data={"chat_id": chat_id}, files={"video": video})
    
    if response.ok:
        print("[✓] Видео отправлено в Telegram")
    else:
        print(f"[!] Ошибка отправки в Telegram: {response.text}")

def run(topic: str):
    phrases = generate_script(topic)
    audio_paths = generate_voices(phrases)
    video_paths = get_video_clips(phrases)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"static/videos/final_{timestamp}.mp4"

    build_video(video_paths, audio_paths, output_path=output_path)
    send_video_to_telegram(output_path)

if __name__ == "__main__":
    run("финансовая грамотность")
