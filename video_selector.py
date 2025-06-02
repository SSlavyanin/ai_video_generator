import os
import requests
import logging
import moviepy.editor as mp
import time
from text_generator import compress_scene

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


def download_video_min_duration(query: str, filename: str, min_duration: float = 7.0) -> bool:
    logging.info(f"[download_video_min_duration] Старт поиска видео по запросу: '{query}'")

    if not PEXELS_API_KEY:
        logging.error("[download_video_min_duration] Ошибка: PEXELS_API_KEY не найден.")
        raise ValueError("PEXELS_API_KEY не найден.")

    url = f"https://api.pexels.com/videos/search?query={query}&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
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
                    logging.info(f"[download_video_min_duration] Скачиваем видео: {video_url}")

                    try:
                        with requests.get(video_url, timeout=20, stream=True) as r:
                            r.raise_for_status()
                            with open(temp_path, "wb") as f_out:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f_out.write(chunk)
                        logging.info(f"[download_video_min_duration] Видео скачано: {temp_path}")
                    except Exception as e:
                        logging.error(f"[download_video_min_duration] Ошибка при скачивании: {e}")
                        continue

                    try:
                        clip = mp.VideoFileClip(temp_path)
                        duration = clip.duration
                        logging.info(f"[download_video_min_duration] Длительность видео: {duration:.2f} сек")
                        if duration >= min_duration:
                            clip.reader.close()
                            if clip.audio and clip.audio.reader:
                                clip.audio.reader.close_proc()
                            clip.close()
                            os.rename(temp_path, filename)
                            logging.info(f"[download_video_min_duration] Видео подходит: {filename}")
                            return True
                        else:
                            clip.reader.close()
                            if clip.audio and clip.audio.reader:
                                clip.audio.reader.close_proc()
                            clip.close()
                            os.remove(temp_path)
                            logging.info(f"[download_video_min_duration] Видео слишком короткое, удалено")
                    except Exception as e:
                        logging.error(f"[download_video_min_duration] Видео повреждено: {e}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        logging.warning(f"[download_video_min_duration] Нет подходящих видео по запросу: '{query}'")
        return False

    except Exception as e:
        logging.error(f"[download_video_min_duration] Ошибка API: {e}")
        return False


def get_video_clips(phrases: list[str]) -> list[str]:
    logging.info("=== Старт обработки фраз ===")
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    selected_phrases = phrases[:4]

    for i, phrase in enumerate(selected_phrases):
        logging.info(f"[get_video_clips] Фраза {i + 1}: {phrase}")
        clean_phrase = phrase.replace('"', '').replace("«", "").replace("»", "").strip()
        search_query = compress_scene(clean_phrase)
        logging.info(f"[get_video_clips] Поисковый запрос: '{search_query}'")

        raw_path = f"assets/clips/raw_{i}.mp4"
        final_path = f"assets/clips/clip_{i}.mp4"

        try:
            success = download_video_min_duration(search_query, raw_path)
            if not success:
                logging.warning("[get_video_clips] Не удалось скачать видео")
                continue

            time.sleep(0.5)  # дожидаемся освобождения файла

            logging.info("[get_video_clips] Загружаем видео...")
            clip = mp.VideoFileClip(raw_path)
            logging.info(f"[get_video_clips] Длительность: {clip.duration:.2f} сек")

            end_time = min(7, clip.duration)
            logging.info(f"[get_video_clips] Нарезка: 0–{end_time:.2f} сек")
            subclip = clip.subclip(0, end_time)

            logging.info("[get_video_clips] Сохраняем итоговый клип...")
            subclip.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            paths.append(final_path)

            clip.close()
            subclip.close()
            time.sleep(0.3)  # на всякий случай, дать ffmpeg закрыть файл

            logging.info(f"[get_video_clips] Клип {i + 1} готов")

        except Exception as e:
            logging.error(f"[get_video_clips] Ошибка при обработке '{phrase}': {e}")

    logging.info("=== Обработка завершена ===")
    return paths
