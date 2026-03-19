"""End-to-end demo: Qwen story outline → scene prompts → Pixverse video clips."""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from pixverse import PixverseClient, PixverseError

load_dotenv()

# ── clients ───────────────────────────────────────────────────────────────────
qwen = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api-inference.modelscope.cn/v1"),
)
MODEL = os.environ.get("OPENAI_MODEL", "Qwen/Qwen3.5-27B")
pixverse = PixverseClient(api_key=os.environ["PIXVERSE_API_KEY"])


def chat(system: str, user: str, json_mode: bool = False) -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = qwen.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        **kwargs,
    )
    return resp.choices[0].message.content


def safe_filename(title: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", title)


# ── step 1: user input ────────────────────────────────────────────────────────
# TEST CASE: hardcoded theme for reproducible testing
theme = "一个关于姐妹情谊与背叛的悬疑短剧：两姐妹共同创业，却因一份遗嘱反目成仇"
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── step 2: generate story outline ───────────────────────────────────────────
print("\n⏳ 生成故事大纲…")
outline = chat(
    system=(
        "你是一位专业的短剧编剧。根据用户给出的主题，创作一个完整的短剧故事大纲，包含：\n"
        "- 剧名\n"
        "- 主要人物（2-3人）及其关系\n"
        "- 故事背景\n"
        "- 完整情节：开端 → 发展 → 高潮 → 结局\n"
        "用中文写作，语言生动，情节有冲突感和戏剧张力。大纲约300字。"
    ),
    user=f"主题：{theme}",
)

print("\n" + "─" * 60)
print(outline)
print("─" * 60)

# ── step 2.5: extract character visual descriptions ──────────────────────────
print("\n⏳ 提取角色外貌描述…")
chars_json = chat(
    system=(
        "你是一位影视造型师。从故事大纲中提取主要人物，为每人生成一段固定的英文外貌描述，用于 AI 视频生成。\n"
        "输出 ONLY 合法 JSON，格式如下（不要 markdown 代码块）：\n"
        '{"characters": [\n'
        '  {"name": "角色中文名", "visual": "concise English appearance description: gender, age, hair, skin, clothing style, one or two distinctive features"}\n'
        "]}\n"
        "要求：\n"
        "- 涵盖所有主要角色（通常2-3人）\n"
        "- visual 必须是英文，约30词，具体且可视化，不含性格描写\n"
        "- 服装描述要固定（同一角色跨场景保持一致）"
    ),
    user=f"故事大纲：\n{outline}",
    json_mode=True,
)
characters = json.loads(chars_json)["characters"]

print("\n👤 角色外貌：")
for c in characters:
    print(f"  {c['name']}：{c['visual']}")

# build character reference block to inject into scene prompts
char_ref = "\n".join(
    f"- {c['name']}: {c['visual']}" for c in characters
)

# ── step 3: split outline into scene video prompts ───────────────────────────
print("\n⏳ 拆分场景并生成视频 prompt…")
scenes_json = chat(
    system=(
        "你是一位视频导演。根据提供的故事大纲，将其拆分为5个关键场景，每个场景生成一段适合 AI 视频生成的英文 prompt。\n"
        "输出 ONLY 合法 JSON，格式如下（不要 markdown 代码块）：\n"
        '{"title": "剧名", "scenes": [\n'
        '  {"title": "场景中文标题", "prompt": "cinematic English video prompt"}\n'
        "]}\n"
        "要求：\n"
        "- 恰好5个场景，按故事顺序排列\n"
        "- 每个 English prompt 必须包含该场景出现的角色的完整外貌描述（直接嵌入 prompt 文本），以保证跨场景人物一致性\n"
        "- 描述该场景的视觉画面：镜头类型、环境、人物动作、光线氛围，约70词\n"
        "- prompt 必须是英文，场景标题是中文\n\n"
        f"固定角色外貌（必须逐字嵌入每个相关场景的 prompt）：\n{char_ref}"
    ),
    user=f"故事大纲：\n{outline}",
    json_mode=True,
)

script = json.loads(scenes_json)

# ── create output directory ───────────────────────────────────────────────────
out_dir = Path("output") / f"{ts}_{safe_filename(script['title'])}"
out_dir.mkdir()
print(f"\n📁 输出目录：{out_dir}/")

# save LLM results
(out_dir / "outline.txt").write_text(outline, encoding="utf-8")
(out_dir / "characters.json").write_text(
    json.dumps(characters, ensure_ascii=False, indent=2), encoding="utf-8"
)
(out_dir / "script.json").write_text(
    json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"\n🎬 《{script['title']}》— 场景列表\n")
for i, scene in enumerate(script["scenes"], 1):
    print(f"  {i}. {scene['title']}")
    print(f"     {scene['prompt']}\n")

# ── step 4: submit to Pixverse ────────────────────────────────────────────────
print("🚀 提交视频生成任务…\n")
jobs = []

for scene in script["scenes"]:
    try:
        vid = pixverse.generate(
            scene["prompt"],
            model="v4.5",
            quality="360p",
            duration=5,
        )
        print(f"  ✓ 「{scene['title']}」video_id={vid}")
        jobs.append((scene["title"], vid))
    except PixverseError as e:
        print(f"  ✗ 「{scene['title']}」提交失败：{e}")

# ── step 5: wait, download ────────────────────────────────────────────────────
if jobs:
    print("\n⏳ 等待生成并下载…\n")
    for title, vid in jobs:
        try:
            url = pixverse.wait(vid)
            print(f"  🎥 {title}\n     {url}")
            idx = next(i for i, (t, _) in enumerate(jobs, 1) if t == title)
            fname = out_dir / f"{idx:02d}_{safe_filename(title)}.mp4"
            with httpx.stream("GET", url, timeout=300) as r:
                r.raise_for_status()
                with open(fname, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=65536):
                        f.write(chunk)
            print(f"     已保存 → {fname}\n")
        except (PixverseError, TimeoutError) as e:
            print(f"  ✗ {title} 失败：{e}\n")
else:
    print("\n没有成功提交的视频任务。")
