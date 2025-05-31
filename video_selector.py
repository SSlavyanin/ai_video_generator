import os
import requests
from text_generator import compress_scene  # Импортируем сжатие фразы

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def download_video(query: str, filename: str):
    """
    Загружает первое подходящее видео по запросу с Pexels API и сохраняет в файл.
    """
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
        raise e


def get_video_clips(phrases: list[str]) -> list[str]:
    """
    Получает клипы по фразам:
    - Сжимает каждую фразу до краткого смыслового запроса
    - Загружает подходящее видео по этому запросу
    - Сохраняет клип в папку assets/clips
    """
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    for i, phrase in enumerate(phrases):
        # Очистка фразы от кавычек
        clean_phrase = phrase.replace('"', '').replace("«", "").replace("»", "").strip()
        
        # Сжимаем смысл до короткого видеозапроса
        search_query = compress_scene(clean_phrase)

        path = f"assets/clips/clip_{i}.mp4"

        try:
            download_video(search_query, path)
            paths.append(path)
        except Exception as e:
            print(f"[!] Пропуск видео для фразы: '{phrase}' — {e}")

    return paths
