import os
import requests
from moviepy.editor import VideoFileClip
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
    Обрабатывает первые 4 фразы:
    - Сжимает каждую фразу до короткого запроса
    - Загружает подходящее видео по запросу
    - Обрезает каждый клип до 7 секунд
    - Удаляет временные raw-клипы
    - Сохраняет финальные клипы в assets/clips
    """
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    selected_phrases = phrases[:4]  # Берём первые 4 фразы

    for i, phrase in enumerate(selected_phrases):
        clean_phrase = phrase.replace('"', '').replace("«", "").replace("»", "").strip()
        search_query = compress_scene(clean_phrase)
        raw_path = f"assets/clips/raw_{i}.mp4"
        final_path = f"assets/clips/clip_{i}.mp4"

        try:
            download_video(search_query, raw_path)

            clip = VideoFileClip(raw_path).subclip(0, 7)
            clip.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            paths.append(final_path)

            print(f"[~] Обработан клип {i + 1} из {len(selected_phrases)}")

        except Exception as e:
            print(f"[!] Проблема с фразой '{phrase}': {e}")
        finally:
            # Удаляем временный raw-файл
            if os.path.exists(raw_path):
                os.remove(raw_path)

    return paths
