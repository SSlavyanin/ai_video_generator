import os
import requests

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def download_video(query: str, filename: str):
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY не найден в переменных окружения.")

    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("videos"):
            raise ValueError(f"Нет видео для запроса: '{query}'")

        video_files = data["videos"][0].get("video_files", [])
        if not video_files:
            raise ValueError(f"Нет файлов у первого видео по запросу: '{query}'")

        video_url = video_files[0]["link"]
        video_data = requests.get(video_url, timeout=15).content

        with open(filename, "wb") as f:
            f.write(video_data)

        print(f"[✓] Скачано видео для запроса: {query}")

    except Exception as e:
        print(f"[!] Ошибка при загрузке видео для '{query}': {e}")
        raise e  # можно убрать raise, если хочешь продолжать при ошибке

def get_video_clips(phrases: list[str]) -> list[str]:
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    for i, phrase in enumerate(phrases):
        query = phrase.split()[0] if phrase.strip() else "abstract"
        path = f"assets/clips/clip_{i}.mp4"

        try:
            download_video(query, path)
            paths.append(path)
        except Exception as e:
            print(f"[!] Пропуск видео для фразы: '{phrase}' — {e}")

    return paths
