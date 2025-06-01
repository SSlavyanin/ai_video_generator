import os
import gc
import logging
import moviepy.editor as mp

def build_video(video_paths: list[str], audio_paths: list[str], output_path="static/videos/final_output.mp4"):
    os.makedirs("static/videos", exist_ok=True)
    final_clips = []

    for i in range(len(video_paths)):
        try:
            print(f"[~] Обрабатываю клип {i + 1} из {len(video_paths)}")

            # Загружаем видео, берем первые 3 секунды, уменьшаем высоту до 480
            video = mp.VideoFileClip(video_paths[i]).subclip(0, 3).resize(height=480)

            # Загружаем аудио и ставим его в видео
            audio = mp.AudioFileClip(audio_paths[i])
            video = video.set_audio(audio)

            final_clips.append(video)

            # Чистим память после каждого клипа
            del audio
            gc.collect()

        except Exception as e:
            print(f"[!] Ошибка при обработке клипа {i}: {e}")

    try:
        print("[~] Склеиваю все видео в один файл...")
        final_video = mp.concatenate_videoclips(final_clips)
        final_video.write_videofile(output_path, fps=24, threads=2, preset='ultrafast')
        print(f"[✓] Готово! Видео сохранено по пути: {output_path}")
    except Exception as e:
        print(f"[!] Ошибка при финальной сборке видео: {e}")
