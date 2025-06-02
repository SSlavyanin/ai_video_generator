import os
import time
import requests
import logging
import moviepy.editor as mp
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
                        head = requests.head(video_url, timeout=10)
                        content_length = int(head.headers.get("Content-Length", 0))
                        logging.info(f"[download_video_min_duration] Ожидаемый размер: {content_length} байт")

                        with requests.get(video_url, timeout=30, stream=True) as r:
                            r.raise_for_status()
                            with open(temp_path, "wb") as f_out:
                                total = 0
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f_out.write(chunk)
                                        total += len(chunk)

                        if content_length > 0 and abs(total - content_length) > 50000:
                            logging.warning(f"[download_video_min_duration] Размер скачанного файла не совпадает с ожидаемым: {total} ≠ {content_length}")
                            os.remove(temp_path)
                            continue

                        logging.info(f"[download_video_min_duration] Видео сохранено во временный файл: {temp_path}")
                    except Exception as e:
                        logging.error(f"[download_video_min_duration] Ошибка при скачивании: {e}")
                        continue

                    try:
                        time.sleep(0.5)
                        clip = mp.VideoFileClip(temp_path)
                        logging.info(f"[download_video_min_duration] Проверяем длительность видео: {clip.duration:.2f} сек")
                        if clip.duration >= min_duration:
                            clip.close()
                            os.rename(temp_path, filename)
                            logging.info(f"[download_video_min_duration] Видео подходит и сохранено как: {filename}")
                            return True
                        else:
                            clip.close()
                            os.remove(temp_path)
                            logging.info(f"[download_video_min_duration] Слишком короткое видео (<{min_duration} сек), удаляем")
                    except Exception as e:
                        logging.error(f"[download_video_min_duration] Видео повреждено или не читается: {e}")
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        logging.warning(f"[download_video_min_duration] Не найдено годных видео по '{query}'")
        return False

    except Exception as e:
        logging.error(f"[download_video_min_duration] Ошибка при обращении к Pexels: {e}")
        return False



def get_video_clips(phrases: list[str]) -> list[str]:
    logging.info("Старт обработки фраз")
    os.makedirs("assets/clips", exist_ok=True)
    paths = []

    selected_phrases = phrases[:4]

    for i, phrase in enumerate(selected_phrases):
        logging.info(f"[get_video_clips] Обработка фразы {i + 1}: {phrase}")
        clean_phrase = phrase.replace('"', '').replace("«", "").replace("»", "").strip()
        search_query = compress_scene(clean_phrase)
        logging.info(f"[get_video_clips]   Сжатый поисковый запрос: '{search_query}'")

        raw_path = f"assets/clips/raw_{i}.mp4"
        final_path = f"assets/clips/clip_{i}.mp4"

        try:
            logging.info("[get_video_clips]   Скачиваем видео...")
            success = download_video_min_duration(search_query, raw_path)
            if not success:
                logging.warning("[get_video_clips]   Видео не найдено или не скачано")
                continue

            logging.info("[get_video_clips]   Пауза перед чтением видеофайла...")
            time.sleep(0.5)

            logging.info("[get_video_clips]   Загружаем скачанное видео для обработки...")
            clip = mp.VideoFileClip(raw_path)
            logging.info(f"[get_video_clips]   Длительность видео: {clip.duration:.2f} сек")

            end_time = min(7, clip.duration)
            logging.info(f"[get_video_clips]   Нарезаем видео до {end_time} сек")
            subclip = clip.subclip(0, end_time)

            logging.info("[get_video_clips]   Записываем итоговый клип...")
            subclip.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            paths.append(final_path)

            clip.close()
            subclip.close()

            logging.info(f"[get_video_clips]   Клип {i + 1} обработан успешно")

        except Exception as e:
            logging.error(f"[get_video_clips]   Ошибка при обработке фразы '{phrase}': {e}")

        # ❗ Не удаляем raw-файлы сразу — MoviePy/FFmpeg может всё ещё держать их в кэше
        # if os.path.exists(raw_path):
        #     os.remove(raw_path)

    logging.info("Обработка фраз завершена")
    return paths
