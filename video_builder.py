from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, AudioFileClip
import os

def build_video(video_paths: list[str], audio_paths: list[str], phrases: list[str], output_path="output/final.mp4"):
    os.makedirs("output", exist_ok=True)
    final_clips = []

    for i in range(len(video_paths)):
        video = VideoFileClip(video_paths[i]).subclip(0, 5).resize(height=720)
        audio = AudioFileClip(audio_paths[i])
        video = video.set_audio(audio)

        txt = TextClip(phrases[i], fontsize=40, color='white', bg_color='black', size=video.size)
        txt = txt.set_duration(video.duration).set_position('bottom')
        composed = CompositeVideoClip([video, txt])
        final_clips.append(composed)

    final_video = concatenate_videoclips(final_clips)
    final_video.write_videofile(output_path, fps=24)
