import os
import requests
import moviepy.editor as mp
from text_generator import compress_scene

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def download_video_min_duration(query: str, filename: str, min_duration: float = 7.0) -> bool:
    """
    Скачивает первое подходящее видео с Pexels API, которое длится минимум `min_duration` секунд.
    Сохраняет файл как `filename`. Возвращает True, если успешно.
    """
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY не найден в переменных окружения.")

    url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        videos = data.get("videos", [])
        if not videos:
            print(f"[!] Нет видео для запроса: '{query}'")
            return False

        for video in videos:
            files = video.get("video_files", [])
            for f in files:
                if f.get("width", 0) >= 640 and f.get("quality") == "hd":
                    video_url = f["link"]
                    temp_path = filename + ".tmp"
                    video_data = requests.get(video_url, timeout=15).content

                    with open(temp_path, "wb") as f_out:
                        f_out.write(video_data)

                    try:
                        clip = mp.VideoFileClip(temp_path)
                        if clip.duration >= min_duration:
                            os.rename(temp_path, filename)
                            clip.close()
                            print(f"[✓] Скачано видео для запроса: {query}")
                            return True
                        else:
                            clip.close()
                            os.remove(temp_path)
                    except Exception as e:
                        print(f"[!] Ошибка при проверке видео: {e}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        print(f"[!] Нет подходящих видео ≥ {min_duration} сек для запроса: '{query}'")
        return False

    except Exception as e:
        print(f"[!] Ошибка при загрузке видео для '{query}': {e}")
        return False


def get_video_clips(phrases: list[str]) -> list[str]:
    """
    Получает 4 подходящих клипа по фразам:
    - Сжимает смысл до краткого запроса
    - Ищет и скачивает видео ≥ 7 сек
    - Обрезает до 7 сек
    - Сохраняет в assets/clips/clip_X.mp4
    """
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    selected_phrases = phrases[:4]

    for i, phrase in enumerate(selected_phrases):
        clean_phrase = phrase.replace('"', '').replace("«", "").replace("»", "").strip()
        search_query = compress_scene(clean_phrase)
        raw_path = f"assets/clips/raw_{i}.mp4"
        final_path = f"assets/clips/clip_{i}.mp4"

        try:
            success = download_video_min_duration(search_query, raw_path)
            if not success:
                continue

            clip = mp.VideoFileClip(raw_path)
            print(f"[i] Длительность видео {i + 1}: {clip.duration:.2f} сек")

            end_time = min(7, clip.duration)
            subclip = clip.subclip(0, end_time)

            subclip.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            paths.append(final_path)

            clip.close()
            subclip.close()

            print(f"[~] Обработан клип {i + 1} из {len(selected_phrases)}")

        except Exception as e:
            print(f"[!] Проблема с фразой '{phrase}': {e}")

        finally:
            if os.path.exists(raw_path):
                os.remove(raw_path)

    return paths
