import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def generate_script(topic: str) -> list[str]:
    prompt = f"Напиши короткий сценарий из 4 фраз по теме: {topic}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    return [line.strip("-• ") for line in text.split("\n") if line.strip()]
