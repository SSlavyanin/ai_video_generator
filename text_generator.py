import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_script(topic: str) -> list[str]:
    prompt = f"Напиши короткий сценарий из 4 фраз по теме: {topic}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()
    return [line.strip("-• ") for line in text.split("\n") if line.strip()]
