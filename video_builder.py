import os
import moviepy.editor as mp  # Импортируем как alias для надёжности

def build_video(video_paths: list[str], audio_paths: list[str], phrases: list[str], output_path="output/final.mp4"):
    os.makedirs("output", exist_ok=True)
    final_clips = []

    for i in range(len(video_paths)):
        # Загружаем видео и аудио, ограничиваем видео до 5 сек, ставим высоту 720
        video = mp.VideoFileClip(video_paths[i]).subclip(0, 5).resize(height=720)
        audio = mp.AudioFileClip(audio_paths[i])
        video = video.set_audio(audio)

        # Добавляем текстовую подпись
        txt = mp.TextClip(phrases[i], fontsize=40, color='white', bg_color='black', size=video.size)
        txt = txt.set_duration(video.duration).set_position('bottom')

        # Склеиваем видео и текст
        composed = mp.CompositeVideoClip([video, txt])
        final_clips.append(composed)

    # Объединяем все клипы и сохраняем финальный файл
    final_video = mp.concatenate_videoclips(final_clips)
    final_video.write_videofile(output_path, fps=24)
