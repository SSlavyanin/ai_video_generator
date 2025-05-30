from gtts import gTTS
import os

def generate_voices(phrases: list[str]) -> list[str]:
    paths = []
    for i, phrase in enumerate(phrases):
        tts = gTTS(phrase, lang='ru')
        path = f"assets/voice_{i}.mp3"
        tts.save(path)
        paths.append(path)
    return paths
