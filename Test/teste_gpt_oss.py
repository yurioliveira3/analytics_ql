import os
from openai import OpenAI

# Ollama não exige chave real, qualquer valor serve
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"

client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-oss:20b",
    messages=[
        {"role": "system", "content": "Reasoning effort: low"},
        {"role": "user", "content": "Explique ACID em 3 bullets."}
    ]
)

print(resp.choices[0].message.content)
