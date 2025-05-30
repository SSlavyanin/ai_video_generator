from text_generator import generate_script
from voice_generator import generate_voices
from video_selector import get_video_clips
from video_builder import build_video

def run(topic: str):
    phrases = generate_script(topic)
    audio_paths = generate_voices(phrases)
    video_paths = get_video_clips(phrases)
    build_video(video_paths, audio_paths, phrases)

if __name__ == "__main__":
    run("финансовая грамотность")
