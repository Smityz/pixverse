"""Test vision input with streaming and reasoning content."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ["OPENAI_BASE_URL"],
)

response = client.chat.completions.create(
    model=os.environ["OPENAI_MODEL"],  # Qwen3-VL-30B-A3B-Instruct
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这幅图"},
            {"type": "image_url", "image_url": {
                "url": "https://modelscope.oss-cn-beijing.aliyuncs.com/demo/images/audrey_hepburn.jpg"
            }},
        ],
    }],
    stream=True,
)

done_reasoning = False
for chunk in response:
    if chunk.choices:
        reasoning_chunk = chunk.choices[0].delta.reasoning_content
        answer_chunk = chunk.choices[0].delta.content
        if reasoning_chunk:
            print(reasoning_chunk, end="", flush=True)
        elif answer_chunk:
            if not done_reasoning:
                print("\n\n === Final Answer ===\n")
                done_reasoning = True
            print(answer_chunk, end="", flush=True)
print()
