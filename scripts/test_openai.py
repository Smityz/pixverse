"""Quick test: call ModelScope-hosted Qwen model via OpenAI-compatible API."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)
model = os.environ["OPENAI_MODEL"]

print(f"Model: {model}")
print("Sending test message...")

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Say 'hello' in 5 languages, one per line."}],
    max_tokens=200,
)

print(response.choices[0].message.content)
