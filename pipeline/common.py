import os
import re
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from pixverse import PixverseClient

load_dotenv()

qwen = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api-inference.modelscope.cn/v1"),
)
MODEL = os.environ.get("OPENAI_MODEL", "Qwen/Qwen3.5-27B")
pixverse = PixverseClient(api_key=os.environ["PIXVERSE_API_KEY"])

_log_path: Path | None = None


def set_log_path(path: Path) -> None:
    global _log_path
    _log_path = path


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    if _log_path:
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")


def safe_filename(title: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", title)


def chat(system: str, user: str, json_mode: bool = False, label: str = "llm") -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    log(f"{label} → 请求中…")
    t0 = datetime.now()
    for attempt in range(1, 4):
        try:
            resp = qwen.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                **kwargs,
            )
            break
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                wait = 10 * attempt
                log(f"{label} ← 429 rate limit，{wait}s 后重试 (attempt {attempt})")
                time.sleep(wait)
            else:
                raise
    elapsed = (datetime.now() - t0).seconds
    log(f"{label} ← 完成 ({elapsed}s)")
    return resp.choices[0].message.content
