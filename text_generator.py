import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def generate_script(topic: str) -> list[str]:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("Не найден OPENROUTER_API_KEY в .env")

    prompt = f"Напиши короткий сценарий из 4 фраз по теме: {topic}"

    payload = {
        "model": "meta-llama/llama-4-maverick",  # можно заменить на другой, например openchat/openchat-7b
        "messages": [
            {"role": "system", "content": "Ты сценарист. Пиши краткие, выразительные фразы."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return [line.strip("-• ") for line in text.split("\n") if line.strip()]
    except requests.exceptions.RequestException as e:
        print(f"[OpenRouter API Error] {e}")
        return ["Ошибка генерации текста", "Попробуйте позже", "Проверьте ключ и лимиты", "Или смените модель"]
    except (KeyError, IndexError) as e:
        print(f"[OpenRouter JSON Parse Error] {e}")
        return ["Неверный ответ от модели", "Формат данных не совпал", "Проверьте логи", "Или смените модель"]


def compress_scene(text: str) -> str:
    """Сжать фразу до видеозапроса по смыслу (через GPT)"""
    prompt = f"Из этой фразы сделай короткий видеозапрос по смыслу, например 'женщина грустит у окна', 'мужчина в офисе':\n{text}\n\nВидеозапрос:"

    payload = {
        "model": "meta-llama/llama-4-maverick",
        "messages": [
            {"role": "system", "content": "Ты описываешь сцену для поиска видео. Ответ — короткий, визуальный, без кавычек."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"[Compress API Error] {e}")
        return text  # fallback: вернём оригинал
    except (KeyError, IndexError) as e:
        print(f"[Compress JSON Parse Error] {e}")
        return text  # fallback

