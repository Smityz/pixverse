"""Pipeline stage 2: Extract character appearance descriptions from outline."""

import json
from pathlib import Path

from .common import chat, log


def run(outline: str, out_dir: Path) -> list[dict]:
    cached = out_dir / "characters.json"
    if cached.exists():
        log("characters: 已有 characters.json，跳过生成")
        return json.loads(cached.read_text(encoding="utf-8"))

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
        label="step2 角色",
    )
    characters = json.loads(chars_json)["characters"]
    print("\n👤 角色外貌：")
    for c in characters:
        print(f"  {c['name']}：{c['visual']}")
    cached.write_text(
        json.dumps(characters, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log("step2: 角色提取完毕")
    return characters
