import os
from gtts import gTTS

def generate_voices(phrases: list[str]) -> list[str]:
    os.makedirs("assets", exist_ok=True)  # Убедимся, что папка существует

    paths = []
    for i, phrase in enumerate(phrases):
        tts = gTTS(text=phrase, lang="ru")
        path = f"assets/voice_{i}.mp3"
        tts.save(path)
        print(f"Сохранён голос: {path}")
        paths.append(path)
    return paths
