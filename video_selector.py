import os
import requests
import logging
import moviepy.editor as mp
from text_generator import compress_scene

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


def download_video_min_duration(query: str, filename: str, min_duration: float = 7.0) -> bool:
    """
    Скачивает первое подходящее видео с Pexels API, которое длится минимум `min_duration` секунд.
    Сохраняет файл как `filename`. Возвращает True, если успешно.
    """
    logging.info(f"[download_video_min_duration] Старт поиска видео по запросу: '{query}'")

    if not PEXELS_API_KEY:
        logging.error("[download_video_min_duration] Ошибка: PEXELS_API_KEY не найден в переменных окружения.")
        raise ValueError("PEXELS_API_KEY не найден в переменных окружения.")

    url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
        logging.info("[download_video_min_duration] Отправляем запрос к Pexels API...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        videos = data.get("videos", [])
        if not videos:
            logging.warning(f"[download_video_min_duration] Нет видео для запроса: '{query}'")
            return False

        for idx, video in enumerate(videos):
            logging.info(f"[download_video_min_duration] Обработка видео {idx + 1} из {len(videos)}")
            files = video.get("video_files", [])
            for f in files:
                width = f.get("width", 0)
                quality = f.get("quality")
                if width >= 640 and quality == "hd":
                    video_url = f["link"]
                    temp_path = filename + ".tmp"
                    logging.info(f"[download_video_min_duration] Пытаемся скачать видео: {video_url}")

                    try:
                        with requests.get(video_url, timeout=15, stream=True) as r:
                            r.raise_for_status()
                            with open(temp_path, "wb") as f_out:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f_out.write(chunk)
                        logging.info(f"[download_video_min_duration] Видео сохранено во временный файл: {temp_path}")
                    except Exception as e:
                        logging.error(f"[download_video_min_duration] Ошибка при скачивании видео: {e}")
                        continue

                    try:
                        clip = mp.VideoFileClip(temp_path)
                        logging.info(f"[download_video_min_duration] Проверяем длительность видео: {clip.duration:.2f} сек")
                        if clip.duration >= min_duration:
                            clip.close()
                            os.rename(temp_path, filename)
                            logging.info(f"[download_video_min_duration] Видео подходит по длительности и сохранено как: {filename}")
                            return True
                        else:
                            clip.close()
                            os.remove(temp_path)
                            logging.info(f"[download_video_min_duration] Видео слишком короткое (<{min_duration} сек), удаляем")
                    except Exception as e:
                        logging.error(f"[download_video_min_duration] Ошибка при проверке видео: {e}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        logging.warning(f"[download_video_min_duration] Нет подходящих видео ≥ {min_duration} сек для запроса: '{query}'")
        return False

    except Exception as e:
        logging.error(f"[download_video_min_duration] Ошибка при загрузке видео для '{query}': {e}")
        return False



def get_video_clips(phrases: list[str]) -> list[str]:
    logging.info("Старт обработки фраз")
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    selected_phrases = phrases[:4]

    for i, phrase in enumerate(selected_phrases):
        logging.info(f"Обработка фразы {i+1}: {phrase}")
        clean_phrase = phrase.replace('"', '').replace("«", "").replace("»", "").strip()
        search_query = compress_scene(clean_phrase)
        logging.info(f"  Сжатый поисковый запрос: '{search_query}'")

        raw_path = f"assets/clips/raw_{i}.mp4"
        final_path = f"assets/clips/clip_{i}.mp4"

        try:
            logging.info("  Скачиваем видео...")
            success = download_video_min_duration(search_query, raw_path)
            if not success:
                logging.warning("  Видео не найдено или не скачано")
                continue

            logging.info("  Загружаем скачанное видео для обработки...")
            clip = mp.VideoFileClip(raw_path)
            logging.info(f"  Длительность видео: {clip.duration:.2f} сек")

            end_time = min(7, clip.duration)
            logging.info(f"  Нарезаем видео до {end_time} сек")
            subclip = clip.subclip(0, end_time)

            logging.info("  Записываем итоговый клип...")
            subclip.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            paths.append(final_path)

            clip.close()
            subclip.close()

            logging.info(f"  Клип {i+1} обработан успешно")

        except Exception as e:
            logging.error(f"  Ошибка при обработке фразы '{phrase}': {e}")

        finally:
            if os.path.exists(raw_path):
                os.remove(raw_path)

    logging.info("Обработка фраз завершена")
    return paths

