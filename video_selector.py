import os
import requests
from config import PEXELS_API_KEY

def download_video(query: str, filename: str):
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    r = requests.get(url, headers=headers)
    data = r.json()
    try:
        video_url = data["videos"][0]["video_files"][0]["link"]
        video_data = requests.get(video_url).content
        with open(filename, "wb") as f:
            f.write(video_data)
        print(f"Скачано видео для запроса: {query}")
    except Exception as e:
        print(f"Ошибка при загрузке видео: {e}")

def get_video_clips(phrases: list[str]) -> list[str]:
    os.makedirs("assets/clips", exist_ok=True)
    paths = []
    for i, phrase in enumerate(phrases):
        query = phrase.split()[0]  # простейший ключ — первое слово
        path = f"assets/clips/clip_{i}.mp4"
        download_video(query, path)
        paths.append(path)
    return paths
